# MASBench T1 runner 身份现场复验预算

2026-11-19 Asia/Shanghai。拟在 HPC 固定 Ollama 0.11.11、`qwen2.5:7b`、1024 窗口上执行一次。输入、故障触发和资源上限沿用上一轮四例方案。唯一本轮现场变化是渲染与生成沿用同一默认 runner 选项，并增补响应后身份与卸载退出证据。 [首轮验收](../reports/masbench_t1b_formal_acceptance_2026-11-19.md) [固定复验计划](masbench_t1b_formal_runner_retest_plan.json)

| 项目 | 上限 |
| --- | --- |
| 合成输入 | 超窗负控制、正常生成、发送后 watchdog、控制器中断、恢复后生成各一次。真实题目零曝光。 |
| 派发与 Token | 最多四次生成，预留 4096 输入／1088 输出，每个请求输入和输出预留之和 ≤1024。无自动重试。 |
| 时间 | 现场 1020 秒，920 秒封闭新派发。准备 150 秒且仅渲染 120 秒内，生成阶段 60 秒，watchdog 从实际发送起 0.25 秒，单次清理 40 秒。禁网回归与独立审计各 90 秒。 |
| 服务操作 | 复验期间独占项目 Ollama。现场渲染 4，常规 GET 24，清理 GET 16，卸载 4。旧锁处置只读进程、连接、证据及资源状态，额外模型或 HTTP 请求为零。 |
| 资源 | 2 CPU，Driver RSS 2 GiB，服务 RSS 和显存各 16 GiB，新增 SSD 总计 ≤56 MiB，回传 ≤56 MiB。既有 helper 只校验 SHA，无重新构建。 |

现场前核实正式失败登记、绑定预算账本、标记原始 210 字节和 SHA，以及两个记录的 PID 和启动时间。保留原始运行目录，将原标记、相关证据和处置凭证写入个人 HDD 并读取校验。持有同一个文件的独占锁时重新检查项目服务身份、子进程、连接及显存。达到全部条件后仅清空活动标记。超时和中断的旧请求预留继续留在原账本。任何身份、配额、服务独占或恢复验证失败即停。

登记入口为 `scripts/hpc_runs.py run --gzip-source-patch`。正式运行 `hpc-masbench-t1b-formal-runner-retest-20261119` 执行 `timeout --kill-after=2s 1018s {python} experiments_ext/masbench_t1b_live.py`；独立审计 `hpc-masbench-t1b-formal-runner-retest-audit-20261119` 执行 `timeout --kill-after=2s 88s prlimit --as=2147483648 -- {python} experiments_ext/masbench_t1_runner_evidence_audit.py formal-runner-retest`。现场仅在本轮定额和锁处置授权完成后生成一次性授权文件。

验收需通过所有四例、超窗拒绝、请求与 runner 同一身份、三次独立卸载及原进程退出核验。原生即时取消及通用模型任务能力仍各自等待验证。T2 与真实四题按既有顺序关卡执行。
