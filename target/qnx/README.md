# QNX 8.0 target demo

This directory holds the DeadlineLens periodic-task demo for QNX 8.0. It writes a `deadlinelens-trace/v1` JSON file that the Linux host analyzer can open.

It has been compiled with the real QNX compiler (`qcc -Vgcc_ntox86_64`) and run on QNX 8.0 under QEMU. The official contest capture is `traces/qnx-deadlinelens-trace.json`. Do not treat a host rebuild of this binary as a replacement for that capture. Build and run details are in `notes/build-run-note.md`.

These sources are not compiled on Linux. On a development host, use `target/posix_fallback` instead. `cc -std=c11 -c` on these files is expected to fail.

## Build (on a machine with QNX SDP 8.0)

```bash
source qnxsdp-env.sh   # from the SDP 8.0 install
qcc -Vgcc_ntox86_64 -Wall -Wextra -O2 \
    -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"' \
    -o periodic_task periodic_task.c deadline_trace.c
```

Or `make` after `qcc` is on `PATH`.

## Run (on the QNX 8.0 guest)

```bash
./periodic_task --out qnx-deadlinelens-trace.json --target qemu \
    --toolchain 'qcc -Vgcc_ntox86_64'
```

The demo starts two `SCHED_FIFO` threads (sensor priority 21, control priority 15). They wake with `clock_nanosleep` / `TIMER_ABSTIME` on a 10 millisecond period. Control job 3 is intentionally long enough to miss its deadline.

Copy the JSON to the host and run:

```bash
python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --require-qnx-evidence
```
