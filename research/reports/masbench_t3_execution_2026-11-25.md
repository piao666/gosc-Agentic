# MASBench T3 四题真实模型诊断

## 研究问题与已核验边界

[HYPOTHESIS] 在四个已冻结的开发问题中，共享文字消息可能帮助两名代理补齐各自缺失的线索。Full 和 No-A2A 在同题、同模型、同提示族下配对，先看 base，protocol 为辅助。论文相关背景和分组前置工作沿用此前审计。T3 是开发诊断。D1 文章隔离和封存样本的原有边界继续适用。 [候选矩阵](../protocols/masbench_t3_candidate_plan_2026-11-25.json) · [T2 验收](masbench_t2_context_acceptance_2026-11-25.md)

## 代码与禁网验收

[CODE] LiveDriver 绑定冻结的顺序、完整私有视图与首轮请求，复用同源计数、精确窗口、预算、进程身份和卸载证据。任务预留和合成预留独立。用量未知保留为 null，失败不退回已占用额度。运行原文及账本进入个人 HDD，每文件两次核对 SHA-256，SSD 保存登记和摘要。 [Driver](../../extensions/masbench_reasoning/live_driver.py) · [现场入口](../../experiments_ext/masbench_t3_live.py) · [离线审计入口](../../experiments_ext/masbench_t3_audit.py)

[RUN] 首次禁网集成因超时清理提前终止等待错误的应用进程，无法返回部分通信记录，在 2.27 秒后失败。修复在失败后先封闭派发，待应用写回失败记录后再卸载。复验在 49.58 秒内完成 96 次任务及 2 次合成的伪造预留，验证 18 道 runner 退场栅栏、失败后的继续派发、超时保留未知用量和截断保留已知用量。HDD 逐文件读回通过。本地和 HPC 的回传凭证登记了两个 run 的 18 个文件、4,637,287 字节。整个禁网验收没有真实 HTTP 或模型生成。 [首轮失败](../sync/runs/hpc-masbench-t3-integrated-contract-20261125/stderr.log) · [复验](../artifacts/masbench-t2-t3-20261125/t3-integration-contract.json) · [回传凭证](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

## HPC 现场

[RUN] `hpc-masbench-t3-live-20261125` 于北京时间 11:43:12 启动，11:54:55 退出，耗时 702.95 秒。同步 ID `20261125T034132Z`，HEAD `b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0`，1310 个文件、零 SHA 不匹配。用户确认的额度为 16384 窗口、最多 96 次任务和 2 次合成生成、每次预留 512 个输出 tokens、生成不超过 180 秒、整轮 9 小时 40 分、SSD 增量至多 32 MiB、HDD 增量至多 1 GiB。HPC 基线服务从 1024 切换到 16384，现场进程 39248。 [授权与哈希](../protocols/masbench_t3_execution_authorization_2026-11-25.json) · [现场状态](../sync/runs/hpc-masbench-t3-live-20261125/status.json)

登记程序使用既有入口，具体命令如下。

```bash
GIT_INDEX_FILE=/tmp/gosc-t2-b05-index-20261125 .venv/bin/python scripts/hpc_runs.py run \
  --gzip-source-patch --run-id hpc-masbench-t3-live-20261125 --kind analysis --stage T3 \
  --purpose frozen-four-development-families-live-paired-diagnostic --model qwen2.5:7b \
  --cache-mode disabled --config research/protocols/masbench_t3_execution_authorization_2026-11-25.json \
  -- timeout --kill-after=2s 34798s '{python}' experiments_ext/masbench_t3_live.py
```

## 工程结果、成本与归档

- [RUN] 2 次合成预检、16 个任务 episode 全部运行结束。共 51 次生成，其中任务 49 次。预留 131,147 输入和 26,112 输出 tokens。实测总量为 131,147 输入和 5,286 输出 tokens，任务部分为 123,889 输入和 5,282 输出。51 次均可核对实际用量，现场没有超时、缺失用量或截断。禁网复验中的超时未知值仍保留。 [现场账本摘要](../artifacts/masbench-t2-t3-20261125/t3-live-summary.json)
- [RUN] 独立禁网审计用 `experiments_ext/masbench_t3_audit.py` 耗时 0.71 秒，重核 18 次旧 runner 退出与卸载证明。GPU 采样峰值 6.30 GiB，服务进程树 RSS 采样峰值 5.07 GiB，Driver RSS 采样峰值 246.7 MiB。现场后核对服务 PID 42172、窗口 1024、GPU 0 MiB、无 runner、无活动运行和空恢复锁。原生即时取消仍未验证。 [审计结果](../artifacts/masbench-t2-t3-20261125/t3-audit.json)
- [RUN] 现场 SSD 登记目录占用 2,441,216 字节。个人 HDD 原始证据目录为 `/hdd/u202520081000097/gosc-t3-runs/hpc-masbench-t3-live-20261125`，684 个文件的逻辑大小为 16,983,131 字节，含原始请求、响应、计数、传输、资源和恢复记录。登记及独立审计均核对了 SHA-256。现场、审计的 21 个登记文件已回传并校验，总计 4,679,051 字节，真实原文保留在 HPC HDD。北京时间 11:59:41 复测个人 SSD 剩 43,433,984 字节，HDD 剩 517,812,883,456 字节。 [HDD 索引](../artifacts/masbench-t2-t3-20261125/t3-hdd-manifest.json) · [回传凭证](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

## 任务结果与关卡决定

| 提示族 | 条件 | 完全答对 | 平均 F1 | 任务请求 | 后续请求可核验的收信次数 |
| --- | --- | ---: | ---: | ---: | ---: |
| base（主） | Full | 1/4 | 0.3117 | 5 | 1 |
| base（主） | No-A2A | 1/4 | 0.3117 | 5 | 0 |
| protocol（辅助） | Full | 0/4 | 0.2779 | 15 | 11 |
| protocol（辅助） | No-A2A | 0/4 | 0.0000 | 24 | 0 |

[RUN] base 的四对 F1 差值均为 0，三题在首轮回答即结束。余下一题的消息确实进入接收方下一条真实请求，最终 F1 仍相同。Full 仅一个家族完全答对，低于预定的两个。辅助提示族有三对 F1 正差且能追溯到收信，四对均未完全答对。四个 protocol/No-A2A episode 耗尽发言轮数，均无最终答案。这些结果按预定规则计零。

[RUN] Full 在 base 和 protocol 下分别产生 61,560 和 55,680 字节的模拟线传输，合计 234,480 channel uses。两组 No-A2A 均为零。此处统计合同信道的帧开销，任务效果来自这 4 个真实模型开发问题，尚无独立泛化结果、资源匹配的效果比较或统计显著性结论。 [配对与消息哈希](../artifacts/masbench-t2-t3-20261125/t3-audit.json)

**工程验收通过，研究关卡 No-Go。** 主提示族未达到预设的正确率和配对收益条件。T4 未启动，本轮未扩大题量、替换主提示族或改变 D1。若继续探索任务能力，先用已留存的轨迹区分首轮提前提交与多轮整合失败。任何新增模型调用或协议更换需单独审查和授权。
