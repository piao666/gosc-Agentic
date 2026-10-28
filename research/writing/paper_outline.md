# 论文骨架与证据依赖

> 最新证据2026-10-27：[独立校准与审计发现](../reports/information_calibration_results_2026-10-27.md)可写为固定工作点负结果：156任务/N12、主要比较0/5联合支持、时间戳/位置及native阈值边界。另列bits/AoI的7次选包违规与严格审计失败，完整诊断复算一致不写全通过。方法收益/LLM迁移/正式test仍未成立；系统模型、实验协议、负结果与局限可以继续成稿。

> 2026-10-27证据补充：[GP-ID合同与成本验收报告](../reports/information_identifiability_acceptance_2026-10-27.md)可支撑有限观测/typed账本的实现论断，不能填补任务净收益的TODO。下文未运行描述保留10月26日起草含义。

2026-10-26；状态：研究草稿提纲，非投稿稿。暂不确定目标venue、作者、贡献数量或投稿时间。

候选问题标题：**接收端状态何时值得获取：无线多智能体通信中的信息使用、陈旧度与服务成本**。最终题名须随证据和导师意见调整，不预设正向方法论文。

| 章节 | 核心论点/内容 | 证据与当前边界 |
|---|---|---|
| Problem formulation | 新信息价值与获取代价须分开识别 | [问题定义](problem_statement.md)；[HYPOTHESIS]必要性尚未成立 |
| System model | 本地可见状态、原生候选、有限UL/DL/CPU、因果反馈 | [系统模型](system_model.md)；GP-ID未运行验收，CPU为假设 |
| Experimental protocol | 不购摘要强对照、购买但不使用、位置×阈值控制、世界隔离 | [实验协议](experimental_protocol.md)；无正式收益N/预算 |
| Mechanism | age统一缩放与理想动态price关系；新信息只影响估值副本 | [CODE]已有源码/代数；不声称新调价理论或全局任务最优 |
| Reproduction results | GOSC可复现范围和未恢复材料 | [P1清单](../reports/p1_evidence_gaps_2026-10-26.md)、原总审计 |
| Information/cost results | 付费时间戳与位置的增量、实际成本前沿 | TODO: EVIDENCE；既有两版No-Go必须展示 |
| Ablation/boundaries | native vs paid、position vs timestamp、observer开销、失败 | TODO: EVIDENCE；不得把短probe作功效/效果证据 |
| Related work | GOSC、BANDMAS、D02、ToM2C/iCoTASC等的必要差异 | 既有Gap Matrix/笔记；方法确定后继续核验实现与引用 |
| Introduction/Abstract/Conclusion | 根据最终结果凝练贡献和外推边界 | 最后写；没有数据不写显著提升/首次/SOTA |

## 预期图表与来源

- Fig.1 信息可见边界与slot/队列时序：模型图，须标本项目假设；不得借用作者图冒充原创。
- Table.1 对照与信息权限：GP-ID协议；实现事实和未运行状态分列。
- Fig.2 age缩放/显式price的有限数值诊断：旧1536目录仅可按其原范围引用；新闭环目录待执行，不推广普遍逐位等价。
- Fig.3/Table.2 任务结果与真实通信/CPU前沿、CI/N：旧GP-v2可写探索性负结果；新GP-ID TODO: EVIDENCE。
- Table.3 UL/DL typed账本、CPU/observer开销和右截断：新日志待HPC验收，旧DL仍只可写保守识别界。
- Table.4 失败条件与复现缺口：保留作者cache失败、历史差异、预算blocked、任务净收益No-Go。

## 可接受的结果分支

[HYPOTHESIS] 若新信息在公平成本下有可重复增量，再论证轻量预测器是否必要；若native简单规则解释收益，收缩摘要必要性；若任务/成本不支持收益，写可靠边界并与导师审阅后续方向。任何分支都不能由现在的实现完成直接推出足够发表的贡献。
