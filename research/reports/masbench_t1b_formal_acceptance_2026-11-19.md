# MASBench T1 正式四例合成验收

2026-11-19，Asia/Shanghai。对应 [已批准预算和命令](../protocols/masbench_t1b_formal_budget_2026-11-19.md) 与 [固定输入](../protocols/masbench_t1b_formal_plan.json)。本轮验收的研究问题是，真实 Driver 能否在不截断合成输入的情况下，持久约束请求/Token、核验模型身份，并在超时和中断后按证据恢复派发。结果只用于工程验收。数据分区与既有科学判定沿用原记录。

## 接线和授权

[CODE] `extensions/masbench_reasoning/live_driver.py` 只对正式方案的仅渲染 POST 扩展至 120 秒，完整准备和绑定限 150 秒，生成阶段另起 60 秒，发送后 watchdog 用 worker 的实际发送时间起算 0.25 秒。生成保持持久预留、同源完整计数、`ContextBinding` 和 `ControlledClient` 路径。清理预算 40 秒，退出观察用本轮已记录的 PID/启动时间校验。与原 GOSC 任务算法、调度、无线预算和论文收益无关。

[RUN] 先在 HPC 内核禁网回归 `hpc-masbench-t1b-formal-contract-20261119`，51 项通过，测试用时 6.570 秒，登记用时 6.912235 秒，产物 5,833,033 bytes。之后用户批准该次独占项目 Ollama、最多四次生成、4096 输入／1088 输出、现场 1020 秒、SSD 新增 56 MiB。现场预检未见活动登记或已建立连接，恢复标记为 0，GPU 0 MiB，SSD 个人可用约 148.73 MiB。已有词表 helper SHA 一致。

[RUN] 真实登记基准 `d5f5522f99872d7453ef54cce06c9ae941846877`，`n1` 项目 .venv，2 CPU，Ollama 0.11.11、`qwen2.5:7b`、1024 窗口。执行快照 `20261119T064308Z`，1218 文件、0 SHA 差异。冻结命令在预算文件中。此前两次 499 和单次冷渲染的结果都有各自登记。 [授权预检](../logs/masbench-t1-driver-2026-11-17/t1_formal_preflight_20261119.json)

## 四例及最终停机

[RUN] `hpc-masbench-t1b-formal-20261119` 登记耗时 104.22154 秒，exit 1。超窗负控制在任何 HTTP 前拒绝。四个生成派发均有真实发送记录，完成后最终清理因身份差异保持栅栏。真实题目曝光为 0。 [真实摘要](../sync/runs/hpc-masbench-t1b-formal-20261119/outputs/summary.json)

| 固定用例 | 请求预留（输入／输出） | 已知实际用量 | 现场结果 |
| --- | ---: | ---: | --- |
| 正常 | 29／32 | 29／2 | 生成正常完成，返回 `OK`。 |
| watchdog | 48／512 | `null` | 已派发，在发送后 0.250837 秒记录 timeout。自有 HTTP worker 记录 SIGTERM、SIGKILL，进程返回 −15。卸载、原 runner 身份退出、空驻留和显存采样核验后恢复派发。 |
| 控制器中断 | 38／512 | `null` | 已派发，约 0.005 秒后向自有控制器发 SIGKILL，记录控制器退出，另记录 HTTP worker 信号。卸载、原 runner 身份退出、空驻留和显存采样核验后恢复派发。 |
| 恢复生成 | 29／32 | 29／2 | 恢复后再次派发，生成正常完成并返回 `OK`。随后最终清理没有通过。 |

[RUN] 合计预留 **144 输入／1088 输出 tokens**。两条故障请求实际用量保持未知，分别保留完整预留。常规 GET 15、清理 GET 8、渲染 4、卸载 3。采样 203 次，Driver RSS 峰值 116,719,616 bytes、服务树 RSS 5,374,939,136 bytes、GPU 显存 5,200,936,960 bytes。现场登记产物 58 个，251,373 bytes。

[RUN] 最后一次派发前绑定 PID `54817`、启动标识 `4915893959`；最终卸载前现场进程已是 PID `54844`、启动标识 `4915894302`。API 已回复显式卸载成功，驻留列表为空，现场复查 GPU 0 MiB；最终 Driver 缺少对新身份的完整退出证据，记录 `unload-unverified` 并保留 210 字节标记，SHA-256 `b5b58650e78e392a8b58700e0e438414f4d0cf2d2440abf9c87da156dca4a52b`。旧已绑定身份退场、现场无剩余 runner、API ACK 分别是记录事实，恢复栅栏保持关闭。原生即时取消依然未验收。 [原始控制链](../sync/runs/hpc-masbench-t1b-formal-20261119/outputs/driver/control.jsonl)

## runner 更替的定位

[RUN] 最后一个用例服务日志先在本地时间 14:46:14 记录 runner 启动，14:46:15 完成仅渲染。14:46:17 再次记录启动，随后生成在 14:46:27 返回 200，14:46:28 卸载返回 200。固定模型 manifest 的参数层没有 `num_thread` 或 `num_ctx` 覆盖。 [原始日志偏移、SHA 与模型参数](../logs/masbench-t1-driver-2026-11-17/t1_formal_reload_observation_20261119.json)

[CODE] Driver 的仅渲染调用显式设 `num_thread=2`，本轮实际 OpenAI 兼容生成 payload 只有 `max_tokens/messages/model/stream/temperature`。Ollama 0.11.11 的 `openai/openai.go:405–574` 将该请求转为常规 `ChatRequest`，不传 `num_thread`；`api/types.go:755–759` 默认 `NumThread=0`。`server/sched.go:582–615` 的 `needsReload` 比较两个 Runner options 并也检查 runner ping。 [Driver 源码](../../extensions/masbench_reasoning/live_driver.py)

[HYPOTHESIS] 请求线程选项不同足以触发该版本重载，是当前观测到的 runner 更替最强解释。服务日志没有逐字段打印本次重载判定，其他触发条件仍待受控核验。后续先让渲染和生成的有效 runner 选项一致，再用针对性禁网合同覆盖中途重载与最终退出证明。确认后为新一轮拟预算，旧恢复标记按本次四条发送及未知用量保留证据后单独处置。

## 独立证据审计与关卡结果

[RUN] `hpc-masbench-t1b-formal-audit-20261119` 核验了失败前缀、账本与硬预算，登记用时 0.160901 秒。补充审计 `hpc-masbench-t1b-formal-audit-detail-20261119` 用时 0.145068 秒，逐例复核了四个请求 ID、派发时间、窗口约束、已知或未知用量、两个故障清理的 runner 退出证据，以及最终未绑定的 PID `54844`。两次审计均以 exit 0 完成，记录的验收判定均为 `acceptance_passed=false`。 [首份审计](../sync/runs/hpc-masbench-t1b-formal-audit-20261119/outputs/audit.json) [四例补充审计](../sync/runs/hpc-masbench-t1b-formal-audit-detail-20261119/outputs/audit.json)

[RUN] watchdog 清理在单调时钟 `49158880.445825815` 开始，于 `49158880.84458324` 完成，随后恢复控制器用例派发。控制器中断清理于 `49158937.666149095` 开始，`49158938.27909054` 完成，随后恢复生成派发。最终清理在 `49158953.488478705` 开始，`49158954.07607322` 记录 `unload-unverified`。最后一个事件提供 API 应答时的证据，最终清理完成时间和最终派发许可均未确认。 [单调时钟、信号及控制链](../sync/runs/hpc-masbench-t1b-formal-20261119/outputs/driver/control.jsonl)

[RUN] 四个登记目录共 572 个文件、15,510,350 bytes，已在本地逐文件核对 SHA-256，HPC 与本地凭证本身的 SHA-256 一致。 [定向回传凭证](../sync/receipts/20261119T065439Z-t1-formal-scoped.json)

**T1 No-Go。** 两次触发的故障恢复均通过，最终卸载的身份退出合同失败。保持恢复锁及故障预算证据，待修复和针对性禁网验证后再审查现场复验。T2 与真实四题 B1 仍在等待前置验收和各自授权。
