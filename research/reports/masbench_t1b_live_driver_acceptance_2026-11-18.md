# MASBench T1-B 真实服务合成验收

2026-11-18 Asia/Shanghai

**结论：T1-B 未通过，T1 整体保持阻断。** 正常请求验证了真实模型身份、同源计数、完整提示词和实际 usage。watchdog 验证了请求发送、客户端超时、向自有 HTTP worker 发信号以及未知用量保留。卸载 API 已确认，驻留列表为空，但缺少请求对应的旧 runner 的 PID 和进程启动时间。外层验收停止了后续派发。控制器中断和恢复请求均未执行，T2 和正式 B1 保持关闭。

## 研究问题和证据范围

[HYPOTHESIS] 在真实服务上，Driver 应能在派发前确定完整输入能装进窗口，先记账再发送。超时或中断后，应在证明旧 runner 已退出、服务和资源已恢复之后才重新允许派发。

[CODE] 本轮是工程验收。完整消息经 `LiveDriver.attest` 同源计数，匹配真实 Ollama 所渲染的模板与实际窗口，生成继续走 `ControlledClient.generate`。持久账本和控制事件分别记录 token 预留、结果和服务清理，相关实现位于 `execution_safety.py`、`fixture_driver.py` 和 `live_driver.py`。原 GOSC 调度、无线信道和算法主张未参与本轮。无新增论文主张或科学任务效果样本。

[RUN] 授权范围为冻结的虚构用例，最多四次生成。模型为已有 `qwen2.5:7b`，Ollama 0.11.11，配置和现场窗口为 1024。HPC 为 `n1`，base `d5f5522f99872d7453ef54cce06c9ae941846877`，Python 来自项目 `.venv`，2 CPU、24 GiB 内存。服务身份为 PID `37483`，启动标识 `4897373256`。helper SHA-256 为 `e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5`。本轮复用现存二进制，D1 划分及真实题目曝光数维持原记录，真实题目曝光为 0。

## 登记过程及负结果

| HPC 登记 | 实际结果 |
| --- | --- |
| `hpc-masbench-t1b-wiring-regression-20261118` | 40 项无网络接线回归通过。5.589345 秒，回执 `20261118T050052Z-06c2ae`。 |
| `hpc-masbench-t1b-live-20261118` | 超窗负控制写入账本时触发 EDQUOT。零 HTTP、零生成、零 token 预留。退出码 1，登记面板刷新另报 EDQUOT。 |
| `hpc-masbench-t1b-live-v2-20261118` | 42 MiB 写入探针成功，随后持久账本初始化仍触发 EDQUOT。账本空，控制日志尚未创建，零 HTTP、零生成。登记收尾写状态再次触发 EDQUOT，进程已退出。保留原 `running` 状态副本，补记 `failed`，结束时间和退出码为未知。 |
| `hpc-masbench-t1b-live-v3-20261118` | 改用可选的无损 gzip 登记快照。0 个源文件哈希差异。登记运行 35.627553 秒，退出码 1。两次合成生成已实际发出，按 runner 证据不足条件停止。 |

前两次启动均在对模型发出请求前失败。重新登记只更新 run ID，保留原授权、原计划、失败状态、配额错误和恢复清单。HPC 上三份本轮自建的管理快照以无损 gzip 存放，本地保留已校验的原始文件。登记工具新增可选 `--gzip-source-patch`，本轮第三次的原补丁 24,394,486 bytes，压缩后 1,724,203 bytes，manifest 记录两者 SHA-256。正常登记命令沿用默认原格式。

## 真实服务结果

[RUN] 超窗负控制完整输入为 **2697 tokens**，加输出预留 32 超过 1024，在任何 HTTP 之前拒绝。

| 用例 | 输入／输出预留 | 可确认的实际用量 | 结果 |
| --- | ---: | --- | --- |
| 正常 | 29／32 | 29 输入、2 输出 | 固定模型及模板绑定，完整渲染一致。返回 `OK`，`finish_reason=stop`，usage 与计数一致。 |
| watchdog | 48／512 | `null` | 发送后触发客户端超时，账本保留完整预留。卸载 API 及空列表有证据，旧 runner 退出缺证据。 |
| 控制器中断 | 未预留 | 未执行 | 外层停止。 |
| 恢复后的正常请求 | 未预留 | 未执行 | 外层停止。 |

[RUN] 两次生成合计预留 **77 输入／544 输出**。两个已发出的完整输入加输出上限分别为 61 和 560，均在 1024 内。控制调用共 12 次，其中常规 GET 7、清理 GET 2、debug 2、卸载 1。登记产物 32 个，共 224,675 bytes。资源监视采样 69 次，观测峰值为 Driver RSS 87.9 MiB、服务进程树 RSS 4959.9 MiB、GPU 显存 4960 MiB。

## watchdog 时间线

原始控制日志使用 HPC 单调时钟。下列时间是日志原值，单位为秒。服务端另有本地时区日志和卸载响应 UTC 时间。

| 事件 | seq | 单调时间 | 证据 |
| --- | ---: | ---: | --- |
| 写入生成请求 | 78 | 49070216.407510 | HTTP worker PID 51703，进程启动标识 4907021627。 |
| 客户端 watchdog 超时 | 80 | 49070216.660863 | 距发送约 0.253 秒。 |
| 向 HTTP worker 进程组发送 SIGTERM | 81 | 49070216.662606 | `sent=true`。 |
| 向同一进程组发送 SIGKILL | 82 | 49070216.694135 | `sent=true`，随后观察到 worker 退出码为 −15。 |
| 客户端将请求记为 timeout | 84 | 49070216.722276 | 当前请求已结算为 uncertain，实际 usage 为 `null`。 |
| 第一次清理查询 | 90 | 49070216.899596 | 此时 `/api/ps` 已为空。 |
| 开始显式卸载 | 92 | 49070216.904065 | `old_runners=[]`。 |
| 显式卸载返回并完成空列表核对 | 107 | 49070217.225286 | `done=true`、`done_reason=unload`、驻留列表空。响应时间 06:07:31.625403314 UTC。 |
| Driver 写出派发许可 | 108 | 49070217.238022 | `permitted=true`，旧 runner 退出观察为空，许可缺少必要证据。外层验收随后拒绝继续。 |

[RUN] 服务端日志在 14:07:32 Asia/Shanghai 记录这条生成的 HTTP 499，同一秒还有 `context canceled`。这些记录表明服务端观察到了取消。显式卸载完成后复查时，服务无直接子进程，GPU 0 MiB，服务锁标记为 0 字节。**旧 runner 最后退出的时刻和断连后的即时空闲仍未核验。** 取消信号作用于本轮 HTTP worker 进程组，服务端取消证据来自自己的日志。

## 独立审计和实际命令

[RUN] 独立审计登记 `hpc-masbench-t1b-live-evidence-audit-20261118`，0.148867 秒，exit 0。它复核 32 项登记产物哈希、账本和控制日志的哈希链、gzip 补丁及原始 SHA、两个已发请求与完整渲染、窗口和预算、控制端信号顺序，以及服务端 200 和 499 记录。审计结果为 `acceptance_passed=false`，两份日志之间的取消证据一致，但派发恢复证据不足。审计全程零模型调用。

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-live-v3-20261118 --kind test --stage T1-B --purpose authorized-frozen-synthetic-driver-acceptance-after-two-zero-call-startup-failures --model qwen2.5:7b --config research/protocols/masbench_t1b_synthetic_execution_plan.json -- {python} experiments_ext/masbench_t1b_live.py
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-live-evidence-audit-20261118 --kind analysis --stage T1-B --purpose independent-failed-prefix-watchdog-runner-and-ledger-audit --config research/protocols/masbench_t1b_synthetic_execution_plan.json -- {python} experiments_ext/masbench_t1b_evidence_audit.py
```

实际生成和审计在 HPC 执行，两次执行的源码同步 ID 分别为 `20261118T060234Z` 和 `20261118T062452Z`。证据见 [真实运行摘要](../sync/runs/hpc-masbench-t1b-live-v3-20261118/outputs/summary.json)、[控制日志](../sync/runs/hpc-masbench-t1b-live-v3-20261118/outputs/driver/control.jsonl)、[账本](../sync/runs/hpc-masbench-t1b-live-v3-20261118/outputs/driver/campaign/ledger.jsonl)、[服务端事件摘录](../logs/masbench-t1-driver-2026-11-17/t1b_service_observations_localtime.json)及[独立审计](../sync/runs/hpc-masbench-t1b-live-evidence-audit-20261118/outputs/audit.json)。

[RUN] 本地使用 `python scripts/hpc_runs.py pull --max-bytes 104857600` 回传。双方留存[回执](../sync/receipts/20261118T063007Z-069719.json)，全部登记产物已镜像。回执覆盖全仓运行清单，新增下载 5,837,544 bytes。

## 可否进入下一阶段

**No-Go。** 需在派发前固化实际 runner 的 PID、启动标识及其所属服务的证据。恢复时应逐一核对这些身份，在证据缺失时保持锁和账本栅栏关闭。验收应覆盖服务已提前清空驻留列表的情况，仍能把退出观察绑定回派发前的 runner。完成针对性无模型回归和审查后，另行提出真实合成验收预算。正式 B1 真实题目仍须等 T1、T2 等前置关卡通过后另行批准。
