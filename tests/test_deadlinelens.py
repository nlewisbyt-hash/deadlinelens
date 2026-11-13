#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from host.deadlinelens.analyze import analyze  # noqa: E402
from host.deadlinelens.parse import load_trace, validate  # noqa: E402
from host.deadlinelens.provenance import classify_evidence  # noqa: E402
from host.deadlinelens.render import write_html  # noqa: E402


class SampleTraceTests(unittest.TestCase):
    def test_sample_has_one_control_miss(self):
        trace = load_trace(ROOT / "traces" / "sample_missed_deadline.json")
        result = analyze(trace)
        self.assertEqual(result["job_count"], 10)
        self.assertEqual(result["miss_count"], 1)
        miss = result["misses"][0]
        self.assertEqual(miss["thread"], "control")
        self.assertEqual(miss["job"], 3)
        self.assertTrue(miss["inferred_miss"])

    def test_render_mentions_miss(self):
        trace = load_trace(ROOT / "traces" / "sample_missed_deadline.json")
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "report.html"
            write_html(trace, dest)
            html = dest.read_text(encoding="utf-8")
        self.assertIn("control", html)
        self.assertIn("Missed deadlines", html)
        self.assertIn("<svg", html)
        self.assertIn("Period jitter", html)
        self.assertIn("Priority inversions", html)
        self.assertIn("does not assume an SDP is installed", html)
        self.assertIn("Not contest evidence", html)
        self.assertIn('data-evidence-kind="not_contest_evidence"', html)

    def test_cli_writes_report(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "out.html"
            js = Path(td) / "out.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "host.deadlinelens.cli",
                    str(ROOT / "traces" / "sample_missed_deadline.json"),
                    "-o",
                    str(dest),
                    "--json",
                    str(js),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(dest.is_file())
            data = json.loads(js.read_text())
            self.assertEqual(data["miss_count"], 1)



    def test_sample_jitter_is_zero_on_regular_releases(self):
        result = analyze(load_trace(ROOT / "traces" / "sample_missed_deadline.json"))
        self.assertTrue(result["jitter"])
        self.assertTrue(all(j["max_abs_error_ns"] == 0 for j in result["jitter"]))
        self.assertEqual(result["misses"][0]["inferred_miss"], True)

    def test_sample_tardiness_and_response_stats(self):
        result = analyze(load_trace(ROOT / "traces" / "sample_missed_deadline.json"))
        miss = result["misses"][0]
        self.assertEqual(miss["tardiness_ns"], 4_100_000)
        self.assertEqual(miss["slack_ns"], -4_100_000)
        self.assertFalse(miss["exact_boundary"])
        names = {r["thread"] for r in result["response_stats"]}
        self.assertEqual(names, {"sensor", "control"})
        control = next(r for r in result["response_stats"] if r["thread"] == "control")
        self.assertEqual(control["miss_count"], 1)
        self.assertGreater(control["max_start_latency_ns"], 0)



class PosixFallbackTests(unittest.TestCase):
    def test_posix_demo_emits_compatible_trace(self):
        src = ROOT / "target" / "posix_fallback" / "periodic_demo.c"
        with tempfile.TemporaryDirectory() as td:
            binary = Path(td) / "periodic_demo"
            trace_path = Path(td) / "demo.json"
            compile_proc = subprocess.run(
                ["cc", "-std=gnu11", "-Wall", "-o", str(binary), str(src)],
                capture_output=True,
                text=True,
            )
            if compile_proc.returncode != 0:
                self.skipTest("cc not available: " + compile_proc.stderr)
            run = subprocess.run([str(binary), str(trace_path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(trace_path.read_text(encoding="utf-8"))
            self.assertIn("NOT contest evidence", data["source"])
            self.assertIn("not captured on QNX", data["source"])
            result = analyze(load_trace(trace_path))
            self.assertEqual(result["miss_count"], 1)
            self.assertEqual(result["misses"][0]["thread"], "control")
            self.assertEqual(result["misses"][0]["job"], 3)
            self.assertEqual(result["evidence"]["kind"], "not_contest_evidence")
            self.assertFalse(result["evidence"]["is_contest_evidence"])


class ExtraTraceTests(unittest.TestCase):
    def test_exact_boundary_counts_as_miss(self):
        result = analyze(load_trace(ROOT / "traces" / "sample_exact_deadline.json"))
        self.assertEqual(result["job_count"], 3)
        self.assertEqual(result["miss_count"], 1)
        miss = result["misses"][0]
        self.assertEqual(miss["thread"], "worker")
        self.assertEqual(miss["job"], 2)
        self.assertTrue(miss["exact_boundary"])
        self.assertEqual(miss["tardiness_ns"], 0)
        self.assertTrue(miss["logged_miss"])
        self.assertTrue(miss["inferred_miss"])

    def test_jitter_sample_reports_max_error(self):
        result = analyze(load_trace(ROOT / "traces" / "sample_jitter.json"))
        self.assertEqual(len(result["jitter"]), 1)
        self.assertEqual(result["jitter"][0]["max_abs_error_ns"], 1_500_000)
        self.assertEqual(result["miss_count"], 0)

    def test_inversion_sample_flags_low_running_while_high_ready(self):
        result = analyze(load_trace(ROOT / "traces" / "sample_priority_inversion.json"))
        self.assertEqual(result["miss_count"], 0)
        self.assertTrue(result["priority_inversions"])
        hit = result["priority_inversions"][0]
        self.assertEqual(hit["running"], "low")
        self.assertEqual(hit["waiting"], "high")
        self.assertEqual(hit["t_ns"], 1_000_000)

    def test_render_includes_new_sections(self):
        trace = load_trace(ROOT / "traces" / "sample_missed_deadline.json")
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "report.html"
            write_html(trace, dest)
            html = dest.read_text(encoding="utf-8")
        self.assertIn("Tardiness", html)
        self.assertIn("Response times", html)
        self.assertIn("Release-to-start wait", html)
        self.assertIn("Exact boundary", html)
        self.assertIn("Utilization", html)


class ParseValidationTests(unittest.TestCase):
    def test_rejects_wrong_format(self):
        with self.assertRaisesRegex(ValueError, "unsupported format"):
            validate({"format": "nope", "threads": [{"id": 1, "name": "t", "priority": 1, "period_ns": 1, "deadline_ns": 1}], "events": []})

    def test_rejects_unknown_event_type(self):
        data = {
            "format": "deadlinelens-trace/v1",
            "threads": [{"id": 1, "name": "t", "priority": 1, "period_ns": 1000, "deadline_ns": 1000}],
            "events": [{"t_ns": 0, "type": "explode", "thread_id": 1, "job": 1}],
        }
        with self.assertRaisesRegex(ValueError, "unknown event type"):
            validate(data)

    def test_rejects_non_positive_period(self):
        data = {
            "format": "deadlinelens-trace/v1",
            "threads": [{"id": 1, "name": "t", "priority": 1, "period_ns": 0, "deadline_ns": 1000}],
            "events": [],
        }
        with self.assertRaisesRegex(ValueError, "must be positive"):
            validate(data)



class EvidenceClassificationTests(unittest.TestCase):
    def test_handwritten_samples_are_not_contest_evidence(self):
        for name in (
            "sample_missed_deadline.json",
            "sample_exact_deadline.json",
            "sample_jitter.json",
            "sample_priority_inversion.json",
        ):
            ev = classify_evidence(load_trace(ROOT / "traces" / name))
            self.assertEqual(ev["kind"], "not_contest_evidence", name)
            self.assertFalse(ev["is_contest_evidence"], name)

    def test_complete_qnx_metadata_is_contest_evidence(self):
        data = {
            "format": "deadlinelens-trace/v1",
            "source": "qnx-periodic-task (captured on QNX)",
            "qnx_version": "QNX 8.0.0",
            "target": "qemu",
            "toolchain": "qcc -Vgcc_ntox86_64",
            "qnx": {"uname_sysname": "QNX"},
            "threads": [
                {"id": 1, "name": "sensor", "priority": 21, "period_ns": 10_000_000, "deadline_ns": 10_000_000}
            ],
            "events": [
                {"t_ns": 0, "type": "release", "thread_id": 1, "job": 1},
                {"t_ns": 100, "type": "start", "thread_id": 1, "job": 1},
                {"t_ns": 200, "type": "end", "thread_id": 1, "job": 1},
            ],
        }
        ev = analyze(validate(data))["evidence"]
        self.assertEqual(ev["kind"], "qnx_contest_evidence")
        self.assertTrue(ev["is_contest_evidence"])
        self.assertEqual(ev["target"], "qemu")
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "report.html"
            write_html(validate(data), dest)
            html = dest.read_text(encoding="utf-8")
        self.assertIn("QNX contest evidence metadata present", html)
        self.assertIn("qcc -Vgcc_ntox86_64", html)

    def test_qnx_claim_without_toolchain_is_incomplete(self):
        ev = classify_evidence(
            {
                "source": "qnx-periodic-task (captured on QNX)",
                "qnx_version": "QNX 8.0.0",
                "target": "qemu",
            }
        )
        self.assertEqual(ev["kind"], "unverified_qnx_claim")
        self.assertFalse(ev["is_contest_evidence"])

    def test_cli_require_qnx_evidence_rejects_sample(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "out.html"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "host.deadlinelens.cli",
                    str(ROOT / "traces" / "sample_missed_deadline.json"),
                    "-o",
                    str(dest),
                    "--require-qnx-evidence",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("not classified as QNX contest evidence", proc.stderr)

    def test_qnx_sources_do_not_compile_on_this_linux_host(self):
        srcs = [
            ROOT / "target" / "qnx" / "periodic_task.c",
            ROOT / "target" / "qnx" / "deadline_trace.c",
        ]
        with tempfile.TemporaryDirectory() as td:
            for src in srcs:
                out = Path(td) / (src.stem + ".o")
                proc = subprocess.run(
                    ["cc", "-std=c11", "-c", "-o", str(out), str(src)],
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(proc.returncode, 0, src)
                self.assertIn("posix_fallback", proc.stderr)
                self.assertFalse(out.exists())



if __name__ == "__main__":
    unittest.main()
