from __future__ import annotations

from .provenance import classify_evidence
from .schema import END, MISS, PREEMPT, READY, RELEASE, START


def analyze(trace: dict) -> dict:
    threads = {t["id"]: t for t in trace["threads"]}
    jobs: dict[tuple[int, int], dict] = {}
    for ev in trace["events"]:
        key = (ev["thread_id"], ev["job"])
        rec = jobs.setdefault(
            key,
            {
                "thread_id": ev["thread_id"],
                "thread": threads[ev["thread_id"]]["name"],
                "priority": threads[ev["thread_id"]]["priority"],
                "period_ns": threads[ev["thread_id"]]["period_ns"],
                "deadline_ns": threads[ev["thread_id"]]["deadline_ns"],
                "job": ev["job"],
                "release_ns": None,
                "start_ns": None,
                "end_ns": None,
                "logged_miss": False,
            },
        )
        if ev["type"] == RELEASE:
            rec["release_ns"] = ev["t_ns"]
        elif ev["type"] == START and rec["start_ns"] is None:
            rec["start_ns"] = ev["t_ns"]
        elif ev["type"] == END:
            rec["end_ns"] = ev["t_ns"]
        elif ev["type"] == MISS:
            rec["logged_miss"] = True

    misses = []
    inferred = []
    logged_but_on_time = []
    incomplete = []
    for rec in jobs.values():
        if rec["release_ns"] is not None and rec["start_ns"] is not None:
            rec["start_latency_ns"] = rec["start_ns"] - rec["release_ns"]
        if rec["start_ns"] is not None and rec["end_ns"] is not None:
            rec["exec_ns"] = rec["end_ns"] - rec["start_ns"]
        if rec["release_ns"] is None or rec["end_ns"] is None:
            if rec["release_ns"] is not None and rec["end_ns"] is None:
                incomplete.append(rec)
            continue
        deadline_abs = rec["release_ns"] + rec["deadline_ns"]
        rec["deadline_abs_ns"] = deadline_abs
        rec["response_ns"] = rec["end_ns"] - rec["release_ns"]
        rec["slack_ns"] = deadline_abs - rec["end_ns"]
        rec["tardiness_ns"] = max(0, rec["end_ns"] - deadline_abs)
        rec["exact_boundary"] = rec["end_ns"] == deadline_abs
        is_miss = rec["end_ns"] >= deadline_abs
        rec["inferred_miss"] = is_miss
        if is_miss or rec["logged_miss"]:
            misses.append(rec)
        if is_miss and not rec["logged_miss"]:
            inferred.append(rec)
        if rec["logged_miss"] and not is_miss:
            logged_but_on_time.append(rec)

    inversions = _priority_inversions(trace, threads)
    jitter = _period_jitter(jobs, threads)
    response = _response_stats(jobs, threads, trace)
    return {
        "job_count": len(jobs),
        "miss_count": len(misses),
        "misses": sorted(misses, key=lambda r: r.get("deadline_abs_ns") or 0),
        "inferred_miss_without_event": inferred,
        "logged_but_on_time": logged_but_on_time,
        "incomplete_jobs": incomplete,
        "priority_inversions": inversions,
        "jitter": jitter,
        "response_stats": response,
        "span_ns": _span_ns(trace),
        "evidence": classify_evidence(trace),
    }


def _span_ns(trace: dict) -> int:
    events = trace.get("events") or []
    if not events:
        return 0
    times = [int(e["t_ns"]) for e in events]
    return max(times) - min(times)


def _priority_inversions(trace: dict, threads: dict) -> list[dict]:
    """A lower-priority thread is running while a higher-priority one is ready.

    Application-level approximation. PREEMPT clears the running thread but
    leaves it ready; END drops it from both. This is not a kernel scheduler
    trace and is not by itself contest evidence of QNX scheduling.
    """
    ready: set[int] = set()
    running: int | None = None
    hits = []
    for ev in trace["events"]:
        typ = ev["type"]
        tid = ev["thread_id"]
        if typ == RELEASE or typ == READY:
            ready.add(tid)
        elif typ == START:
            running = tid
            ready.add(tid)
        elif typ == PREEMPT:
            if running == tid:
                running = None
            ready.add(tid)
        elif typ == END:
            ready.discard(tid)
            if running == tid:
                running = None
        if running is None or not ready:
            continue
        run_prio = threads[running]["priority"]
        for other in ready:
            if other == running:
                continue
            if threads[other]["priority"] > run_prio:
                hits.append(
                    {
                        "t_ns": ev["t_ns"],
                        "running": threads[running]["name"],
                        "waiting": threads[other]["name"],
                        "running_priority": run_prio,
                        "waiting_priority": threads[other]["priority"],
                    }
                )
    seen = set()
    uniq = []
    for h in hits:
        key = (h["t_ns"], h["running"], h["waiting"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    return uniq


def _period_jitter(jobs: dict, threads: dict) -> list[dict]:
    """Compare consecutive release intervals to the configured period."""
    by_thread: dict[int, list[int]] = {}
    for rec in jobs.values():
        if rec["release_ns"] is None:
            continue
        by_thread.setdefault(rec["thread_id"], []).append(int(rec["release_ns"]))
    out = []
    for tid, releases in by_thread.items():
        releases = sorted(releases)
        period = int(threads[tid]["period_ns"])
        intervals = [b - a for a, b in zip(releases, releases[1:])]
        errors = [abs(iv - period) for iv in intervals]
        out.append(
            {
                "thread_id": tid,
                "thread": threads[tid]["name"],
                "period_ns": period,
                "release_count": len(releases),
                "intervals_ns": intervals,
                "max_abs_error_ns": max(errors) if errors else 0,
                "mean_abs_error_ns": (sum(errors) / len(errors)) if errors else 0,
            }
        )
    return out


def _response_stats(jobs: dict, threads: dict, trace: dict) -> list[dict]:
    """Per-thread response, slack, start-latency, and crude utilization."""
    span = _span_ns(trace) or 1
    by_thread: dict[int, list[dict]] = {}
    for rec in jobs.values():
        by_thread.setdefault(rec["thread_id"], []).append(rec)
    out = []
    for tid, recs in by_thread.items():
        responses = [r["response_ns"] for r in recs if r.get("response_ns") is not None]
        slacks = [r["slack_ns"] for r in recs if r.get("slack_ns") is not None]
        latencies = [r["start_latency_ns"] for r in recs if r.get("start_latency_ns") is not None]
        execs = [r["exec_ns"] for r in recs if r.get("exec_ns") is not None]
        misses = sum(1 for r in recs if r.get("inferred_miss") or r.get("logged_miss"))
        out.append(
            {
                "thread_id": tid,
                "thread": threads[tid]["name"],
                "priority": threads[tid]["priority"],
                "job_count": len(recs),
                "miss_count": misses,
                "min_response_ns": min(responses) if responses else None,
                "max_response_ns": max(responses) if responses else None,
                "mean_response_ns": (sum(responses) / len(responses)) if responses else None,
                "min_slack_ns": min(slacks) if slacks else None,
                "max_start_latency_ns": max(latencies) if latencies else None,
                "exec_sum_ns": sum(execs) if execs else 0,
                "utilization": (sum(execs) / span) if execs else 0.0,
            }
        )
    out.sort(key=lambda r: (-r["priority"], r["thread"]))
    return out
