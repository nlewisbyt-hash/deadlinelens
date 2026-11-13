from __future__ import annotations

from html import escape
from pathlib import Path

from .analyze import analyze

_TEMPLATE = Path(__file__).with_name("report_template.html")


def _ns_label(ns: int | float | None) -> str:
    if ns is None:
        return "—"
    ns = int(round(ns))
    if abs(ns) >= 1_000_000:
        return f"{ns / 1_000_000:.3f} ms"
    if abs(ns) >= 1_000:
        return f"{ns / 1_000:.1f} µs"
    return f"{ns} ns"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p>None.</p>"
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _timeline_svg(trace: dict, analysis: dict | None = None) -> str:
    threads = trace["threads"]
    events = trace["events"]
    t_min = min((e["t_ns"] for e in events), default=0)
    t_max = max((e["t_ns"] for e in events), default=1)
    span = max(t_max - t_min, 1)
    width = 900
    row_h = 52
    height = 90 + row_h * len(threads)
    left = 110

    def x(t: int) -> int:
        return left + int((t - t_min) / span * width)

    jobs: dict[tuple[int, int], dict] = {}
    for ev in events:
        rec = jobs.setdefault((ev["thread_id"], ev["job"]), {"thread_id": ev["thread_id"], "job": ev["job"]})
        rec[ev["type"]] = ev["t_ns"]

    extras: dict[tuple[int, int], dict] = {}
    if analysis:
        for rec in analysis.get("misses") or []:
            extras[(rec["thread_id"], rec["job"])] = rec
        for rec in analysis.get("incomplete_jobs") or []:
            extras[(rec["thread_id"], rec["job"])] = rec

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width + left + 20} {height}" '
        f'width="{width + left + 20}" height="{height}" font-family="sans-serif">'
    ]
    axis_y = 24
    parts.append(f'<line x1="{left}" y1="{axis_y}" x2="{left + width}" y2="{axis_y}" stroke="#999"/>')
    for frac in range(0, 6):
        t = t_min + span * frac / 5
        xx = x(int(t))
        parts.append(f'<line x1="{xx}" y1="{axis_y - 4}" x2="{xx}" y2="{axis_y + 4}" stroke="#999"/>')
        parts.append(
            f'<text x="{xx}" y="{axis_y - 8}" font-size="10" text-anchor="middle" fill="#555">'
            f"{escape(_ns_label(int(t - t_min)))}</text>"
        )

    for i, th in enumerate(threads):
        y = 40 + i * row_h
        parts.append(
            f'<text x="8" y="{y + 16}" font-size="12">{escape(th["name"])} p{th["priority"]}</text>'
        )
        # faint row guide
        parts.append(
            f'<line x1="{left}" y1="{y + 20}" x2="{left + width}" y2="{y + 20}" '
            f'stroke="#eee"/>'
        )
        for (tid, job), rec in jobs.items():
            if tid != th["id"]:
                continue
            extra = extras.get((tid, job), {})
            # Waiting (release -> start)
            if "release" in rec and "start" in rec:
                wx1, wx2 = x(rec["release"]), x(rec["start"])
                if wx2 > wx1:
                    parts.append(
                        f'<rect x="{wx1}" y="{y + 4}" width="{wx2 - wx1}" height="12" fill="#f7dc6f" opacity="0.85">'
                        f"<title>{escape(th['name'])} job {job} wait {_ns_label(rec['start'] - rec['release'])}</title></rect>"
                    )
            # Execution bar
            if "start" in rec and "end" in rec:
                x1, x2 = x(rec["start"]), x(rec["end"])
                miss = rec.get("miss") is not None or (
                    "release" in rec and rec["end"] >= rec["release"] + th["deadline_ns"]
                )
                color = "#c0392b" if miss else "#2980b9"
                slack = extra.get("slack_ns")
                tardy = extra.get("tardiness_ns")
                bits = [
                    f"{th['name']} job {job}",
                    f"start={_ns_label(rec['start'] - t_min)}",
                    f"end={_ns_label(rec['end'] - t_min)}",
                ]
                if "release" in rec:
                    bits.append(f"deadline={_ns_label(rec['release'] + th['deadline_ns'] - t_min)}")
                if miss and tardy is not None:
                    bits.append(f"tardiness={_ns_label(tardy)}")
                elif slack is not None:
                    bits.append(f"slack={_ns_label(slack)}")
                title = escape(" · ".join(bits))
                bar_w = max(x2 - x1, 2)
                parts.append(
                    f'<rect x="{x1}" y="{y}" width="{bar_w}" height="18" fill="{color}">'
                    f"<title>{title}</title></rect>"
                )
                if bar_w >= 14:
                    parts.append(
                        f'<text x="{x1 + 2}" y="{y + 13}" font-size="9" fill="#fff">{job}</text>'
                    )
                if miss:
                    parts.append(
                        f'<text x="{x2 + 3}" y="{y + 13}" font-size="9" fill="#c0392b">miss</text>'
                    )
            elif "start" in rec and "end" not in rec:
                x1 = x(rec["start"])
                parts.append(
                    f'<rect x="{x1}" y="{y}" width="8" height="18" fill="none" stroke="#c0392b" '
                    f'stroke-dasharray="2,2"><title>{escape(th["name"])} job {job} incomplete</title></rect>'
                )
        # Deadline ticks and release marks
        for (tid, job), rec in jobs.items():
            if tid != th["id"] or "release" not in rec:
                continue
            rx = x(rec["release"])
            parts.append(
                f'<polygon points="{rx},{y + 22} {rx - 3},{y + 28} {rx + 3},{y + 28}" fill="#7f8c8d">'
                f"<title>release job {job}</title></polygon>"
            )
            dx = x(rec["release"] + th["deadline_ns"])
            parts.append(
                f'<line x1="{dx}" y1="{y - 4}" x2="{dx}" y2="{y + 22}" '
                f'stroke="#7f8c8d" stroke-dasharray="2,2"/>'
            )
    parts.append("</svg>")
    return "".join(parts)



def _footer_note(evidence: dict) -> str:
    kind = evidence.get("kind") or "unverified"
    if kind == "qnx_contest_evidence":
        return (
            "This report was generated from a trace captured on QNX 8.0. "
            "QEMU is accepted by the official rules (https://qnx.devpost.com/rules). "
            "Keep the JSON, the QEMU or hardware run record, and the build/run note "
            "together as official evidence."
        )
    return (
        "Official contest evidence must later include a trace captured on QNX 8.0. "
        "QEMU is accepted by the official rules (https://qnx.devpost.com/rules). "
        "A POSIX fallback emitter exists only to develop this host report and is "
        "not contest evidence. This report does not assume an SDP is installed."
    )


def _evidence_banner(evidence: dict) -> str:
    kind = evidence.get("kind") or "unverified"
    css = {
        "qnx_contest_evidence": "qnx-evidence",
        "not_contest_evidence": "not-evidence",
    }.get(kind, "unverified")
    titles = {
        "qnx_contest_evidence": "QNX contest evidence metadata present",
        "not_contest_evidence": "Not contest evidence",
        "unverified_qnx_claim": "Incomplete QNX provenance",
        "unverified": "Unverified origin",
    }
    title = titles.get(kind, "Unverified origin")
    return (
        f'<div class="banner {css}" data-evidence-kind="{escape(kind)}">'
        f"<b>{escape(title)}</b>"
        f"{escape(evidence.get('summary') or '')}</div>"
    )


def _provenance_table(evidence: dict) -> str:
    rows = [
        ["source", evidence.get("source") or ""],
        ["qnx_version", evidence.get("qnx_version") or ""],
        ["target", evidence.get("target") or ""],
        ["toolchain", evidence.get("toolchain") or ""],
        ["uname_sysname", evidence.get("uname_sysname") or ""],
        ["sched_note", evidence.get("sched_note") or ""],
    ]
    if not any(value for _label, value in rows):
        return ""
    return '<div class="prov"><h2>Provenance</h2>' + _table(
        ["Field", "Value"],
        [[escape(label), escape(value) if value else "—"] for label, value in rows],
    ) + "</div>"


def render_html(trace: dict, analysis: dict | None = None) -> str:
    analysis = analysis or analyze(trace)
    miss_rows = [
        [
            escape(m["thread"]),
            str(m["job"]),
            escape(_ns_label(m.get("response_ns"))),
            escape(_ns_label(m.get("deadline_ns"))),
            escape(_ns_label(m.get("tardiness_ns"))),
            escape(_ns_label(m.get("slack_ns"))),
            "yes" if m.get("logged_miss") else "no",
            "yes" if m.get("inferred_miss") else "no",
            "yes" if m.get("exact_boundary") else "no",
        ]
        for m in analysis["misses"]
    ]
    jitter_rows = [
        [
            escape(j["thread"]),
            escape(_ns_label(j["period_ns"])),
            str(j["release_count"]),
            escape(_ns_label(j["max_abs_error_ns"])),
            escape(_ns_label(j.get("mean_abs_error_ns"))),
        ]
        for j in analysis.get("jitter") or []
    ]
    inv_rows = [
        [
            escape(_ns_label(inv["t_ns"])),
            escape(inv["running"]),
            str(inv["running_priority"]),
            escape(inv["waiting"]),
            str(inv["waiting_priority"]),
        ]
        for inv in analysis["priority_inversions"]
    ]
    resp_rows = [
        [
            escape(r["thread"]),
            str(r["priority"]),
            str(r["job_count"]),
            str(r["miss_count"]),
            escape(_ns_label(r.get("min_response_ns"))),
            escape(_ns_label(r.get("mean_response_ns"))),
            escape(_ns_label(r.get("max_response_ns"))),
            escape(_ns_label(r.get("min_slack_ns"))),
            escape(_ns_label(r.get("max_start_latency_ns"))),
            f"{r['utilization'] * 100:.1f}%",
        ]
        for r in analysis.get("response_stats") or []
    ]
    max_jitter = max((j["max_abs_error_ns"] for j in analysis.get("jitter") or []), default=0)
    evidence = analysis.get("evidence") or {}
    tmpl = _TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{SOURCE}}": escape(str(trace.get("_source") or trace.get("source") or "")),
        "{{EVIDENCE_BANNER}}": _evidence_banner(evidence),
        "{{PROVENANCE_TABLE}}": _provenance_table(evidence),
        "{{JOB_COUNT}}": str(analysis["job_count"]),
        "{{MISS_COUNT}}": str(analysis["miss_count"]),
        "{{MISS_CLASS}}": "bad" if analysis["miss_count"] else "",
        "{{INV_COUNT}}": str(len(analysis["priority_inversions"])),
        "{{MAX_JITTER}}": escape(_ns_label(max_jitter)),
        "{{SVG}}": _timeline_svg(trace, analysis),
        "{{MISS_TABLE}}": _table(
            [
                "Thread",
                "Job",
                "Response",
                "Relative deadline",
                "Tardiness",
                "Slack",
                "Logged miss",
                "Inferred miss",
                "Exact boundary",
            ],
            miss_rows,
        ),
        "{{JITTER_TABLE}}": _table(
            ["Thread", "Period", "Releases", "Max |error|", "Mean |error|"],
            jitter_rows,
        ),
        "{{RESP_TABLE}}": _table(
            [
                "Thread",
                "Prio",
                "Jobs",
                "Misses",
                "Min resp",
                "Mean resp",
                "Max resp",
                "Min slack",
                "Max start latency",
                "Utilization",
            ],
            resp_rows,
        ),
        "{{INV_TABLE}}": _table(
            ["Time", "Running", "Prio", "Waiting", "Prio"],
            inv_rows,
        ),
        "{{FOOTER_NOTE}}": _footer_note(evidence),
    }
    html = tmpl
    for key, value in repl.items():
        html = html.replace(key, value)
    return html


def write_html(trace: dict, dest: Path, analysis: dict | None = None) -> Path:
    dest = Path(dest)
    dest.write_text(render_html(trace, analysis), encoding="utf-8")
    return dest
