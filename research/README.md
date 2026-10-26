# 研究进度与证据入口

版本归档（2026-10-26）：用户授权一次提交并推送当前研究分支；[提交说明](../commit/2026-10-26-01-causal-service-and-age-review.md)覆盖10月24–25日连续任务和此前未推送祖先。最终身份/推送状态以Git历史和远端引用核验；旧报告“未提交/未推送”保留历史时点。原No-Go和未执行的新协议/正式test/训练边界不变。

最新机制审查（2026-10-25）：[摘要成本与age/动态price](reports/summary_age_mechanism_review_2026-10-25.md)。原252任务/950281事件只读分析，新独立N0；18合同和1536固定合成选择器比较通过。选中pose摘要UL20,516uses，占全通信34.27%；连ACK保守界的直接摘要费占41.90%–66.63%（识别界非CI）。即使固定轨迹账本免去全部摘要UL，39,341.75uses仍超periodic的1.05成本上限。age理想目标等价动态price，native-age免费时间戳对照及逐决策factor/DL类型记录仍缺；[新协议审阅候选](protocols/summary_age_revision_review_2026-10-25.md)未执行，原No-Go保持。

最新（2026-10-25）：[GP-v2独立校准与前沿审计](reports/causal_calibration_audit_2026-10-25.md)。用户批准1200s预算后，21候选×12新world共252任务在447.37s完成；950,281事件和CI/N/前沿/消融独立核对通过。选中pose较periodic平均快8.6667slots，但通信比1.606664、逻辑CPU比2.813743，联合成本支持未达到；规划N21907>200上限，当前协议**No-Go**。正式test/扩N/训练未运行，P1原作者复现缺口不变。下方10月24日预算Pending为前序快照。

最新（2026-10-24）：[GP-v2时钟/有界catchup进展](reports/causal_service_progress_2026-10-24.md)。187主回归及28补充合同通过（含重复，共190不同测试），42短probe和31,280事件独立审计完成；21候选/214world事前冻结。独立校准投影895.50s超480s门槛，**校准未运行、预算Pending**；正式test/训练未启动。完整成本前沿/消融收益待验证，[1200秒校准预算提案](protocols/causal_calibration_budget_proposal_2026-10-24.md)待用户批准。旧GP-v1科学No-Go保留，新服务收益未知。本轮未Git提交/推送。以下为前序快照。

文档更新：2026-10-23（Asia/Shanghai）。最新为[同步成本/估值实际改变率审查](reports/sync_cost_value_review_2026-10-23.md)：最终51合同通过，观察回放24/24精确匹配原校准；两版主要统计一致，辅助观察修正与首轮记录均保留。新独立N=0，正式验证和复杂训练仍No-Go。

本地归档：[2026-10-23 / 01提交说明](../commit/2026-10-23-01-paid-pose-calibration-and-cost-review.md)。当日实现、报告、运行元数据和47份R2/R3白名单副本随该提交保存，未推送GitHub；历史日志/报告中“未提交”保留当时含义。科学关卡未因归档变为通过。

[CODE] 本轮起点为研究分支`research/progress-audit-2026-10-19`的`4ff4147`。10月22日已核验GitHub main停留在`876fc52`；该远端观察本轮未刷新。历史run中的`876fc52`/dirty/source SHA是执行时事实，不倒填为归档commit。

## 当前判断

最新机制审查：[报告](reports/sync_cost_value_review_2026-10-23.md)。paid-pose的3927次实际估值中，96.49%改变投影坐标、79.35%改变超过诊断容差的候选价值、10.54%改变选包。直接摘要账本占相对public-ToM额外资源83.28%；反馈实际2slot但RTO1slot，盲目task历史重播占paid DL77.46%，而DL排队p90仅1slot。摘要不是未接入；服务时钟/重播应先审查，不能据此认定收益修复已成立。原No-Go不撤销，不扩大样本。

最新校准：[报告](reports/periodic_crn_calibration_2026-10-23.md)。从10个简单候选选中periodic k8/eps0；paid-pose相对该对照平均多3.8333slots、成本比1.426004，相对public-ToM多1.5slots、成本比1.357991。小校准的探索性结果，不是普遍无效或显著变差证明。规划N15419超过200world事前上限，未冻结可执行test N/预算、不扩样本救结果；预留test任务0次。[事前协议](protocols/periodic_crn_stage_v1.json)。

以下原生适配/字节服务段落为前序验收快照，其“仍待完成”不覆盖上述最新校准判决。

最新原生适配：[报告](reports/native_adapter_progress_2026-10-23.md)。HPC145测试及3份同世界4slot原始trace已完成；支持范围内原生语义/实际帧长/局部接收短闭环已接通。新GP-v1 wire与stop-and-wait/付费重播不等于作者原wire；强periodic基线/配对CRN/新world与功效预算仍待完成，未运行收益campaign。

最新服务进展：[付费字节服务链](reports/paid_service_progress_2026-10-23.md)。HPC修复后128合同/回归通过；首次零值账本失败保留。此为bytes服务，不是原生task wire/options/投递完整适配；效果world/N/预算仍未冻结。[效果设计关卡](protocols/paid_service_effect_design_v1.md)。

| 阶段 | 已有证据 | 验收边界 |
|---|---|---|
| P0 | 环境、文献清单、GOSC纸码映射 | 全部元数据/出版状态仍部分核验 |
| P1 | HPC85测试；A1 1200任务；主队列23阶段已评估、22正常退出；图表17PDF/18TeX | 原1000–1079校准、作者cache生成链及部分历史差异未解决 |
| P2 | 13旧记录+29选段笔记、Gap Matrix、RQv2、拒稿自查 | 非42篇全部通读、非新颖性证明 |
| P3旧探索（截至10/22） | 1248校准+260验证；免费特权6比较0通过；23摘要测试及96条件回放 | 当时cache未进入任务策略；不替代新付费闭环校准 |
| P3实现合同 | 10月23日：26新增合同+85原测试+18旧codec合同=129通过；47份交付副本哈希审计通过 | 默认配置下的估值专用pose与RTT状态机已实现；paid系统/效果实验仍未完成 |
| P3付费闭环校准（10/23） | 同GP-v1 periodic/CRN，156HPC测试、12world×12候选校准/独立算术审计 | 校准触发No-Go；未运行正式test、未证明付费摘要收益、未完成成本前沿/全部消融 |
| P4/P5 | 有研究报告和协议资产 | 新方法完整实验、正式稿件未完成；复杂训练No-Go |

上述[RUN]事实引用既有报告，本页不是新run或实时调度状态。

## 按问题找证据

- 当前方案：[低成本同步与最简单估值接口协议](protocols/receiver_summary_minimal_protocol_v1.md)；部分接口合同已实现和测试，paid任务主试验仍未冻结/未运行。
- 已归档交付：[R2/R3成果包](artifacts/r2-r3-20261019/README.md)，47份原输出副本随当日本地Git提交保存，尚未推送GitHub。
- 原生复验：[总审计](reports/final_reproduction_audit_2026-10-22.md)、[图表主张矩阵](reports/claim_acceptance_matrix_2026-10-22.md)、[纸码映射](logs/GOSC_paper_code_map.md)。
- 新方向的负结果：[特权诊断](reports/receiver_headroom_pilot_2026-10-22.md)。
- 同步信息/成本：[摘要审计](reports/receiver_summary_information_cost_audit_2026-10-22.md)。96条件复用旧轨迹，不是96独立世界或新方法收益验证。
- 文献：[阅读范围](literature/reading_review_2026-10-22.md)、[Gap Matrix](literature/Research-Gap-Matrix-2026-10-22.md)、[RQv2](ideas/RQ_v2.md)。
- 当前动作：[下一步](sync/plans/next_steps.md)；机器摘要：[project_status.json](sync/project_status.json)。二者是研究判断，不替代run/status与回执。
- 本轮：[任务说明](logs/minimal-interface-2026-10-23/task_brief.md)、[交付/验收报告](reports/minimal_interface_delivery_2026-10-23.md)；前一轮[静态审查](reports/status_and_protocol_review_2026-10-23.md)保留历史含义。

## 读取顺序与保护

先读本页与最新专项报告，再按需回到冻结协议、run manifest/status、outputs和receipts。旧报告中的“未运行”只表示当时状态；当前实施需遵守根AGENTS.md的HPC规则，说明书中的Windows计算示例不再是执行入口。

Git仅保存非忽略文件。原始输出/图件有部分按忽略规则留在本地与HPC；R2/R3白名单副本纳入当日本地提交。源码同步、HPC执行与回传已有登记；本次没有推送、分支合并或新HPC计算。在线manifest或回执不是完整数据副本。
