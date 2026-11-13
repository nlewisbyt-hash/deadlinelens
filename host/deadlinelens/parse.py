from __future__ import annotations

import json
from pathlib import Path

from .schema import END, FORMAT, MISS, PREEMPT, READY, RELEASE, START

KNOWN_EVENT_TYPES = {RELEASE, START, END, MISS, PREEMPT, READY}


def load_trace(path: Path | str) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return validate(data, source=str(path))


def validate(data: dict, source: str = "") -> dict:
    if not isinstance(data, dict):
        raise ValueError("trace must be a JSON object")
    fmt = data.get("format")
    if fmt != FORMAT:
        raise ValueError(f"unsupported format {fmt!r}, expected {FORMAT}")
    threads = data.get("threads")
    events = data.get("events")
    if not isinstance(threads, list) or not threads:
        raise ValueError("threads must be a non-empty list")
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    ids = set()
    for th in threads:
        for key in ("id", "name", "priority", "period_ns", "deadline_ns"):
            if key not in th:
                raise ValueError(f"thread missing {key}")
        if th["id"] in ids:
            raise ValueError(f"duplicate thread id {th['id']}")
        for num_key in ("id", "priority", "period_ns", "deadline_ns"):
            if not isinstance(th[num_key], int):
                raise ValueError(f"thread {num_key} must be an int")
        if th["period_ns"] <= 0 or th["deadline_ns"] <= 0:
            raise ValueError(f"thread {th['id']} period_ns and deadline_ns must be positive")
        ids.add(th["id"])
    for ev in events:
        for key in ("t_ns", "type", "thread_id", "job"):
            if key not in ev:
                raise ValueError(f"event missing {key}: {ev}")
        if ev["thread_id"] not in ids:
            raise ValueError(f"event references unknown thread {ev['thread_id']}")
        if not isinstance(ev["t_ns"], int) or not isinstance(ev["job"], int):
            raise ValueError(f"event t_ns and job must be ints: {ev}")
        if ev["type"] not in KNOWN_EVENT_TYPES:
            raise ValueError(f"unknown event type {ev['type']!r}")
    data = dict(data)
    data["_source"] = source
    data["events"] = sorted(events, key=lambda e: (int(e["t_ns"]), int(e["thread_id"])))
    return data
