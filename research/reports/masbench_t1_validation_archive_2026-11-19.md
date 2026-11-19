# MASBench T1 验证总报告

2026-11-19，Asia/Shanghai。归档基线 `d5f5522f99872d7453ef54cce06c9ae941846877`。T1 验证的是实验执行器能否在真实模型上先算完整输入、先记账再派发，以及故障后能否确认运行模型的进程已经退出再放行。固定环境为 HPC `n1`、Ollama 0.11.11、`qwen2.5:7b` 和 1024-token 窗口。原生即时取消仍未验证，真实 MASBench 题目曝光为零。 [六关卡路线](../protocols/masbench_six_gate_roadmap_2026-11-17.md)

**最终结果是 T1 工程验收通过。** 最终 HPC 53 项禁网测试通过，四例真实服务合成复验用时 28.762073 秒，独立证据审计通过。此前的超时、证据缺失、配额与登记失败均保留。 [最终现场报告](masbench_t1b_formal_runner_retest_2026-11-19.md) [独立现场审计](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-formal-runner-retest-audit-20261119__audit.json)

## 从接线到验收

| 阶段 | 验证经过和实际判定 | 证据 |
| --- | --- | --- |
| 前置部署，11 月 17 日 | 已构建同源计数 helper；离线通过 14 项渲染、36 项窗口、6 项 schema 拒绝、4 项 special-token 锚点。真实部署以临时 32768 窗口验证完整长输入、usage 和断连后卸载。服务随后恢复 1024。两项为前置历史，本阶段仅复用 helper 并核验固定 SHA。 | [离线合同](masbench_cpp_offline_acceptance_2026-11-17.md) · [真实部署](masbench_real_deployment_acceptance_2026-11-17.md) |
| T1-A，11 月 18 日 | 接入 `ControlledClient`、`ContextBinding` 和持久账本。31 项首轮断言通过，登记因测试生成的符号链接失败。后续分别通过 36、39、40 项；独立审计首轮因 EDQUOT 未完成收尾，v2/v3 完成。最终 40 项覆盖窗口边界、账本、程序中断、卸载、合成 Full/No-A2A 消息可见性和虚构模型身份隔离。 | [T1-A 报告](masbench_t1a_live_driver_acceptance_2026-11-18.md) · [最终 T1-A 审计](../artifacts/masbench-t1-20261119/hpc-masbench-t1a-evidence-audit-v3-20261118__audit.json) |
| T1-B 首轮，11 月 18 日 | 40 项接线回归通过。两次启动因 SSD 配额在生成前失败，采用有原始与压缩 SHA 的无损 gzip 登记快照后，第三次发出两条合成生成。正常用量可对账；watchdog 有实际工作进程信号及服务端 499／`context canceled`。清理时才寻找旧 runner，空驻留导致缺少 PID 和启动时间，外层停止后两例。独立审计核实失败证据。 | [首轮 T1-B](masbench_t1b_live_driver_acceptance_2026-11-18.md) · [失败审计](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-live-evidence-audit-20261118__audit.json) |
| runner 预绑定，11 月 18 日 | 派发前保存 PID、启动时间和载荷 SHA。46 项断言通过后登记器拒绝软链，修正夹具目录后 47 项及独立审计通过。现场渲染约 30 秒收到 HTTP 499；生成 0 次。登记收尾另遇 EDQUOT，恢复锁保留。 | [复验报告](masbench_t1_runner_recheck_2026-11-18.md) · [控制链](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-runner-recheck-20261118__control.jsonl) |
| 存储与冷加载，11 月 18–19 日 | HDD 复制 47 个文件并逐件验证，实测恢复演练覆盖四项候选。经批准清理四个 SSD 原件后，个人配额增加 196,595,712 bytes，保留内容累计持久写入 48 MiB。旧失败的两版控制日志分别归档。核查显示约 30 秒的 499 出现在冷加载期间，与旧 worker 的固定 socket 截止相符。49 项禁网回归通过；随后现场渲染在约 60 秒操作截止再次取消，生成仍为 0。 | [HDD 归档](hpc_storage_archive_t1_gate_2026-11-18.md) · [SSD 恢复与失败审计](hpc_storage_and_t1_recovery_2026-11-19.md) |
| 单次冷渲染，11 月 19 日 | 首次在复核代码中触发局部变量遮蔽，保留零发送失败；改正后最终 6 项禁网夹具通过。唯一获批现场渲染约 10.05 秒、HTTP 200；记录模型映射、I/O 样本、卸载和 runner 退出。生成 0 次。该样本无法精确分拆 SSD 读取、初始化和权重装载耗时。 | [诊断报告](masbench_t1_cold_load_diagnostic_2026-11-19.md) · [独立审计](../artifacts/masbench-t1-20261119/hpc-masbench-t1-cold-load-audit-v2-20261119__audit.json) |
| 正式四例首轮，11 月 19 日 | 独立计时准备和生成 watchdog，51 项禁网回归通过。四次合成生成均实际派发，两个故障后的恢复栅栏通过。最终清理时 PID 从 `54817` 变为 `54844`，缺少对新身份的退出证明，现场退出 1，保留恢复锁。两次独立审计维持未通过判定。 | [现场失败报告](masbench_t1b_formal_acceptance_2026-11-19.md) · [四例失败审计](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-formal-audit-detail-20261119__audit.json) |
| 对齐 runner 选项并复验，11 月 19 日 | 固定源码显示渲染的 `num_thread=2` 与生成默认值 `0` 会满足重载条件。改为相同默认选项，新增响应后身份和卸载证据。53 项禁网通过。随后旧锁和五份关联证据逐份归档、读回并核验后清空活动标记。真实模型四例全部达到预设结果，三次卸载证实原进程退出，独立审计通过。 | [最终复验](masbench_t1b_formal_runner_retest_2026-11-19.md) · [归档与清锁回执](../logs/masbench-t1-driver-2026-11-17/t1_formal_marker_recovery_applied_20261119.json) |

[RUN] 上述过程共有 **32 次 HPC 登记，22 次 completed、10 次 failed**。两条因配额未能可靠收尾的失败保留未知结束时间及退出码。部分状态为 completed 的登记是独立核查失败证据，其 `acceptance_passed` 仍为 false。测试数量是各版本的结果，包含重复测试。三轮实际派发共 10 次合成生成，其他现场尝试停在渲染或更早步骤。 [完整登记、实际命令及状态](../artifacts/masbench-t1-20261119/run_index.json)

## 最终四例的证据

[RUN] 超窗负控制在 HTTP 请求前被拒绝。生成前固定的完整输入、模板、模型、窗口与 runner 均受校验。正常及恢复生成返回 `OK`，各为 29 输入／2 输出 tokens，两次分别复用派发前的 PID `56965` 和 `57090`。四次派发总预留 144 输入／1088 输出 tokens，两次故障均在持久账本中保留 `usage=null`，合计继续占用 86 输入／1024 输出 tokens。 [现场摘要](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-formal-runner-retest-20261119__summary.json) [持久账本](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-formal-runner-retest-20261119__ledger.jsonl)

[RUN] watchdog 在真实发送后 0.250656 秒触发，HTTP worker 记录发出的 SIGTERM 与 SIGKILL。控制器中断记录发出的 SIGKILL、控制器退出和独立的 HTTP worker 信号。三次卸载均保存开始、完成、原 PID 与启动时间退出观察以及显存复核。两次故障清理后记录派发许可并实际发送下一例。最终卸载之后服务空闲，恢复锁为 0 字节，显存 0 MiB。 [哈希控制链](../artifacts/masbench-t1-20261119/hpc-masbench-t1b-formal-runner-retest-20261119__control.jsonl) [最后服务检查](../logs/masbench-t1-driver-2026-11-17/t1_formal_runner_retest_postflight_20261119.json)

[CODE] 原始 GOSC 调度、信道和任务算法，以及既有 `ControlledClient`、`execution_safety.py`、`fixture_driver.py` 均沿用原代码。新 Driver 接入现有合同，保留审批和预算边界。合成消息、真实服务响应和进程事件提供工程证据，任务样本和任务置信区间在 T1 不适用。 [Driver](../../extensions/masbench_reasoning/live_driver.py) [无模型合同](../../tests_ext/test_masbench_t1_live_driver.py)

## 可追溯文件与下一关

Git 归档覆盖阶段报告、32 条 HPC 登记及日志、30 份通过登记 SHA 核验的关键证据、10 份完整回执的 SHA 及相关文件条目。其余原始产物、源码快照补丁和完整回执沿用原位置与原哈希；HDD 两次归档各有定位及读回记录。 [证据包](../artifacts/masbench-t1-20261119/README.md) [完整回执索引](../artifacts/masbench-t1-20261119/receipt_index.json)

T1 通过的支持域是固定 1024 部署下的显式卸载和进程退出栅栏。线程选项对齐后的证据支持重载解释，早期现场日志未记录调度器逐字段判定。原生即时取消、长期 32768 配置、真实任务能力和通信收益继续等待各自的验证。T2 下一步独立核算资源、长上下文和回滚边界；真实四题 B1 在各前置关卡通过后另行授权。D1 文章隔离及 G1/GP-ID 科学 No-Go 继续适用。
