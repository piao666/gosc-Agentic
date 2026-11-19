# MASBench T1-B 存储恢复后合成复验提案

2026-11-19 Asia/Shanghai。待单独批准。只使用 HPC 项目的已有 Ollama 0.11.11、`qwen2.5:7b`、1024 窗口和同源计数 helper。验收时段使用项目 Ollama 的独占窗口。

[RUN] 前次渲染请求开始冷加载，收到 `context canceled` 并以约 30.07 秒的 HTTP 499 结束。旧 HTTP worker 的固定读取超时为 30 秒，短于 Driver 操作上限 60 秒。新版本让 worker 继承 Driver 的剩余操作时间，硬限仍为 60 秒。超时用例的发送后 0.25 秒 watchdog 独立计时。冷启动最终完成时间仍待现场观察。

| 项目 | 上限 |
| --- | --- |
| 合成用例 | 一次派发前超窗负控制，以及正常、watchdog、控制器中断、恢复后正常各一次 |
| 生成与预留 | 最多四次生成，输入 4096、输出 1088 tokens。单例输出上限 32／512／512／32 |
| 窗口 | 完整提示词计数与输出预留之和每次不超过 1024 |
| HTTP | debug 4、卸载 4、常规 GET 24、清理 GET 16 |
| 时间 | Driver 480 秒，350 秒后停发，单操作 60 秒 |
| 资源 | 2 CPU，Driver 进程树 RSS 2 GiB，服务 RSS 和 GPU 显存采样各 16 GiB |
| 证据 | 运行产物 16 MiB，只读独立审计 90 秒／2 GiB，单次回传 100 MiB |

先复查 SSD 实测写入、恢复标记为空、固定模型身份和当前服务空闲。任何一个用例在故障点之前正常结束、证据缺失、源或服务身份变化、窗口计数不一致、额度触发或清理不完整，停止此轮。证据包含请求身份和发送、实际触发和信号、旧 runner 退出、卸载起止、通过前后资源，以及可核验的恢复派发。未知实际 usage 保持 null，已预留输入和输出保留。原生即时空闲单列。真实题目曝光为 0，原服务配置不变。前次失败不覆写。

用户批准后生成本轮独立授权文件，记录该时段服务身份和冻结快照。HPC 原项目路径下的登记命令如下。

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-post-storage-20261119 --kind test --stage T1-B --purpose approved-post-storage-cold-render-synthetic-acceptance --model qwen2.5:7b --config research/protocols/masbench_t1b_post_storage_plan.json -- {python} experiments_ext/masbench_t1b_live.py
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --gzip-source-patch --run-id hpc-masbench-t1b-post-storage-audit-20261119 --kind analysis --stage T1-B --purpose independent-post-storage-t1-audit --config research/protocols/masbench_t1b_post_storage_plan.json -- timeout --kill-after=5s 85s prlimit --as=2147483648 -- {python} experiments_ext/masbench_t1_runner_evidence_audit.py live
```
