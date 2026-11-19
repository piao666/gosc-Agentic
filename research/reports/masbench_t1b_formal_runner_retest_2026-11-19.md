# MASBench T1 runner 更替核对与复验

2026-11-19 Asia/Shanghai，基准提交 `d5f5522f99872d7453ef54cce06c9ae941846877`。本轮核对上次最终清理阶段的 runner 更替，并检查同一 runner 的身份和退出证据能否从派发贯穿至卸载。验收对象是实验执行器。 [首轮验收](masbench_t1b_formal_acceptance_2026-11-19.md) [本轮预算](../protocols/masbench_t1b_formal_runner_retest_budget_2026-11-19.md)

## 重载条件

[CODE] HPC 的固定 Ollama 0.11.11 源码中，`server/routes.go:96–107` 按服务默认、模型参数、请求参数的顺序叠加选项。`api/types.go:755–759` 的默认 `NumThread` 为 `0`，由运行时选择线程数。`openai/openai.go:502–526` 的兼容生成映射只把本次请求相关的 `max_tokens` 和 `temperature` 写入生成选项，未覆盖 `NumThread`。固定模型的参数层也未定义 `num_thread`。`server/sched.go:582–615` 比较的是整个 `Runner` 选项；`2` 对 `0` 已足以满足重载条件。该条件与旧日志中仅渲染成功后再次启动 runner 的顺序一致。健康检查等条件也可能触发重载，旧日志没有给出逐字段判定。 [旧现场服务日志索引](../logs/masbench-t1-driver-2026-11-17/t1_formal_reload_observation_20261119.json)

[CODE] Driver 的仅渲染请求现在沿用与兼容生成相同的 runner 默认选项。正常响应后再次核对 PID 和启动时间。若发现未绑定身份，记录出现时间和身份，在卸载中单独检查其退出，并保留派发栅栏。既有同源计数、完整渲染、预算账本和两条故障路径继续通过原入口。复验审计将从控制链重算上述身份和请求散列。 [Driver](../../extensions/masbench_reasoning/live_driver.py) [复验审计](../../experiments_ext/masbench_t1_runner_evidence_audit.py)

## HPC 回归与现场前置

[RUN] 在节点 `n1`，项目 Python 3.11.15，源码快照 `20261119T070540Z` 的 1227 个文件均通过 SHA-256 核验。经 GOSC HPC 登记运行 `timeout --kill-after=2s 88s {python} experiments_ext/masbench_t1a_contract.py`。53 项禁网测试通过，测试用时 7.013 秒、登记耗时 7.458177 秒；输出 6,110,172 bytes。增加的用例核对渲染实际载荷和成功响应后的身份，并模拟新 runner 在清理前已退出的情形，验证其退出仍有单独记录且不得释放栅栏。使用既有假模型和假服务，现场 HTTP 和模型生成均为零。 [回归登记](../sync/runs/hpc-masbench-t1b-formal-runner-retest-contract-20261119/manifest.json)

[RUN] 复核 SSD 可用 147,906,560 bytes（约 141.05 MiB），HDD 可用 517,861,826,560 bytes（约 482.29 GiB）。从上轮原始控制链和账本确认 PID `54817`、`54844` 的启动时间均已不存在，该 Ollama 服务身份仍匹配，无活跃连接和登记任务，显存占用 0 MiB。上轮 210 字节恢复锁 SHA-256 仍匹配，两笔故障 `usage=null` 和原预留保持在旧账本。 [配额核验](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_t1_formal_runner_retest_20261119.json) [只读锁核验](../logs/masbench-t1-driver-2026-11-17/t1_formal_marker_recovery_readonly_20261119.json)

[RUN] 禁网登记的 510 个文件已逐文件核对 SHA-256，回传凭证在两端保存。 [回传凭证](../sync/receipts/20261119T071034Z-t1-formal-runner-retest-fixture-scoped.json)

## 旧锁归档与现场执行

[RUN] 用户确认本轮归档、清空旧活动锁及独占项目 Ollama 的四例预算。在 `/hdd/u202520081000097/gosc-archive/2026-11-19-t1-formal-failed-lease` 归档由旧锁、旧控制链、旧账本、旧登记状态、旧摘要和原独立审计组成的六份原件，逐份验证 SHA-256 读回，并保存清锁前和完成凭证。2026-11-19 07:15:08.574030 UTC 持独占锁清空活动标记。旧两笔 `usage=null` 和预留保留在原账本。这一步没有 HTTP 或模型调用。 [归档及清锁凭证](../logs/masbench-t1-driver-2026-11-17/t1_formal_marker_recovery_applied_20261119.json)

[RUN] HPC `n1`、2 CPU、Python 3.11.15。固定 Ollama 0.11.11、`qwen2.5:7b`、有效窗口 1024。源码及授权通过快照 `20261119T071534Z` 上行，1238 个文件通过 SHA-256 校验。登记 `hpc-masbench-t1b-formal-runner-retest-20261119` 通过 `timeout --kill-after=2s 1018s {python} experiments_ext/masbench_t1b_live.py` 执行，无随机种子。现场历时 **28.762073 秒**，退出码 0。超窗负控制在 HTTP 前拒绝，固定四条合成请求之外的真实题目输入为零。 [授权](../protocols/masbench_t1b_formal_runner_retest_authorization.json) [执行命令与环境](../sync/runs/hpc-masbench-t1b-formal-runner-retest-20261119/manifest.json) [现场摘要](../sync/runs/hpc-masbench-t1b-formal-runner-retest-20261119/outputs/summary.json)

| 用例 | 预留输入／输出 tokens | 实际用量 | 进程及处置 |
| --- | ---: | --- | --- |
| 正常 | 29／32 | 29／2 | `OK`，请求派发和响应后 runner 同为 PID `56965`，启动标识 `4916076832`。 |
| watchdog 超时 | 48／512 | `null` | 发送后 0.250656 秒触发超时。向 HTTP worker `57012` 实际发送 SIGTERM 和 SIGKILL。PID `56965` 退出证明入账后许可恢复。 |
| 控制器中断 | 38／512 | `null` | 发送后约 4.9 毫秒向控制器 `57034` 发出 SIGKILL 并核实退出，HTTP worker `57065` 收到实际发出的 SIGTERM 和 SIGKILL。PID `57047` 退出证明入账后许可恢复。 |
| 恢复生成 | 29／32 | 29／2 | `OK`，请求派发和响应后 runner 同为 PID `57090`，启动标识 `4916078546`。最终卸载核验该身份退出。 |

[RUN] 三次卸载在单调时钟 `49160779.25432259`、`49160783.576692514`、`49160794.44591951` 开始，于 `49160779.83878916`、`49160784.15436474`、`49160795.01679298` 完成身份、空驻留和显存核查。前两次分别在 `49160779.84835864`、`49160784.16649918` 记录恢复派发许可，后续请求均实际发出。终末清理完成时四次调用和 1088 个输出 tokens 的预留额度已用完，派发许可为 false。服务空闲、活动锁 0 字节、显存 0 MiB，Ollama PID 和启动标识未变。 [原始控制链](../sync/runs/hpc-masbench-t1b-formal-runner-retest-20261119/outputs/driver/control.jsonl) [现场后核查](../logs/masbench-t1-driver-2026-11-17/t1_formal_runner_retest_postflight_20261119.json)

[RUN] 四次生成共预留 **144 输入／1088 输出 tokens**。两笔未知用量合计保留 86 输入／1024 输出 tokens 预留。渲染 4、常规 GET 15、清理 GET 9、卸载 3。57 次资源采样中 Driver RSS 峰值 89,927,680 bytes，服务树 RSS 4,616,704,000 bytes，显存 5,200,936,960 bytes。现场登记产物 58 个共 251,642 bytes。两次个人配额采样间 SSD 用量净增 5,283,840 bytes，回传前余 130,768,896 bytes。 [执行前配额](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_t1_formal_runner_retest_approved_20261119.json) [执行后配额](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_t1_formal_runner_retest_after_20261119.json)

## 独立审计与验收

[RUN] 独立登记 `hpc-masbench-t1b-formal-runner-retest-audit-20261119` 以退出码 0、0.162362 秒完成。核对了 58 个现场产物、发出的完整请求与渲染散列、计数和窗口、两条成功响应前后的 runner 身份、两笔未知用量、故障信号、三次清理及后续派发。`acceptance_passed=true`。现场及独立审计两个目录共 75 个文件、4,962,944 bytes，通过 SHA-256 核验并保存双端回传凭证。 [审计执行登记](../sync/runs/hpc-masbench-t1b-formal-runner-retest-audit-20261119/manifest.json) [独立审计](../sync/runs/hpc-masbench-t1b-formal-runner-retest-audit-20261119/outputs/audit.json) [回传凭证](../sync/receipts/20261119T071840Z-t1-formal-runner-retest-scoped.json)

**T1 通过固定部署下的合成端到端验收。** 对齐 runner 选项之后，两次正常生成均复用对应的派发前 runner，原失败结论保持为上一轮记录。运行证据支持“线程选项差异触发旧重载”的解释，旧服务日志未记录逐字段的实际判定。客户端断开后仍通过显式卸载和退出观察确认空闲，原生即时取消保留未验证状态。后续 T2 配置决策和真实四题 B1 各自等待授权与前置条件。
