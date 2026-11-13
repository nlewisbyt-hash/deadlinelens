# DeadlineLens build / run note

Official rules require stating the QNX version, the target (hardware or QEMU), and the toolchain, plus evidence that QNX 8.0 was actually used: https://qnx.devpost.com/rules

**Status on 2026-11-13, Asia/Shanghai:** this note records a real capture. QNX SDP 8.0 was installed with the official Software Center. The demo was compiled with the real `qcc` and run on a QNX 8.0 guest built with the official `mkqnximage` tool and booted under QEMU. The resulting trace is in `traces/qnx-deadlinelens-trace.json`. Formal Devpost Submit has not been done. This note does not include license keys, passwords, or private host paths.

| Item | Value |
| --- | --- |
| QNX version | QNX 8.0.0 (`uname` on the guest: `QNX deadlinelens 8.0.0 2026/10/30-09:10:05EDT x86pc x86_64`) |
| Target | QEMU, x86_64 (official `mkqnximage --type=qemu --arch=x86_64`) |
| Toolchain | `qcc -Vgcc_ntox86_64` (qcc 12.2.0, default target `gcc_ntox86_64`) |
| Host OS | Debian GNU/Linux 13 (trixie), x86_64 |
| License | Non-commercial QNX SDP 8.0 developer license. Do not paste the license key here. |
| How to install SDP | Official Software Center / Quickstart: https://www.qnx.com/developers/docs/8.0/com.qnx.doc.qnxsdp.quickstart/topic/install_host.html — then `source qnxsdp-env.sh` from that install |
| How the QEMU image was built | Official `mkqnximage --type=qemu --arch=x86_64 --graphics=no --ram=1G --cpu=2 --ssh-ident <host-public-key> --users=root --sshd-pregen=yes --hostname=deadlinelens --noprompt --secpol=no --sys-size=40 --data-size=40 --build` |
| How to boot QEMU | Host hypervisor was `/usr/bin/qemu-system-x86_64` 10.0.13. KVM was not used (`-cpu max` TCG). Networking was user-mode slirp with SSH forwarded to `127.0.0.1:2222`, not a bridge. See the exact command below. |
| How to build the demo | After `qnxsdp-env.sh` is sourced: see the compile line below (`target/qnx/Makefile` when present). |
| How to get JSON | On the QNX guest: `./periodic_task --out qnx-deadlinelens-trace.json --target qemu --toolchain 'qcc -Vgcc_ntox86_64'` |
| Trace path | `traces/qnx-deadlinelens-trace.json` |
| How to generate the report | `python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json -o traces/qnx-report.html --json traces/qnx-analysis.json --require-qnx-evidence` |

## Compile (2026-11-13, 14:00 Asia/Shanghai)

```bash
qcc -Vgcc_ntox86_64 -Wall -Wextra -O2 \
    -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"' \
    -o periodic_task periodic_task.c deadline_trace.c
```

The compiler exited 0 (one `snprintf` format-truncation warning). The binary is an ELF64 x86-64 QNX executable.

## QEMU command used for the official capture

The official QSTI desktop image was installed, but it was **not** the image used for the official trace (graphics/Screen is not useful headless; this note does not treat that boot as contest evidence). The official capture used a smaller image from `mkqnximage` as above.

```bash
/usr/bin/qemu-system-x86_64 -name deadlinelens-qnx800 -smp 2 -cpu max -m 1G \
    -kernel output/ifs.bin \
    -drive file=output/disk-qemu.vmdk,if=ide,id=drv0,index=0 \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22 \
    -device virtio-net-pci,netdev=net0,mac=52:54:00:00:08:00 \
    -object rng-random,filename=/dev/urandom,id=rng0 -device virtio-rng-pci,rng=rng0 \
    -display none \
    -chardev socket,id=s0,host=127.0.0.1,port=4445,server=on,wait=off \
    -serial chardev:s0
```

SSH key login as root on `127.0.0.1:2222` succeeded. The demo ran with exit 0. The JSON was copied to `traces/qnx-deadlinelens-trace.json`.

Guest `uname -a`:

```
QNX deadlinelens 8.0.0 2026/10/30-09:10:05EDT x86pc x86_64
```

## Trace metadata (official evidence)

- `format`: `deadlinelens-trace/v1`
- `source`: `qnx-periodic-task (captured on QNX)`
- `qnx_version`: `QNX 8.0.0`
- `target`: `qemu`
- `toolchain`: `qcc -Vgcc_ntox86_64`
- `uname_sysname`: `QNX`
- `uname_release`: `8.0.0`
- `uname_version`: `2026/10/30-09:10:05EDT`
- `uname_machine`: `x86pc`
- `sched_note`: `SCHED_FIFO requested for sensor and control threads.`

Host analysis (`traces/qnx-analysis.json`): 10 jobs, 1 missed deadline (control job 3, tardiness 3,079,687 ns ≈ 3.080 ms), 4 priority inversions, 0 period jitter, `evidence=qnx_contest_evidence`.

## Host checks after the capture

```bash
python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --json traces/qnx-analysis.json \
    --require-qnx-evidence
# exit 0 on the real QNX trace

python3 -m host.deadlinelens.cli traces/sample_missed_deadline.json --require-qnx-evidence
# exit 2 (and the same for the other traces/sample_*.json files)

python3 tests/test_deadlinelens.py -v
```

Samples and any POSIX fallback are development aids only. They are not contest evidence.
