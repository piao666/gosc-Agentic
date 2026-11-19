# MASBench T1 runner 恢复修复与复验

日期 2026-11-18，Asia/Shanghai。对应 [上一次 T1-B 现场失败](masbench_t1b_live_driver_acceptance_2026-11-18.md) 和 [本次批准的固定合成复验预算](../protocols/masbench_t1b_runner_recheck_budget_2026-11-18.md)。

## 修复的具体问题

[RUN] 上一次 watchdog 发送成功后触发超时，第一次清理查询已经返回空驻留列表。Driver 因为在这一刻才寻找 runner，所以未留下旧 PID 和启动时间。日志虽然写出了继续许可，外层验收判定证据不足并停止。

[CODE] 固定 Ollama 0.11.11 的 `llm/server.go` 用服务自己的可执行文件，以 `runner --model <blobs 路径>` 启动子进程。Driver 现在在模型身份、窗口和完整渲染核对时，把服务 PID／启动时间下的实际 runner 持久化。在预留和发送前复查 runner 仍是同一个，再记录该身份与请求编号及 payload 哈希的绑定。

[CODE] 恢复从当前服务锁期间的持久记录取 runner 身份。卸载后核对旧 PID 对应的启动时间已经消失或变更、当前服务无 runner、驻留为空，并重新采样 Driver、服务内存和 GPU 显存。任何缺失或不符都保留锁和恢复限制。保守 token 预留保留，未知实际用量仍记为 null。

## 无模型合同和证据审查

| HPC 登记 | 结果 |
| --- | --- |
| `hpc-masbench-t1-runner-recovery-contract-20261118` | 46 项断言通过。模拟 proc 的三条软链留在产物目录，登记拒绝并记录失败。移到专用临时目录，原路径、目标、失败状态和常规产物均保存。 |
| `hpc-masbench-t1-runner-recovery-contract-v2-20261118` | 47 项通过。含提前空驻留、旧进程仍活、PID 复用、派发前身份变化、缺少身份、资源复测失败和持久账本重开。测试 7.620 秒，登记 7.942982 秒，产物 5,695,395 bytes。 |
| `hpc-masbench-t1-runner-recovery-audit-20261118` | 0.288747 秒，exit 0。独立复核最终登记的 469 个产物及 7 个关键账本与恢复场景。 |

[RUN] 无模型回归使用项目 `.venv`，由内核禁止网络，2 CPU，90 秒和 2 GiB 地址空间上限。真实 HTTP、模型调用和真实题目均为 0。旧 helper 只核验 SHA，沿用既有离线合同。第一轮登记失败未改为成功。 [最终回归](../sync/runs/hpc-masbench-t1-runner-recovery-contract-v2-20261118/stderr.log) · [独立审计](../sync/runs/hpc-masbench-t1-runner-recovery-audit-20261118/outputs/audit.json)

## 经批准的真实合成复验

[RUN] 用户批准本轮复验以及项目服务在验收窗口独占。HPC 为 `n1`，项目基准为 `d5f5522f99872d7453ef54cce06c9ae941846877`。服务 PID 37483，启动标识 4897373256，Ollama 0.11.11，`qwen2.5:7b` 及默认窗口 1024。启动前无已登记活动、无已建立连接、无锁标记、GPU 0 MiB。同源计数 helper SHA 与上一轮相同。配额探针成功写入 20 MiB，文件移除后登记运行。启动源快照 `20261118T074013Z`，1122 文件、0 SHA 不匹配。

[RUN] 登记 `hpc-masbench-t1b-runner-recheck-20261118`，31.942077 秒，退出码 120，状态 `failed`。登记收尾写 `dashboard.json` 时明确收到 EDQUOT。Driver 未留下总结，stderr 为 0 字节，子进程为何退出未完全核验。20 MiB 探针只证明检查当时可写。

[RUN] 超窗负控制在 HTTP 前通过。第一例账本完整计数 29，并记录一次初始 `GET /api/ps` 和一次 `POST /api/chat` 渲染检查的发送。随后持久记录里只出现了一次清理 GET 的额度扣记，无该请求发送标记，也没有 runner 身份或卸载起止证据。**生成数 0，预留输入／输出均为 0，真实 MASBench 题目曝光 0。** 正常生成、watchdog、控制器中断与恢复生成均未执行。

[RUN] 只读核查验证控制链 22 条、预算链 7 条、10 个登记产物，以及两条已发送请求与冻结请求的哈希。服务日志在 15:43:48 记录初始查询 200，在 15:44:18 记录渲染请求 499，与约 30 秒的请求窗口相符。缺少 Driver 侧渲染响应和退出日志，具体卡在模型加载、响应还是证据写入的哪一步未完全核验。 [失败证据核查](../logs/masbench-t1-driver-2026-11-17/runner_recheck_failure_observation_v2.json)

[RUN] 服务退出核查发现测试进程退出、服务无直接子进程、GPU 0 MiB，服务恢复锁仍属于本次 campaign。现时空闲观测缺少此前 runner 身份，故锁保留。无补写实际 usage，无恢复派发。18 个本轮登记文件已逐文件哈希校验并回传。 [本轮登记](../sync/runs/hpc-masbench-t1b-runner-recheck-20261118/status.json) · [控制链](../sync/runs/hpc-masbench-t1b-runner-recheck-20261118/outputs/driver/control.jsonl) · [原始账本](../sync/runs/hpc-masbench-t1b-runner-recheck-20261118/outputs/driver/campaign/ledger.jsonl)

[RUN] `python scripts/hpc_runs.py pull --max-bytes 104857600` 完成本地回传，回执标记 `all_outputs_mirrored=true`。HPC 写入 2,236,516 bytes 的原始回执触发 EDQUOT，留下零字节失败文件。随后 HPC 保存 308,302 bytes 的同名 `.json.gz`，已按原始 SHA-256 `1de8d67965067cc8eee784ad2ac0581d87318ddbcbae4777a7ceece55f879351` 验证可还原。 [完整本地回执](../sync/receipts/20261118T080840Z-e03b60.json)

[RUN] 收尾文档上行 `20261118T081953Z` 也因 EDQUOT 失败。按失败包和上一份已校验清单核对，只有 README 完成写入，另有一个新增管理脚本留下空文件。已恢复原 README 并校验其 SHA，将空文件移到专用临时目录保留，确认真实运行使用的源码和授权匹配 `20261118T074013Z`。本报告和阶段结论保存于本地。 [同步核对](../logs/masbench-t1-driver-2026-11-17/runner_recheck_sync_observation.json) · [恢复记录](../logs/masbench-t1-driver-2026-11-17/runner_recheck_sync_reconciliation.json)

## 阶段结论

**T1-B No-Go，T1 整体未验收。** 代码与无模型合同确认了预绑定和失败关闭逻辑。现场复验未走到生成，故无法判定真实 watchdog、控制器中断或资源复测是否完整。原生即时空闲仍未知。T2 和正式 B1 继续等待。

本轮按已批准预算中的登记命令运行。现场运行未完成，真实合成端到端的独立审计未启动。再次复验前，应先保证运行中的日志、清理记录、摘要和回执有持久证据空间，并独立定位渲染请求的 499。现有恢复锁需通过单独的恢复操作处理，后续真实合成复验须另行确认。
