# DeadlineLens demo video script (≤3 minutes, pre-recorded)

Official rules (re-read 2026-11-13, Asia/Shanghai): https://qnx.devpost.com/rules and https://qnx.devpost.com/.

- Pre-recorded video is allowed. An on-camera defense is not required.
- Length must be **under three minutes**. Judges are not required to watch beyond three minutes.
- The video must show the project functioning on the device it was built for (here: the host tool analyzing a trace captured on **QNX 8.0 under QEMU**).
- Upload to **YouTube**, make it public, and paste the link on the Devpost form. This script does **not** upload anything.
- Do not use third-party trademarks or copyrighted music without permission. Prefer silence, or a short voice-over you record yourself.
- Language: English (or provide an English translation).

A local silent walkthrough generated from the real HTML report and on-screen commands is at:

`notes/deadlinelens-demo-walkthrough.mp4`

- Format: 1280×720 H.264 (yuv420p) with a silent AAC track, no music
- Duration: **2 minutes 21 seconds** (under the official three-minute cap)
- It is a starting cut you can voice over, or replace with a live screen recording
- It has **not** been published, and must not be uploaded until you decide to put it on YouTube

A 3:2 gallery thumbnail is at `notes/devpost-thumbnail.png` (1200×800, under 5 MB).

Total narration target: **2 minutes 21 seconds** (hard cap 2:50).

---

## Shot list and narration

### Shot 1 — Title (0:00–0:12)

**On screen:** Title card “DeadlineLens” and the line “See missed deadlines in real QNX 8.0 traces.”

**Say:** “This is DeadlineLens, a host tool for QNX 8.0. It shows missed deadlines, period jitter, and priority inversions from an application-level JSON trace.”

### Shot 2 — The problem (0:12–0:28)

**On screen:** Short problem text: late jobs, jitter, inversions; “timing is part of correctness.”

**Say:** “On a real-time system, the failure may not be a crash. A control job can finish a few milliseconds late, or a low-priority thread can run while a higher-priority thread is already ready. Those are the bugs I want to see clearly.”

### Shot 3 — How the pieces fit (0:28–0:48)

**On screen:** Two boxes: “QNX 8.0 / QEMU target demo” and “Linux host analyzer,” with arrows to `traces/qnx-deadlinelens-trace.json` and `traces/qnx-report.html`.

**Say:** “There are two parts. A demo on QNX 8.0 under QEMU writes the trace. A Python host tool analyzes it and builds an HTML timeline. Samples and a POSIX fallback exist only for development, and the tool will reject them as contest evidence.”

### Shot 4 — Build and run commands (0:48–1:08)

**On screen:** The three short commands (compiler, guest run, host analyzer). Show QNX version 8.0.0, target QEMU, toolchain `qcc -Vgcc_ntox86_64`.

**Say:** “The demo is compiled with the real QNX compiler, qcc, target gcc_ntox86_64, from SDP 8.0. It runs on a QNX 8.0 QEMU guest. On the host I pass the trace to DeadlineLens with the flag that requires QNX evidence.”

**Commands to show (no private host paths):**

```bash
qcc -Vgcc_ntox86_64 -Wall -Wextra -O2 \
    -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"' \
    -o periodic_task periodic_task.c deadline_trace.c

./periodic_task --out qnx-deadlinelens-trace.json --target qemu \
    --toolchain 'qcc -Vgcc_ntox86_64'

python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --require-qnx-evidence
```

### Shot 5 — Real QNX evidence in the report (1:08–1:32)

**On screen:** `traces/qnx-report.html` — green “QNX contest evidence” banner and the provenance table: source `qnx-periodic-task (captured on QNX)`, qnx_version `QNX 8.0.0`, target `qemu`, toolchain `qcc -Vgcc_ntox86_64`, uname_sysname `QNX`.

**Say:** “This is the report from the real capture. The banner says QNX contest evidence is present. The provenance table shows the source was captured on QNX, version 8.0.0, the target is QEMU, and the toolchain is qcc dash V gcc_ntox86_64.”

### Shot 6 — Timeline, one missed deadline (1:32–1:50)

**On screen:** KPI row (10 jobs, 1 missed deadline, 4 inversions) and the timeline. Highlight the red control job 3 bar.

**Say:** “The run has ten jobs and one missed deadline. On the timeline, sensor jobs stay blue. Control job 3 is red: it ran long enough to pass its ten-millisecond deadline, about 3.08 milliseconds late.”

### Shot 7 — The same miss in the table (1:50–2:04)

**On screen:** Missed-deadlines table: control, job 3, response 13.080 ms, relative deadline 10.000 ms, tardiness 3.080 ms, logged miss yes, inferred miss yes. Then the response-time and jitter tables.

**Say:** “The table lists that same miss, both logged and inferred. Control’s maximum response is 13.08 milliseconds against a 10 millisecond deadline.”

### Shot 8 — Close (2:04–2:21)

**On screen:** Closing card with the files judges should open: `traces/qnx-deadlinelens-trace.json`, `traces/qnx-report.html`, `notes/build-run-note.md`. Optional: “Developer Tooling & Host Tools.”

**Say:** “The JSON, the HTML report, and the build-run note are in the repository. That is DeadlineLens: a host tool, and real evidence from QNX 8.0 on QEMU.”

---

## Recording notes (if you recut it yourself)

- Record the HTML report from a browser at 1280×720 or 1920×1080. Pointer motion is enough; you do not need to appear on camera.
- Scroll from the evidence banner to the timeline, then to the missed-deadline table. Pause on control job 3.
- Keep the YouTube title and description in English. Do not add a music bed unless you own it or it is clearly licensed for this use.
- After upload, set the video to Public, copy the URL into the Devpost form, and watch the first 15 seconds to confirm the embed works.
- Do not show license keys, passwords, or private machine paths.

## Storyboard timing summary

| Time | Shot | Visual |
| --- | --- | --- |
| 0:00–0:12 | 1 | Title card |
| 0:12–0:28 | 2 | Problem |
| 0:28–0:48 | 3 | Host tool + QNX target |
| 0:48–1:08 | 4 | Commands, version / target / toolchain |
| 1:08–1:32 | 5 | Report: evidence banner + provenance |
| 1:32–1:50 | 6 | Timeline + missed deadline (control job 3) |
| 1:50–2:04 | 7 | Missed-deadline and response tables |
| 2:04–2:21 | 8 | Closing file list |
