# MASBench T1 正式四例合成验收预算

2026-11-19 Asia/Shanghai。状态为待单独批准。目标是在已安装的 Ollama 0.11.11、固定 `qwen2.5:7b` 和 1024 窗口上验证 Driver 的真实运行合同。输入保持原四例虚构输入和一条超窗负控制。无真实 MASBench 题目、无新模型、无服务配置变更。

[RUN] 单次冷渲染诊断成功，发送到结果 10.05 秒，GPU 峰值 4.84 GiB，旧标记已处理。之前真实渲染先后在约 30 和 60 秒处超时，两次历史失败保留。120 秒是拟议的停机上限。 [诊断报告](../reports/masbench_t1_cold_load_diagnostic_2026-11-19.md)

| 项目 | 上限 |
| --- | --- |
| 按顺序的合成用例 | 超窗负控制在派发前；正常生成、发送后 watchdog、发送后控制器中断、恢复后正常生成各一次。计划内无重试。 |
| 生成调用与预留 | 最多 4 次，输入 4096／输出 1088 tokens；四例输出预留 32／512／512／32；每次完整输入加输出预留 ≤1024。 |
| 各阶段时钟 | 每例准备与绑定合计 150 秒，其中仅渲染 RPC ≤120 秒。身份与计数绑定成功后，普通生成及派发前身份复核另有 60 秒；watchdog 仍在生成发送后 0.25 秒触发。每次卸载与证据核查合计 40 秒。 |
| 现场墙钟 | 1020 秒，920 秒后停止新的真实派发。上界核算参考 20 秒起步 + 4 × (150 + 60) + 3 × 40 = 980 秒，其余供登记与边界余量。 |
| HTTP | 生成 4，渲染 4，常规 GET 24，清理 GET 16，卸载 4。失败即保留已经预留的额度。 |
| HPC 资源 | 2 CPU。Driver 进程树 RSS 2 GiB，服务进程树 RSS 和 GPU 显存采样各 16 GiB。 |
| 夹具、审计与磁盘 | 禁网夹具 90 秒，独立只读审计 90 秒。真实产物 ≤16 MiB，夹具 ≤16 MiB，审计 ≤8 MiB，登记源快照及回执预算 16 MiB，新增 SSD 总预算 56 MiB。回传 ≤56 MiB。 |

复验时段独占项目 Ollama。先核查服务 PID 与启动标识、模型/模板/helper SHA、空驻留、恢复标记、个人配额与持久写入。任何用例未达到故障触发、身份不符、计数不一致、证据不完整或资源越界即停止派发。清理只针对本轮自有工作进程和已核验模型，必要时保留恢复标记。独立审计须重算分段时钟、真实用量、未知用量、保守预留、信号、卸载、旧 runner 退出及恢复派发。原生即时空闲仍单列。

实运行与审计均在 HPC 原路径通过 `scripts/hpc_runs.py run --gzip-source-patch` 登记。启动前冻结源、计划、预算及服务身份，建立新授权与唯一登记。现场和只读审计命令拟为：

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-formal-20261119 --kind test --stage T1-B --purpose approved-four-case-acceptance-separated-phase-clocks --model qwen2.5:7b --config research/protocols/masbench_t1b_formal_plan.json -- timeout --kill-after=2s 1018s {python} experiments_ext/masbench_t1b_live.py
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-formal-audit-20261119 --kind analysis --stage T1-B --purpose independent-four-case-acceptance-and-phase-clock-audit --config research/protocols/masbench_t1b_formal_plan.json -- timeout --kill-after=2s 88s prlimit --as=2147483648 -- {python} experiments_ext/masbench_t1_runner_evidence_audit.py formal
```

正式四例独立审查通过后才重新评估 T2。真实 B1 受既有单独关卡和授权约束。
