# 研究进度与证据入口

2026-11-04版本归档：[提交说明](../commit/2026-11-04-01-native-information-and-masbench-preparation.md)汇总G1负诊断、候选/任务与路线B审查、MASBench环境/数据/无模型客户端验收；[20份小型证据](artifacts/native-masbench-20261104/README.md)按原HPC字节与SHA归档。科学No-Go保持、真实模型任务仍未放行；本次只做Git/文件管理。以后每次提交按[固定模板](../commit/TEMPLATE.md)写“提交内容、主要尝试、结果、当前进展、下一步安排”。

2026-11-03 P0–P2准备验收：[新报告](reports/masbench_reasoning_preparation_acceptance_2026-11-03.md)、[上下文/预算提案](benchmarks/masbench_reasoning_context_resource_budget_v1.md)。修正空支持键后仍38组/最大242；4题/4分量开发预留248行、余52，模型尚未曝光。最终147合同＋独立httpx MockTransport5项通过，无真实HTTP/模型/任务。精确tokenizer/effective context和未来独立池充分性Pending，6000s/256MiB只是提案；真实诊断仍须另批，G1/GP-ID科学No-Go保持。

2026-11-03路线B工程验收：[数据审计与无模型适配验收](reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)、[有限接口合同](benchmarks/masbench_reasoning_adapter_contract_v1.md)。HPC最终67合成合同通过，73冻结源码不变；数据300条/200唯一问题/100重复组，2条support一致性异常，保守分组最大242条、划分未冻结。没有模型调用或真实任务；工程支持域Go，数据/上下文/预算仍Pending，G1/GP-ID科学No-Go保持，完成本轮后停止。

2026-11-02环境维护验收：[Reasoning独立环境](benchmarks/masbench_reasoning_environment_v1.md)、[完整维护报告与失败记录](logs/masbench-environment-repair-2026-11-02/report.md)。三个模型的本项目历史digest/全部blob SHA通过；独立客户端依赖、SDK GET清单及metadata通过。用户逐项授权清理hai-study、两个指定Laya目录及完整安装包后解除配额阻断。仅基础环境Go，没有模型加载/生成、任务/训练或Git提交；数据、能力及无线合同仍Pending，G1/GP-ID科学No-Go不变。

2026-11-02 13:46路线B环境复核：[HPC连接恢复后的只读记录](logs/masbench-reasoning-hpc-2026-11-02/task_log.md)确认身份/HEAD及2CPU/24GiB/L40；Ollama服务在线但模型清单为空，旧三个标准manifest未见，缺openai/httpx等依赖。连接阻断解除，当前运行仍No-Go/Blocked；模型能力、数据及合同仍Pending。没有启动推理/测试/安装/下载/实验；旧超时与科学No-Go保留。

2026-11-02路线B静态交付复核：[三份Reasoning规格与审查](benchmarks/masbench_reasoning_adapter_spec_v1.md)保持设计稿；[当前只读核查](logs/masbench-reasoning-static-2026-11-02/task_log.md)因HPC SSH超时而Pending。下文10月30日模型/包清单为历史快照，不作今日实况。方向Conditional Go，运行No-Go/Blocked；未实施、未运行测试/任务/模型、未提交Git，G1/GP-ID科学No-Go保持。

2026-10-30路线B第一阶段：[MASBench Reasoning静态适配规格](benchmarks/masbench_reasoning_adapter_spec_v1.md)、[科研可行性审查](benchmarks/masbench_reasoning_feasibility_review.md)、[关卡矩阵](benchmarks/masbench_reasoning_gate_matrix.md)。已固定第三方commit并追踪私有context/共享板/首答案/None分母；只读HPC发现服务在线但模型列表为空、旧三manifest未见且依赖缺失，数据正文核验仍Pending。方向Conditional Go，当前运行Blocked/No-Go；没有集成/任务/测试/训练/付费调用/安装/提交。G1与GP-ID No-Go保持，交付后等待研究决策。

2026-10-30方向静态审查：[候选表达与调度耦合](reports/candidate_expression_review_2026-10-30.md)、[Planner Search适配性](reports/planner_search_task_fit_review_2026-10-30.md)、[路线A/B与Go/No-Go建议](reports/research_route_decision_2026-10-30.md)。确认FIFO/每率最长前缀限制表达，未证明是G1失败的因果主因；原G1 No-Go保持。若保留LLM多Agent论文主问题，优先建议路线B单一公开benchmark的静态适配规格，A保留备选与系统边界，不自动实施。仅源码/已有记录/公开原文只读核查，无新计算、算法/候选/任务修改、同步或Git提交推送；本轮完成后等待研究决策。

2026-10-30最小机制诊断：[Shadow结果与No-Go报告](reports/native_information_shadow_results_2026-10-30.md)、[执行索引](protocols/native_information_shadow_execution_2026-10-30.json)。用户明确授权后两已曝光world×24slots、82快照在HPC5.681158s完成，独立审计passed，全部回传；69个多前缀快照有非比例估值变化，但492次快照×价格比较的EVID前缀切换为0，仅16次速率/9次开关差异，G1完整选包均被声明有限控制集合复现。**本版G1内容路线No-Go并停止，不训练复杂模型挽救。** 效果N0，不证明任意调价等价或信息普遍无价值；候选生成/任务适配性待另行审阅。下文“未授权/未运行”保留前序阶段含义。

2026-10-30合同验收：[Native-Information HPC工程检查](reports/native_information_contract_acceptance_2026-10-30.md)最终519完整测试通过（34新case），原件全部回传。支持域工程合同Go；无生产算法改动，最小Shadow诊断/收益/训练/正式test仍未放行，原科学No-Go保持。

2026-10-30实施入口：[Native-Information最小Shadow代码交付](reports/native_information_implementation_2026-10-30.md)。局部G0/G1、真实入口/自有证据账本、被动宿主、同状态重选、独立标量/预算审计、合同定义及授权门控已写；**全部新增项目测试/prepare/Shadow未运行，工程验收Pending**。原No-Go保持，未获得诊断运行授权，两份已验收静态文档原样保留。

2026-10-30用户验收：[Native-Information静态规格](protocols/native_information_value_spec_v1.md)与[可行性审查](reports/native_information_feasibility_review_2026-10-30.md)通过，正文原样保留。[验收记录](logs/native-information-review-2026-10-30/user_acceptance.md)明确当前阶段：**静态研究设计完成 → 等待最小机制诊断 → 再决定第一篇论文是否继续沿G1路线推进**。诊断只问固定候选下是否存在无法由简单调价解释的内容级决策差异；未批准运行，原No-Go、算法/实验/训练/正式测试边界保持。

2026-10-29研究决策：[付费位置为何未建立净收益，以及现有信息下的调度候选](reports/research_decision_existing_information_2026-10-29.md)。基于014b85d静态审查；建议优先审阅无需新增同步的最小内容价值代理，效果待验证。无新计算，原科学No-Go与BF工程Go分别保留。

2026-10-28归档入口：[最近几轮结果汇总](reports/recent_rounds_summary_2026-10-28.md)、[8份HPC汇总JSON白名单](artifacts/gp-id-bf-20261027/README.md)、[提交说明](../commit/2026-10-28-01-information-identifiability-and-budget-selector.md)。工程Go与科学No-Go分开，保留原失败/旧状态和P1缺口；本次只做版本归档，无新科研运行。

最新工程验收（2026-10-27）：[BF-selector-v1实施/验收报告](reports/budget_selector_acceptance_2026-10-27.md)与[执行索引](protocols/budget_selector_execution_2026-10-27.json)。485完整HPC测试通过；7旧违规/192可行目录、52短fixture及7派生修复到wire合同、独立原始行/预算/组/成员/CRC/typed账本核验通过并回传。旧源/默认与失败保持；新显式入口GP-ID-BF-v1，收益N0。工程Go不撤销原科学No-Go，不自动扩N、正式test或训练。下方Pending属前序快照。

最新静态审阅（2026-10-27）：[selector预算可行性修订结论](reports/selector_budget_revision_review_2026-10-27.md)与[细化规格v1](protocols/selector_budget_feasibility_spec_v1_2026-10-27.md)。方向有条件通过；须补有界失败、每组至多一项、旧可行调用兼容、版本化重放与CPU/wall记录。代码/HPC合同未实现未运行，没有新样本；原工程阻断和科学No-Go保持。

最新校准（2026-10-27）：[156任务结果与审计发现](reports/information_calibration_results_2026-10-27.md)、[执行索引](protocols/information_calibration_execution_2026-10-27.json)。批准2400s/384MiB后13方案×12新world在777.09s完成；全量原件87,333,208bytes回传。5组主要比较均无联合支持，统计No-Go；paid-pose对periodic慢33.83slots，通信/CPU比2.142/3.664。严格审计发现bits6/AoI1次真实选包超预算，诊断核完156记录/账本/重选/统计仍保持blocked_selection_budget；不冒称全审计通过。事前379测试及wrapper9通过；结果后390通过/1测试fixture失败，补字段后3针对合同通过。原失败保留，在线策略未改，正式test/扩N/训练No-Go。下一步先审阅selector预算可行性及研究主张收缩；下方N0/待审批是前序快照。

最新验收（2026-10-27）：[GP-ID-v1 HPC验收报告](reports/information_identifiability_acceptance_2026-10-27.md)与[执行状态](protocols/information_identifiability_execution_2026-10-27.json)。完整343测试通过；13方案×2成本world×观察开关共52个24slot fixture、独立typed账本/决策审计和成本汇总完成，全部回传。1825同目录数值比较0差异，非通用等价证明；任务收益N0、付费信息净收益未建立。首轮合同失败与7项红回归保留。下一独立校准仅[设计/预算审阅候选](protocols/information_identifiability_calibration_review_2026-10-27.md)，原No-Go/封存test/训练边界不变；以下10月26日未运行段落保留历史含义。

最新实现（2026-10-26）：[信息价值/获取成本识别报告](reports/information_identifiability_implementation_2026-10-26.md)与[GP-ID-v1协议](protocols/information_identifiability_v1.md)。独立对照/前瞻观测、合同测试和有界probe/独立审计入口已写；HPC SSH超时，用户要求先完成实现，**全部新增合同/prepare/probe/审计未运行、无新任务收益证据**。四份[写作骨架](writing/paper_outline.md)及[P1缺口清单](reports/p1_evidence_gaps_2026-10-26.md)已建立；原No-Go/封存test/训练边界不变。下面日期段落均保留历史含义。

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
