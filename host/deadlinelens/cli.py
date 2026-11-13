#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from host.deadlinelens.analyze import analyze
    from host.deadlinelens.parse import load_trace
    from host.deadlinelens.render import write_html
else:
    from .analyze import analyze
    from .parse import load_trace
    from .render import write_html


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="DeadlineLens host analyzer")
    p.add_argument("trace", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("deadlinelens-report.html"))
    p.add_argument("--json", type=Path, help="optional analysis JSON")
    p.add_argument(
        "--require-qnx-evidence",
        action="store_true",
        help="exit 2 unless the trace is labeled as QNX contest evidence",
    )
    args = p.parse_args(argv)
    trace = load_trace(args.trace)
    analysis = analyze(trace)
    evidence = analysis.get("evidence") or {}
    write_html(trace, args.output, analysis)
    if args.json:
        slim = {
            "job_count": analysis["job_count"],
            "miss_count": analysis["miss_count"],
            "evidence": evidence,
            "span_ns": analysis.get("span_ns"),
            "misses": [
                {
                    "thread": m["thread"],
                    "job": m["job"],
                    "response_ns": m.get("response_ns"),
                    "tardiness_ns": m.get("tardiness_ns"),
                    "slack_ns": m.get("slack_ns"),
                    "exact_boundary": m.get("exact_boundary"),
                    "inferred_miss": m.get("inferred_miss"),
                    "logged_miss": m.get("logged_miss"),
                }
                for m in analysis["misses"]
            ],
            "jitter": [
                {
                    "thread": j["thread"],
                    "period_ns": j["period_ns"],
                    "max_abs_error_ns": j["max_abs_error_ns"],
                    "mean_abs_error_ns": j.get("mean_abs_error_ns"),
                }
                for j in analysis.get("jitter") or []
            ],
            "response_stats": analysis.get("response_stats") or [],
            "priority_inversions": analysis["priority_inversions"],
        }
        args.json.write_text(json.dumps(slim, indent=2), encoding="utf-8")
    print(f"jobs={analysis['job_count']} misses={analysis['miss_count']} inversions={len(analysis['priority_inversions'])}")
    for m in analysis["misses"]:
        tardy = m.get("tardiness_ns")
        boundary = " exact-boundary" if m.get("exact_boundary") else ""
        print(f"  miss {m['thread']} job {m['job']} tardiness={tardy} ns{boundary}")
    print(
        f"evidence={evidence.get('kind')} "
        f"contest_evidence={evidence.get('is_contest_evidence')}"
    )
    if evidence.get("qnx_version") or evidence.get("target") or evidence.get("toolchain"):
        print(
            "  qnx_version={qnx_version!s} target={target!s} toolchain={toolchain!s}".format(
                **{k: evidence.get(k) or "" for k in ("qnx_version", "target", "toolchain")}
            )
        )
    print(f"wrote {args.output}")
    if args.require_qnx_evidence and not evidence.get("is_contest_evidence"):
        print(
            "error: --require-qnx-evidence was set, but this trace is not "
            f"classified as QNX contest evidence (kind={evidence.get('kind')})",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
