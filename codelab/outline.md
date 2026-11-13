# Codelab 提纲：在 QEMU 上用 QNX 8.0 抓住一次错过的截止期

供后续冲击 Official Rules 中的 Best Codelab / Tutorial bonus（$3,500）。教程必须在提交期内撰写，并教读者如何构建、运行或移植到 QNX：https://qnx.devpost.com/rules

**当前是可以先写完结构的教程草稿，不是已经在 QNX 上跑通过的成品。** 非商用 SDP 8.0 许可已经 Deployed，但本机仍未安装 Software Center / SDP（安装包下载遇到 myQNX 登录墙，见 `notes/sdp-install-blocker-2026-11-12.md`）。凡涉及 SDP / QEMU 启动的命令，都标为「对照当时官方文档填写」，不要把占位命令写成已验证步骤。

官方获取页：https://www.qnx.com/getqnx  
中国站：https://china.qnx.com/products/everywhere/  
QNX 8.0 文档入口（待对照，不预先编造具体命令）：https://www.qnx.com/developers/docs/

---

## 读者现在不用 SDP 也能跟做的部分（第 0 章）

这些步骤已经可以在普通 Linux 主机上完成，用来理解工具和报告长什么样：

1. 克隆或打开本仓库，运行 `python3 tests/test_deadlinelens.py -v`。
2. 生成示例报告：

   ```bash
   python3 -m host.deadlinelens.cli traces/sample_missed_deadline.json -o report.html
   ```

3. 打开 `report.html`：蓝色条是在截止期前结束的 job，红色条是在截止期或之后结束的 job，黄色条是从 release 到 start 的等待，灰色虚线是相对 deadline，小三角是 release。把鼠标放到色条上可以看到松弛（slack）或迟到量（tardiness）。表格还包含响应时间、周期抖动，以及根据应用层事件近似得到的优先级倒挂。结束时刻刚好落在 deadline 上的 job 也算错过。
4. 再打开另外几份示例，对照同一份报告（都是手写示例，不是 QNX 上采到的，不能当参赛证据）：

   ```bash
   python3 -m host.deadlinelens.cli traces/sample_exact_deadline.json -o /tmp/exact.html
   python3 -m host.deadlinelens.cli traces/sample_jitter.json -o /tmp/jitter.html
   python3 -m host.deadlinelens.cli traces/sample_priority_inversion.json -o /tmp/inversion.html
   ```

   - `sample_exact_deadline.json`：worker 的第 2 个 job 刚好在 deadline 结束，应显示 1 次 miss，tardiness 为 0，并标成 exact boundary。
   - `sample_jitter.json`：release 间隔相对 10 ms 周期最大偏差 1.5 ms，没有 miss。
   - `sample_priority_inversion.json`：低优先级线程在跑时，高优先级线程已经 ready。
5. （可选，仍不是参赛证据）编译 POSIX 回退演示，再把生成的 JSON 送进同一 CLI。见 `target/posix_fallback/README.md`。写出的 JSON 会在 `source` 字段标明这不是参赛证据。

这一章的目的：让读者先看懂「主机工具在找什么」，再进入必须使用 QNX 8.0 的章节。

---

## 计划中须在 SDP 可用后补写的章节

下列标题保留，正文只写目标和需要对照的官方出处，不填写未验证的命令。

### 1. 获取 QNX Everywhere / SDP 8.0

- 非商用授权已申请并 Deployed。安装步骤仍是：用已登录的 myQNX 会话下载 QNX Software Center，再安装 SDP 8.0（官方 Quickstart：https://www.qnx.com/developers/docs/8.0/com.qnx.doc.qnxsdp.quickstart/topic/install_host.html）。
- 记录实际版本号、主机操作系统、工具链路径（规则要求提交写明 QNX 版本、目标与工具链）：https://qnx.devpost.com/rules
- 教程里保留许可与安装步骤，不要写成「本机已经跑过 QEMU」。

### 2. 用官方示例在 QEMU 中启动

- 具体启动行、镜像和 `buildfile` 以当时 SDP 8.0 示例与文档为准，不在未安装 SDP 时编造命令。
- 说明为什么 QEMU 足够：官方规则允许目标为硬件或 QEMU，不强制开发板。
- 记录串口或屏幕输出，作为后续演示视频的素材。

### 3. 把周期任务编进镜像并复现一次 miss

- 实现 `target/qnx/deadline_trace.h` 与 `periodic_task.c` 中的应用层埋点，写出 `deadlinelens-trace/v1` JSON（schema 见 `host/deadlinelens/schema.py`）。
- 两个周期线程（例如 10 ms），其中一个 job 故意超时，使 miss 可复现。
- 可选：再保留一份 QNX `tracelogger` 原始输出作为补充证据；具体参数必须对照 QNX 8.0 文档再写，不在此处预填。

### 4. 在主机打开同一份踪迹

```bash
python3 -m host.deadlinelens.cli /path/to/qnx-trace.json -o report.html
```

对照：红色时间条、虚线截止刻度、Missed deadlines 表中的 job 号应与目标程序设计的那一次超时一致。

### 5. 为什么这里需要实时调度

- 用报告解释周期、截止期、优先级：普通分时系统很难稳定保证「必须在 deadline 前结束」。
- 点明主机工具的价值：把一次可复现的 miss 变成可视证据，而不是只在 README 里写「运行在 QNX 上」。
- 这一节直接对应规则里 Potential Impact / Technological Implementation 对「真正在 QNX 上做出非平凡实现」的要求。

### 6. 附录

- JSON schema 字段：`format`、`threads`（id、name、priority、period_ns、deadline_ns）、`events`（t_ns、type、thread_id、job）。
- 提交 README 模板（填空，不编造版本）：

  | 项 | 填写 |
  | --- | --- |
  | QNX 版本 | （SDP 安装后填写，例如 8.0.x） |
  | 目标 | QEMU 或具体硬件 |
  | 工具链 | （例如 qcc 路径，安装后填写） |
  | 如何构建 | 链接到经 SDP 验证的命令 |
  | 如何得到 JSON | 目标程序路径与输出文件 |
  | 如何生成报告 | `python3 -m host.deadlinelens.cli …` |

- 常见问题：只在主机跑 POSIX 回退不能当作证据；JSON 与 schema 不符时主机工具会拒绝解析。
- 演示视频分镜（规则：须展示作品在目标设备上运行，≤3 分钟，评委不必看超过 3 分钟；英语或英文字幕，公开 YouTube）：

  1. 0:00–0:20 问题：错过截止期难以一眼看出。
  2. 0:20–1:10 QEMU 中运行周期任务（SDP 可用后录制）。
  3. 1:10–2:10 打开主机报告，指向红色 miss 与表格。
  4. 2:10–2:50 说明 schema 与构建方式，重申这是 QNX 8.0 上的证据。

---

## 完成后仍须补上、现在不能假装已有的证据

- 实际 QNX 8.0 版本号与工具链路径
- 经文档核对的 QEMU 启动与构建命令
- QEMU 运行记录（串口/屏幕）
- 由 QNX 目标写出的 JSON（不是 `traces/sample_missed_deadline.json`，也不是 POSIX 回退输出）
- 演示视频中「目标上在跑 + 主机报告」的连续画面
