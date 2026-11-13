# DeadlineLens — QNX Global Hackathon 作品

截止：2026-12-16 03:00 亚洲/上海（官方 12-15 14:00 ET）。  
官网：https://qnx.devpost.com/  
规则：https://qnx.devpost.com/rules  
获取 QNX 8.0（Everywhere，非商用）：https://www.qnx.com/getqnx  
中国站：https://china.qnx.com/products/everywhere/

赛道：**Developer Tooling & Host Tools**。Devpost 账号已报名（Joined）。**尚未正式提交（Submit）。**

非商用 QNX SDP 8.0 已通过官方 Software Center 安装。许可密钥只放在本机私有笔记里，不要写进公开 README 或提交材料。

**本机已安装 QNX SDP 8.0 与真实 `qcc`，并已在 QNX 8.0 / QEMU 上采集参赛踪迹。** SDP 通过官方 Software Center / `mkqnximage` 安装；`qcc -V` 默认目标为 `12.2.0,gcc_ntox86_64`。真实踪迹在 `traces/qnx-deadlinelens-trace.json`，分析报告在 `traces/qnx-report.html`，完整命令见 `notes/build-run-note.md`。POSIX 回退和 `traces/sample_*.json` 只用于开发主机工具，不能当作参赛证据。

本项目以 MIT License 发布，见仓库根目录 `LICENSE`。Copyright (c) 2026 Baoquan Yang。

## For judges

DeadlineLens is a Linux host tool that finds missed deadlines, period jitter, and priority inversions in an application-level JSON trace, and renders an HTML timeline. The contest capture was compiled with the real QNX compiler (`qcc -Vgcc_ntox86_64`) and run on QNX 8.0.0 under QEMU.

**Start here:**

- `traces/qnx-deadlinelens-trace.json` — capture from QNX 8.0 (`source=qnx-periodic-task (captured on QNX)`, `qnx_version=QNX 8.0.0`, `target=qemu`, `toolchain=qcc -Vgcc_ntox86_64`)
- `traces/qnx-report.html` and `traces/qnx-analysis.json` — host report (`evidence=qnx_contest_evidence`); one missed deadline is control job 3 (tardiness ≈ 3.08 ms)
- `notes/build-run-note.md` — build and run record (QNX version, QEMU target, toolchain, commands). QNX SDP 8.0 was installed with the official Software Center and the official `mkqnximage` tool.

The host analyzer requires no QNX SDP on the machine that opens the report:

```bash
python3 tests/test_deadlinelens.py -v
python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --json traces/qnx-analysis.json \
    --require-qnx-evidence
```

`--require-qnx-evidence` accepts the QNX capture (exit 0) and rejects the development samples in `traces/sample_*.json` (exit 2). Those samples and the POSIX fallback are not contest evidence.

This project is released under the MIT License. See `LICENSE` at the repository root. Copyright (c) 2026 Baoquan Yang.

## 作品方向

主机工具读取应用层 JSON 踪迹（格式见 `host/deadlinelens/schema.py`），标出错过的 deadline、优先级倒挂与周期抖动，并生成可打开的 HTML 时间线。报告会根据 `source` / `qnx_version` / `target` / `toolchain` 标明这是不是 QNX 参赛证据。目标侧（QNX 8.0，QEMU）跑一组周期任务，其中包含一次可复现的错过截止期，并写出同一格式的踪迹。另有 Codelab 大纲，供后续冲击 Best Codelab/Tutorial（$3,500，规则奖项表）。

## 本机现在就能做的

分析这份已在 QNX 8.0 / QEMU 上采集的踪迹（`--require-qnx-evidence` 应成功，退出码 0）：

```bash
python3 tests/test_deadlinelens.py -v
python3 -m host.deadlinelens.cli traces/qnx-deadlinelens-trace.json \
    -o traces/qnx-report.html --json traces/qnx-analysis.json \
    --require-qnx-evidence
```

开发用样例（不是参赛证据）仍可用：

```bash
python3 -m host.deadlinelens.cli traces/sample_missed_deadline.json -o traces/sample_report.html
```

预生成的样例报告在 `traces/sample_report.html`（含「不是参赛证据」横幅）。对开发用踪迹加上 `--require-qnx-evidence` 会以退出码 2 拒绝，避免误当成官方证据。

其他手写示例（同样不是 QNX 采集，不能当参赛证据）：

- `traces/sample_exact_deadline.json`：结束时刻刚好等于 deadline，按约定计为 miss
- `traces/sample_jitter.json`：release 周期抖动
- `traces/sample_priority_inversion.json`：低优先级在跑、高优先级已 ready

在已安装的 SDP 上重新编译并运行目标侧演示（完整命令见 `notes/build-run-note.md`）：

```bash
# After SDP 8.0 is installed, source the official qnxsdp-env.sh from that install
make -C target/qnx
```

## 目录

- `LICENSE`：MIT License，Copyright (c) 2026 Baoquan Yang
- `host/deadlinelens/`：解析、分析、HTML 渲染、证据分类、命令行
- `traces/qnx-deadlinelens-trace.json`：2026-11-13 在 QNX 8.0 / QEMU 上采集的真实踪迹
- `traces/qnx-report.html`、`traces/qnx-analysis.json`：对应的主机报告（`evidence=qnx_contest_evidence`）
- `traces/sample_*.json`：开发用示例，不是参赛证据
- `target/qnx/`：面向 QNX 8.0 / QEMU 的演示源与 Makefile（用 `qcc -Vgcc_ntox86_64` 编译）
- `target/posix_fallback/`：仅供开发主机工具
- `codelab/outline.md`：教程提纲
- `notes/build-run-note.md`：本次真实运行的 build/run 说明（QNX 版本、QEMU、工具链、命令）
- `notes/devpost-submission-draft.md`：可粘贴到 Devpost 的英文提交草稿
- `notes/demo-video-script.md`：不超过 3 分钟的英文预录演示脚本与分镜
- `notes/deadlinelens-demo-walkthrough.mp4`：本地无声走查视频（未发布）
- `notes/devpost-thumbnail.png`：3:2 缩略图（本地生成，未上传）
- `notes/sdp-install-2026-11-12-software-center.md`、`notes/sdp-install-blocker-2026-11-12.md`：安装过程备忘（历史）
- `tests/test_deadlinelens.py`

## 规则要点（与到场无关）

规则要求全程提交线上材料：公开仓库、≤3 分钟演示视频（评委不必看超过 3 分钟）、build/run 说明（QNX 版本、硬件或 QEMU、工具链）、以及真正使用 QNX 的证据。未要求选手到现场或出镜。第一名等奖项亦无线下决赛门槛。提交材料须为英语，或另附英译。

## 本轮推进（2026-11-13）

SDP 8.0 与 `qcc` 已安装。目标演示已用 `qcc -Vgcc_ntox86_64` 编译，并在官方 `mkqnximage` 构建的 QNX 8.0 QEMU 客户机上运行，写出 `traces/qnx-deadlinelens-trace.json`（`source=qnx-periodic-task (captured on QNX)`，`qnx_version=QNX 8.0.0`，`target=qemu`，`toolchain=qcc -Vgcc_ntox86_64`）。主机 CLI 在 `--require-qnx-evidence` 下接受该踪迹（退出码 0），拒绝全部 `sample_*.json`（退出码 2）。

仓库根目录已有 MIT `LICENSE`（Copyright (c) 2026 Baoquan Yang）。**仍需你本人决定后再做的：** 创建公开 GitHub/GitLab/Bitbucket 仓库并把本项目（含根目录 LICENSE）放上去、把不超过 3 分钟的预录演示视频公开到 YouTube、在 Devpost 上正式 Submit。正式提交材料须为英语或另附英译。未执行正式提交，也未创建或推送公开仓库、未发布 YouTube 视频。
