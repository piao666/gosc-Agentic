# Research Task Report — T3-R-v2-T 一次性真实开发诊断

2026-11-26，Asia/Shanghai。**工程闭环通过，科学继续门未通过。** 用户批准的唯一运行 `hpc-t3rv2i-task-live-final-20261126` 已用完 48 次真实生成。四个已曝光家族的 8 个 episode 均完成，模型在冻结终答合同下未产生有效答案。此次结果是开发诊断，继续门按事前阈值判定。[审批与运行证据索引](../logs/masbench-t3rv2t-final-admission-2026-11-26/execution_evidence_index.json)

## 执行与证据

- **研究问题**。允许对等交换的 Full 条件，能否相较 No-A2A 在原四家族达到事前定义的终答改善并有可追溯的 L1/L2？实验单位是家族，四对仅作描述性开发诊断。[冻结申请](../protocols/masbench_t3rv2t_final_execution_request_2026-11-26.md)
- **执行身份**。[RUN] HPC `n1`，Git 基线 `4a7ab227a3051013ce808f6e0407541bdaaa8f7c`。执行快照 `20261126T093309Z`，源码 manifest SHA-256 `e11d78e751fe937bcc7d44c8b493477dc562de06e6fc659863ea3b0e1919ba7f`。审批仅切换 `approved`，实际授权 SHA-256 `18fcf092ce99b6ddd5e41d27490a5c1882738a8d68a372edf546c46979c413a2`。[激活记录](../logs/masbench-t3rv2t-final-admission-2026-11-26/authorization_activation.json)
- **实际命令**。[RUN] 用 `scripts/sync_hpc.py` 排除既有三项未跟踪资料后核 SHA。执行 `python -u -m experiments_ext.masbench_t3rv2t_closeout launch`，在同一调用内完成任务、独立审计、流式回传和双端凭证。另将 [离线评分脚本](../logs/masbench-t3rv2t-final-admission-2026-11-26/offline_score.py) 逐字节同步至 HPC `.local`，经 `masbench_t3rv2i_register run` 登记 `hpc-t3rv2i-task-live-final-20261126-offline-score`，用既有 `score_episode` 与 `paired_summary` 汇总。该步骤在运行闭环后进行，生成请求 0。闭环后评分登记耗时 0.171 s，9 份文件单独 SHA 回传。
- **工程验收与资源**。[RUN] 48 次生成用量全部可核，8 次卸载与 1024 基线回滚通过。真实执行 626.70 s，独立审计登记 0.55 s。整体双端确认 649.00 s，低于 18360 s。616 个文件共 12795849 B，含 HDD 原件 10767382 B。HTTP 282 次，分类为生成 48、render 48、get 152、cleanup_get 16、unload 8、lifecycle_get 10。词表计数 56 次。活动监测最大采样间隔 0.293 s，驱动树 123908096 B、服务树 5401538560 B、GPU 6767509504 B 峰值在既定观察上限内。[回传凭证](../artifacts/masbench-t3rv2t-final-20261126/live_receipt.json)
- **信息边界**。[RUN] 本轮的参考答案只在诊断闭环后的 HPC 离线评分步骤加载，来自旧审计已锁定的原四家族，逐题核对问题身份。原四家族以外记录及封存 52 条均未读取。已曝光家族无法提供独立确认性证据。未增加随机种子或新样本。

[RUN] 收尾另用 `sha256sum` 只读确认双端凭证一致，SHA-256 为 `487aaa0bfec874b170f6ad8cdb496d8cd7b488d9b533524542c7ddc7ec5b6774`。现场无临时 context profile，服务锁 0 B，GPU 使用 0 MiB。

## 科学判定

| 条件 | 家族 | 生成 | 有效终答 | 格式有效但弃答 | 格式无效 | 平均 EM | 平均 F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full | 4 | 24 | 0/8 | 1/8 | 7/8 | 0 | 0 |
| No-A2A | 4 | 24 | 0/8 | 0/8 | 8/8 | 0 | 0 |

[RUN] 四个家族的配对 ΔF1 各为 0，平均 0，低于 0.10。Full 双方 EM1 家族为 0，低于 2。两条件双方有效且正差的家族为 0，低于 2。Full 有 8 条送达且进入下一请求与终答请求的 L1 链，四家族各 2，终答有效引用候选为 0。数值门已失败，独立 L2 语义复核未开展。保留 15 次格式无效与 1 次合规弃答，均纳入原分母。[离线评分](../artifacts/masbench-t3rv2t-final-20261126/offline_score.json)

[RUN] Full 输入/输出 tokens 66702 / 1776，No-A2A 为 65212 / 1674。按传输账本 Full 为 16464 wire bytes、UL/DL 各 16464 用量单位，No-A2A 为 0。四家族没有观察到终答改善。相同指标的零差值与两个条件都未产生有效终答相伴，不能推断可正确作答任务上的通信效应。未做显著性或一般化推断。

**阶段决定。** 此配置与数据上的继续门为 No-Go。授权已用尽，停止真实生成和阶段推进。原 T3/G1/GP-ID 科学 No-Go 保持，Git 未提交或推送。
