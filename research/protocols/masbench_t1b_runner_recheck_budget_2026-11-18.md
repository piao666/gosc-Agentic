# MASBench T1-B runner 退出复验预算提案

2026-11-18 Asia/Shanghai。状态为待单独批准。复验只调用项目已有的 Ollama 0.11.11 和 `qwen2.5:7b`，使用当前 1024 窗口与现有同源计数 helper。现场窗口须由用户再次确认该 Ollama 独占。

前一次 T1-B 后两个用例未能派发。新实现改变了派发和恢复条件，复验从同一个新持久账本中的第一条用例走起，保留前次原始记录和未知用量。先做一次无 HTTP 的合成超窗负控制，再按顺序各做一次正常生成、发送后 0.25 秒 watchdog、发送后中断自有控制器、清理后的正常生成。只允许固定四个用例。任一用例未达到触发要求、身份不符、额度超限或清理无证据时停止派发。计划内无重试。

| 项目 | 单次复验上限 |
| --- | --- |
| 生成次数 | 4 |
| 预留 token | 输入 4096，输出 1088。四例输出上限依次为 32、512、512、32 |
| 窗口 | 每次完整提示词计数与输出预留之和不超过 1024 |
| HTTP | debug 4、卸载 4、常规 GET 24、清理 GET 16 |
| 时间 | Driver 480 秒，350 秒后停发，每操作最多 60 秒 |
| 资源 | 2 CPU，Driver 进程树 RSS 2 GiB，服务进程树 RAM 和 GPU 采样各 16 GiB |
| 成果 | 真实运行产物 16 MiB，HPC 单独登记只读审计 90 秒、2 CPU、2 GiB 地址空间，单次证据回传 100 MiB |

派发前留存完整输入、同源计数、模板、服务与模型身份、实际窗口和 runner 的 PID／启动时间。每个故障用例核验实际发送、控制器或 HTTP worker 信号、卸载起止、身份退出和后续派发许可，unknown usage 保持 null，预留额度保留。服务提前清空时仍按先前绑定的进程身份核验。原生即时空闲仍单列。独立审计以新 run 的冻结快照和原始证据为准。

如果用户批准，才生成新授权文件并登记运行。批准仅适用于此复验，模型、服务和默认窗口配置沿用现状，真实 B1 题目曝光为 0。复验结束及独立审查通过后再决定 T2。

HPC 项目根目录中的实际登记命令如下。两个登记均用无损 gzip 记录源码快照。清理只作用于本轮已核验身份的工作进程和模型，不重启服务。若旧进程退出或资源恢复无法核验，保留恢复锁，停止派发。

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-runner-recheck-20261118 --kind test --stage T1-B --purpose approved-runner-identity-synthetic-recheck --model qwen2.5:7b --config research/protocols/masbench_t1b_runner_recheck_plan.json -- {python} experiments_ext/masbench_t1b_live.py
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-runner-recheck-audit-20261118 --kind analysis --stage T1-B --purpose independent-runner-exit-and-budget-audit --config research/protocols/masbench_t1b_runner_recheck_plan.json -- timeout --kill-after=5s 85s prlimit --as=2147483648 -- {python} experiments_ext/masbench_t1_runner_evidence_audit.py live
```
