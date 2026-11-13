"""Classify whether a trace can be treated as QNX contest evidence.

Official rules require actually using QNX 8.0 and stating the version,
target (hardware or QEMU), and toolchain: https://qnx.devpost.com/rules

Hand-written samples and the POSIX fallback emitter are development aids
only. This module does not itself prove a QNX run; it only reads labels
already present in the JSON.
"""

from __future__ import annotations

NOT_EVIDENCE_MARKERS = (
    "not contest evidence",
    "not captured on qnx",
    "posix-fallback",
    "hand-written",
)


def _qnx_block(trace: dict) -> dict:
    raw = trace.get("qnx")
    return raw if isinstance(raw, dict) else {}


def classify_evidence(trace: dict) -> dict:
    qnx = _qnx_block(trace)
    source = str(trace.get("source") or qnx.get("source") or "")
    qnx_version = str(trace.get("qnx_version") or qnx.get("version") or "")
    target = str(trace.get("target") or qnx.get("target") or "")
    toolchain = str(trace.get("toolchain") or qnx.get("toolchain") or "")
    uname_sysname = str(qnx.get("uname_sysname") or trace.get("uname_sysname") or "")
    sched_note = str(qnx.get("sched_note") or trace.get("sched_note") or "")

    source_l = source.lower()
    labeled_not_evidence = any(marker in source_l for marker in NOT_EVIDENCE_MARKERS)
    looks_like_qnx = (
        uname_sysname == "QNX"
        or qnx_version.startswith("8.")
        or "captured on qnx" in source_l
        or source_l.startswith("qnx-")
    )

    if labeled_not_evidence:
        kind = "not_contest_evidence"
        summary = (
            "This trace is labeled as not contest evidence "
            "(hand-written sample or POSIX fallback). "
            "It cannot satisfy the official QNX 8.0 evidence requirement."
        )
    elif looks_like_qnx and qnx_version and target and toolchain:
        kind = "qnx_contest_evidence"
        summary = (
            "Trace metadata identifies a QNX capture with version, target, "
            "and toolchain. Keep the JSON, the QEMU or hardware run record, "
            "and the build/run note together as official evidence."
        )
    elif looks_like_qnx:
        kind = "unverified_qnx_claim"
        summary = (
            "The source looks QNX-related, but qnx_version, target, or "
            "toolchain is missing. Do not treat this as complete contest "
            "evidence until those fields are filled from the actual SDP run."
        )
    else:
        kind = "unverified"
        summary = (
            "Trace does not identify a QNX 8.0 capture. Do not treat it as "
            "contest evidence."
        )

    return {
        "kind": kind,
        "is_contest_evidence": kind == "qnx_contest_evidence",
        "source": source,
        "qnx_version": qnx_version,
        "target": target,
        "toolchain": toolchain,
        "uname_sysname": uname_sysname,
        "sched_note": sched_note,
        "summary": summary,
    }
