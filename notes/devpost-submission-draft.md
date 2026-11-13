# DeadlineLens — Devpost submission draft (English, paste-ready)

Official sources re-read on 2026-11-13, Asia/Shanghai:

- Rules: https://qnx.devpost.com/rules
- What to Submit / overview: https://qnx.devpost.com/

This draft does not include license keys, passwords, or private host paths. Build and run details that are safe to publish are in `notes/build-run-note.md`. QNX SDP 8.0 was installed with the official Software Center; the official capture image was built with official `mkqnximage`.

Formal Devpost Submit was completed on 2026-11-13 (Asia/Shanghai). Live project: https://devpost.com/software/deadlinelens-71i4mn . This file keeps the submitted copy and the post-submit check.

---

## Step 2 — Project profile

### Project name

```
DeadlineLens
```

### Tagline (113 characters, keep under ~140)

```
A host tool that finds missed deadlines, jitter, and priority inversions in real QNX 8.0 traces.
```

### Thumbnail / gallery image

The 3:2 image at `notes/devpost-thumbnail.png` was uploaded as the Devpost project thumbnail.

### Built with (stay at or under 25 tags)

```
QNX SDP 8.0
qcc
QEMU
mkqnximage
Python 3
C11
HTML
JSON
SCHED_FIFO
clock_nanosleep
```

### Try it out (optional)

Leave blank, or point to the public repository README once that URL exists. The host analyzer runs on Linux with Python 3 and does not need QNX SDP on the machine that opens the report.

---

## Step 3 — Project story (markdown)

Paste the block below into the Devpost description / “Project story” field.

```markdown
## What it does

DeadlineLens is a Linux host tool for QNX 8.0 software. It reads an application-level JSON trace (`deadlinelens-trace/v1`), finds missed deadlines, period jitter, and priority inversions, and renders an HTML timeline.

The trace is produced by a small QNX target demo: two `SCHED_FIFO` threads (sensor at priority 21, control at priority 15) wake with `clock_nanosleep` / `TIMER_ABSTIME` on a 10 millisecond period. Control job 3 is written to run long enough to miss its deadline, so the report has a known, visible miss.

A real capture from QNX 8.0 under QEMU is already in this repository:

- `traces/qnx-deadlinelens-trace.json` — `source=qnx-periodic-task (captured on QNX)`, `qnx_version=QNX 8.0.0`, `target=qemu`, `toolchain=qcc -Vgcc_ntox86_64`
- `traces/qnx-report.html` and `traces/qnx-analysis.json` — host report, `evidence=qnx_contest_evidence`
- `notes/build-run-note.md` — QNX version, QEMU target, toolchain, and the commands used

In that run there are 10 jobs, 1 missed deadline (control job 3, tardiness ≈ 3.080 ms), 4 priority inversions, and 0 period jitter.

Hand-written samples in `traces/sample_*.json` and any POSIX fallback exist only so the host tool can be developed and tested without a board. They are not contest evidence. The flag `--require-qnx-evidence` accepts the QNX capture (exit 0) and rejects those samples (exit 2).

## How it uses QNX 8.0

This entry is in **Developer Tooling & Host Tools**. The analyzer itself runs on Linux. The contest evidence is a real QNX 8.0 capture, not a sample file and not a README mention of QNX.

- **QNX version:** QNX 8.0.0. Guest `uname`: `QNX deadlinelens 8.0.0 2026/10/30-09:10:05EDT x86pc x86_64`.
- **Target:** QEMU, x86_64.
- **Toolchain:** `qcc -Vgcc_ntox86_64` (qcc 12.2.0).

QNX SDP 8.0 was installed with the official Software Center. The official capture image was built with the official `mkqnximage` tool (`--type=qemu --arch=x86_64`). The guest was booted under the host `qemu-system-x86_64` (10.0.13) with TCG (`-cpu max`) and user-mode networking. Exact commands, including the compile line and the QEMU command, are in `notes/build-run-note.md`.

The demo is compiled with the real QNX compiler:

```bash
qcc -Vgcc_ntox86_64 -Wall -Wextra -O2 \
    -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"' \
    -o periodic_task periodic_task.c deadline_trace.c
```

On the QNX 8.0 QEMU guest:

```bash
./periodic_task --out qnx-deadlinelens-trace.json --target qemu \
    --toolchain 'qcc -Vgcc_ntox86_64'
```

On the Linux host (no SDP required to open the report):

```bash
python3 tests/test_deadlinelens.py -v
python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --json traces/qnx-analysis.json \
    --require-qnx-evidence
```

Please open the JSON, the HTML report (green “QNX contest evidence” banner and the provenance table), and the build-run note. In the timeline, control job 3 is the red bar that finishes after its 10 millisecond deadline.

## Challenges and accomplishments

Getting a *real* QNX 8.0 evidence trail — not a sample JSON — was the main challenge. SDP 8.0 had to be installed through the official Software Center, the demo had to be compiled with real `qcc`, and the guest had to boot under QEMU from an official `mkqnximage` image. The host QEMU setup could not use KVM or a libvirt bridge, so the captured run uses TCG and user-mode slirp; that is documented rather than hidden.

The useful result is a host report that can tell contest evidence from development samples, and one missed deadline that is easy to point to: control job 3, about 3.08 milliseconds late, both logged and inferred.

## What I learned

Application-level events are enough to make a missed deadline and a priority inversion visible, if the trace carries provenance (QNX version, target, toolchain, `uname`). A host tool is only as trustworthy as its ability to refuse a sample file when a reviewer asks for QNX evidence.
```

---

## Step 4 — Official form fields

Fill these on the form. Official rules plus the Devpost “What to Submit” list require them.

### Category (choose one)

```
Developer Tooling & Host Tools
```

### Public repository URL

```
https://github.com/nlewisbyt-hash/deadlinelens
```

The repository must be public, must include the MIT `LICENSE` file at the root so Devpost can detect it in the About section, and must show that the project genuinely builds for or runs on QNX 8.0, not only that QNX is named in the README. Submitter / copyright holder: Baoquan Yang, 2026.

### Demo video (YouTube, public, under three minutes)

```
https://youtu.be/9y6AANeVNXg
```

A timed English script is in `notes/demo-video-script.md`. The public video is the local silent walkthrough, published at the URL above. Official rules require a pre-recorded video under three minutes, showing the project working, uploaded to YouTube and made public, with a link on the form. No third-party trademarks or copyrighted music. Judges are not required to watch beyond three minutes. A pre-recorded demo is allowed; an on-camera defense is not required.

### Build and run instructions

Point reviewers to `notes/build-run-note.md`. The required facts are:

- QNX version: **QNX 8.0.0**
- Target: **QEMU (x86_64)**
- Toolchain: **`qcc -Vgcc_ntox86_64`**

### Codelab / tutorial bonus URL

Leave blank unless a real tutorial is published during the submission period. `codelab/outline.md` is only an outline and is not a published codelab.

### Submitter type

Individual (or the form equivalent). Copyright holder: Baoquan Yang, 2026.

---

## Post-submit check (2026-11-13, Asia/Shanghai)

Live software page: https://devpost.com/software/deadlinelens-71i4mn

Devpost showed “Project submitted! Continue to edit your project until the hackathon deadline: December 15, 2026 at 02:00pm EST.” and “SUBMITTED TO / QNX Global Hackathon”. The submission manage page showed “SUBMITTED” and “5/5 steps done”.

| Requirement | Status |
| --- | --- |
| English text description of what it does | Yes — on the live Devpost page |
| How the project uses / supports QNX, with file callouts | Yes — live page + README “For judges” |
| Build/run note with version, target, toolchain | Yes — `notes/build-run-note.md` (QNX 8.0.0, QEMU x86_64, `qcc -Vgcc_ntox86_64`) |
| Real QNX 8.0 evidence (trace + HTML report) | Yes — `traces/qnx-*.json` / `traces/qnx-report.html` |
| Open-source LICENSE at repo root (OSI-recognized MIT) | Yes — GitHub detects MIT on https://github.com/nlewisbyt-hash/deadlinelens |
| Public GitHub / GitLab / Bitbucket repository | Yes — https://github.com/nlewisbyt-hash/deadlinelens |
| ≤3 minute demo on public YouTube, link on the form | Yes — https://youtu.be/9y6AANeVNXg (Nikki Lewis, public, about 2:21) |
| Category Developer Tooling & Host Tools | Yes — saved on the submitted form |
| Formal Devpost Submit | Yes — https://devpost.com/software/deadlinelens-71i4mn |
