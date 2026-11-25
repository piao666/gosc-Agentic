# MASBench T2 窗口需求与部署验收

2026-11-25，Asia/Shanghai。目标是确认冻结四题需要的上下文、对齐实际启动配置和 Driver 的窗口认知，并验证故障清理与回滚。基线 `b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0`，沿用 T1 的 1024 工程支持域。 [预算与验收条件](../protocols/masbench_t2_live_budget_2026-11-25.md)

## 四题的离线窗口需求

[RUN] HPC `n1`、2 CPU，以 `timeout --kill-after=2s 88s {python} experiments_ext/masbench_t2_window_demand.py` 登记并执行词表计数。登记 `hpc-masbench-t2-window-demand-20261125` 在 2.844364 秒完成，退出码 0。执行快照 `20261125T022954Z` 的 1284 个文件均通过 SHA-256 校验。16 个首轮请求均与旧登记哈希一致，沿用固定 Registry、模板及 helper；模型请求及生成均为零。摘要只保存计数、字节数、标签和哈希。 [运行登记](../sync/runs/hpc-masbench-t2-window-demand-20261125/manifest.json) · [逐请求计数](../artifacts/masbench-t2-t3-20261125/t2-window-demand.json) · [回传凭证](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

| 冻结题序号 | base Alice | base Bob | protocol Alice | protocol Bob |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2025 | 2394 | 2158 | 2527 |
| 2 | 2421 | 1797 | 2554 | 1930 |
| 3 | 2903 | 2785 | 3036 | 2918 |
| 4 | 2414 | 1719 | 2547 | 1852 |

表中为完整首轮输入的 Token 数。加每请求的 512 输出预留，峰值 3548，1024 在 16 个首轮请求上均不足。

| 六轮压力场景 | 最大完整输入加 512 输出预留 |
| --- | ---: |
| base Full | 5847 |
| base No-A2A | 4425 |
| protocol Full | 10288 |
| protocol No-A2A | 4558 |

[RUN] 96 条压力请求通过实际应用状态和通信路径，用每轮 505-token 的虚构应答推动历史增长。协议 Full 条件重附累计知识板，峰值出现在题 3 第 6 轮。最大应用层单请求 37,791 字节，低于 65,536 字节上限。**16384 是覆盖本次 10288 峰值的最小测试档位。** 随后的真实生成内容未知，仍须逐请求精确检查，压力测量不能充当任意输出的安全上界。D1 与现有任务注册表保持原记录。

## 16384 首轮现场与零派发回滚

[RUN] 禁网登记 `hpc-masbench-t2-contract-20261125` 耗时 7.679930 秒，覆盖已有 53 项合同及候选配置。现场 `hpc-masbench-t2-live-20261125` 使用快照 `20261125T023746Z`。从同一持久配置启动和重启两次 16384，首例仅渲染期间遇到 Driver RSS 保护并停止。现场 11.652744 秒、exit 1，模型生成及预算预留均为零。卸载返回确认且驻留列表为空，预绑定 runner 证据缺失，Driver 保留恢复锁，自动回滚也保持栅栏。独立前缀核查 `hpc-masbench-t2-audit-20261125` 为 0.152596 秒、exit 0，验收仍判定 false。

[CODE] 旧监视实现分别对 Driver 根进程和服务根进程汇总。此轮由 Driver 的外层启动器创建 Ollama，服务子树落在两个汇总范围内，采样的 Driver RSS 达 2,392,375,296 bytes。修复为使用同一 `/proc` 快照，将固定服务子树从 Driver 合计中剔除，保留独立的 2 GiB 和 16 GiB 门槛。禁网回归覆盖同一父进程和独立服务两种进程树结构。 [资源监视源码](../../experiments_ext/masbench_t1b_live.py)

[RUN] 根据独立审计与两个原始哈希链，当次无请求结算记录、无实际生成、无预留。将 207 字节旧锁、原候选配置及六份关联记录复制至 HDD，逐份核验 SHA 后核查在场服务、空驻留和显存。停止失败的候选实例，恢复已验证的 1024 基线服务和空闲资源，再清空原恢复锁。旧运行和失败判定原存。 [回滚及归档凭证](../logs/masbench-t2-2026-11-25/zero_dispatch_rollback.json) · [修正后复验预算](../protocols/masbench_t2_live_v2_budget_2026-11-25.md)

## 60 秒现场截止与恢复

[RUN] 修正后的禁网合同通过，现场 `hpc-masbench-t2-live-v2-20261125` 实际重启 16384 配置，首例完整渲染和绑定通过。随后真正发送 **9973 输入／32 输出预留** 的请求。生成阶段触发 60 秒截止，用量保守记作 `null`。Driver 向自有 worker 发出停止信号并核验 runner `34972` 退出，卸载及空驻留确认后结束。运行 71.604478 秒、退出码 1，服务自动恢复 1024，显存 0 MiB，恢复锁为空。资源采样的峰值为 Driver RSS 63,352,832 bytes、服务 RSS 5,172,088,832 bytes、GPU 6,767,509,504 bytes。 [失败摘要](../artifacts/masbench-t2-t3-20261125/t2-timeout-summary.json) · [独立审计](../artifacts/masbench-t2-t3-20261125/t2-timeout-audit.json)

[RUN] 服务日志在长输入渲染返回 HTTP 200 后记录 `/v1/chat/completions` 长约 59.716 秒并在请求取消后报 500。此处冷加载已通过，数据只证明生成请求超过截止，无法拆分实际预填充与解码成本。根据旧请求保留预留，从原累计四次额度扣除一次。后续补验只用剩余三次，正常用例扩展独立生成期限至 180 秒，显式核查控制器中断与恢复。 [补验范围](../protocols/masbench_t2_live_v3_budget_2026-11-25.md)

## 补验、独立审计与最终配置

[RUN] 源码快照 `20261125T025034Z`，1299 文件、SHA 差异 0。`hpc-masbench-t2-contract-v3-20261125` 7.549642 秒、exit 0。禁网验证既有 53 项合同、16384 授权、错误窗口拒绝、持久启动设置、进程内存分账和生成期限。正式补验 `hpc-masbench-t2-live-v3-20261125` 运行 109.667734 秒、exit 0。独立审计 `hpc-masbench-t2-audit-v3-20261125` 0.221966 秒、exit 0，核对 46 份现场产物，判定 `acceptance_passed=true`。实际命令、配置哈希和环境见各自 manifest。 [现场登记](../sync/runs/hpc-masbench-t2-live-v3-20261125/manifest.json) · [禁网日志](../sync/runs/hpc-masbench-t2-contract-v3-20261125/stderr.log) · [独立审计](../artifacts/masbench-t2-t3-20261125/t2-final-audit.json)

| 合成用例 | 已预留输入／输出 | 实际用量与结果 |
| --- | ---: | --- |
| 正常长输入 | 9973／32 | 完整渲染、运行时窗口 16384 和 usage 对账。发送到记录响应约 **85.21 秒**，返回 `OK`，实际 9973／2，runner 身份一致。 |
| 控制器中断 | 9679／512 | 已发请求和实际停止信号可核对。用量 `null`，完整预留保留。卸载及 runner 退出后恢复派发许可。 |
| 恢复后生成 | 29／32 | 实际恢复派发，返回 `OK`，实际 29／2。最终卸载核验新 runner 退出。 |

[RUN] 超窗负控制在任何 HTTP 前拒绝。三轮累计实际派发 **4 次**，预留 **29,654 输入／608 输出**，其中两笔实际用量未知的合计预留 **19,652 输入／544 输出**。原 60 秒失败作为独立证据核对请求超时、显式卸载、runner `34972` 退出及自动回滚。补验的 206 次资源采样中，Driver RSS 峰值 95,395,840 bytes，服务树 RSS 4,256,157,696 bytes，GPU 6,767,509,504 bytes。当前维持单并发。 [预算与资源摘要](../artifacts/masbench-t2-t3-20261125/t2-final-summary.json) · [信号、卸载起止与恢复许可](../artifacts/masbench-t2-t3-20261125/t2-final-control.jsonl)

[RUN] 从同一持久配置两次实际启动 16384，运行时以继任服务的模型驻留 API 核验有效窗口。补验结束停止候选拥有的服务，恢复 1024，独立审计匹配四个不同服务 PID／启动标识及原 0.11.11 二进制。最终服务 PID `36124`，无 runner，显存 0 MiB、恢复锁为空。双端定向回执记录首两轮 1089 个文件及最后三条登记的 574 个文件。 [服务切换链](../artifacts/masbench-t2-t3-20261125/t2-service-transitions.jsonl) · [首两轮回传](../artifacts/masbench-t2-t3-20261125/receipt_index.json) · [最终回传](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

**T2 通过所测工程支持域。** 推荐 T3 预算以 16384 重新核定，历史 60 秒单操作设置不能支持本轮实测的长输入。所测 9973 输入只要求短输出，仍须单列实际任务长输出、96 次任务请求的阶段预算及日志体积。原生即时取消仍未验证。真实四题曝光为零，当前活动部署是已回滚的 1024，T3 仍有独立的预算与开跑关卡。
