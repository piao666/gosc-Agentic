# Planner Search任务环境的科研适配性审查

日期：2026-10-30。基线为`014b85d`及冻结本地研究扩展。**判断：Planner Search适合无线服务、结构化证据融合和低成本调度的受控研究；不足以单独支撑“开放式LLM多Agent接收端推理价值”的主结论。** 它具有真实多步物理反馈，不能贬称为无任务或无通信价值；本版G1的No-Go也不证明该环境不存在其他有效机制。

本轮只读源码/既有报告，并核验公开原始论文与官方仓库README。未安装benchmark、调用模型、运行测试/仿真/统计或修改任务。跨环境建议均为[HYPOTHESIS]，不是已经可运行的方案。

## 1. 当前任务实际测量了什么

[CODE] `gosc/environment.py:8–46`产生隐藏静态victim格点和带漏检/虚警的观测；`belief.py:25–43`做已知传感模型下的逐cell LLR融合。`agent.py:28–54`按footprint概率质量、距离折扣与队友repulsion选目标，配合hysteresis及一步网格移动。`simulator.py:214–258`每slot重复感知—确认—规划，消息经通信后影响后续belief/意图与轨迹。

| 所需研究特性 | Planner Search现状 | 可以支持的结论边界 |
|---|---|---|
| 分散观察与私有信息 | 有；当前native还保留各接收者本地Lc及实际收到消息 | 可研究信息陈旧/共享费用；不是完全同知识的伪多Agent |
| 多步任务反馈 | 有；移动改变未来感知、通信路径损耗和任务发现时间 | 可测整段任务时间；不能等同于显式多步推理/子任务依赖链 |
| 信息到行动的路径 | 概率场→空间启发式→target→move | 可测规划代理相关性；缺少开放推理、工具调用、论证整合 |
| 不同内容的作用 | 正负证据、位置及intent都可能有用 | 不同内容重要性并非不存在，但目前选择粒度被FIFO限制 |
| 接收者异质性 | 位置、私有观测、已收信息和优先级不同；Planner规则基本同构 | 不应将同构空间差异直接宣传为异构LLM reasoning state |
| 跨agent必需的信息互补 | 没有固定角色/独占子任务前置链；多个agent可感知同一格点 | 协作可提高效率，但并非每次成功都必须联合多人的互补证据 |
| 推理语义 | 消息是Obs/CONF/INTENT，belief更新为固定算法 | 不能检验自由文本证据依赖、请求—回答、上下文误解等核心LLM现象 |
| 任务评价 | 定位完成slots、完成标志、false declarations、通信账本 | 客观可复现；单一完成时间难分离发现、上报、peer行为与服务费用 |

[CODE] 当前native完成判据尤其需要区分：`native_paid_adapter.py:57–63`在edge融合证据/接收CONF后可直接declare；`:136–139`按edge已定位victim数结束。一次消息即使尚未改善任何peer行动，也可能改变定位完成时刻。反过来，peer行动改变未必马上影响edge定位。因此“消息改善完成时间”与“消息改善接收端推理”不是同一个估计目标。未来若要解释peer决策作用，需单独有动作/信息使用证据；本轮没有这类新反事实。

[CODE] Source filter先依赖本地belief变化筛掉记录；G0/G1只评估保留队列。若某条对概率场影响小却具有任务前置作用，后续估值器无法将其重新选回。这是接口约束；当前Search是否存在足够多此类记录未被识别，不能据此宣称已经找到失败原因。

## 2. 当前“LLM”范围不能被扩大解释

[CODE] `gosc/llm_agent.py:115–128,142–182`先生成至多`llm_candidates`个空间目标，再让模型返回标签；`:93–99`prompt提供mass/distance/nearest teammate等特征。原默认候选数5。它没有让LLM生成消息候选、检验自然语言证据或持续维护开放式多Agent对话。此限制并不否定原LLM proof of concept，但不支持把Planner负/正结果外推为LLM消息推理结果。

[CODE] 更严格地说，当前`native_task_wire.py:71–75`直接拒绝`cfg.llm_agents`、非search、oracle及共享上行等设置。故本轮审查的冻结Native-Information路径**没有运行LLM**；不能只把配置改为mixed就声称完成路线B或沿用全部合同。

[PAPER] GOSC原文自己将LLM部分定位为受限决策proof of concept，并在§V-H限定单一模拟器/两种grid任务的外推范围；复杂ToM未有一致优势见§V-D。本文对FIFO接口与任务适配性的具体批评是我们对源码的审查，不冒充作者自述。参见[GOSC原文](https://arxiv.org/html/2609.39477#S5.SS8)、[原纸码映射](../logs/GOSC_paper_code_map.md)。

## 3. 原有负结果如何影响环境判断

[RUN，沿用旧证据] [GP-ID校准](information_calibration_results_2026-10-27.md)13方案×12world未获得五组主要比较的联合支持；paid-pose对强periodic平均慢33.83slots，通信/逻辑CPU比2.142032/3.664153，原bits/AoI还存在预算违规，整轮保持blocked。不能把它写成所有辅助对照均通过公平合同的无效性定理。

[RUN，沿用旧证据] [BF工程验收](budget_selector_acceptance_2026-10-27.md)与最终519项Native合同保证已检查的实现/预算边界，不保证任务价值空间。之后[最小Shadow](native_information_shadow_results_2026-10-30.md)82快照/492比较未出现G0/G1 EVID前缀切换；替代包没有进入任务轨迹，效果N0。

[HYPOTHESIS] 这些证据共同削弱了“在原固定前缀Planner任务上继续精化G1即可形成论文”的可行性。它们没有比较开放benchmark、没有操纵候选集、没有估计消息到peer行动的真实因果效应，故不能据此认定“Search一定太简单”“LLM换上去就会成功”或“数据量不足是唯一问题”。

## 4. 公开LLM Multi-Agent benchmark的针对性筛选

以下是**有限、目的明确的初筛**，不是全面综述或源码可复现验收。出版状态按核验来源区分。详细阅读范围、作者元数据及访问失败见[文献证据记录](../logs/candidate-task-review-2026-10-30/literature_evidence.md)。所有候选均尚未在本项目运行，不引用其论文成绩充作我们的结果。

### 4.1 MASBench：优先进入静态适配审查的候选

[PAPER] Chu等，*MASBench: Benchmarking LLM-based Multi-Agent Collaboration under Partial Observability*，arXiv:2610.04672v1（2026预印本，本轮未核验正式会议/期刊录用）。§4、附录D/E给出分散证据Reasoning、私有日历Scheduling与局部观察Game；这些结构比Search更直接涉及信息互补/协商。[论文](https://arxiv.org/html/2610.04672#S4)

[CODE，官方README] 已公开数据与OpenAI-compatible端点说明；同时明确Reasoning的`comm_tokens`实际按规范化words计数，且未识别答案样本不计入其legacy mean F1。该口径对丢包/超时研究尤其危险。[官方README](https://github.com/BUPT-GAMMA/MASBench/blob/main/README.md)

[HYPOTHESIS] 建议优先静态审查Reasoning的双agent私有证据边界与所有失败样本分母，再决定是否适配；不能使用“缺答案删除”制造通信收益。若另立统一失败计0的评价，应版本化并同时保留原指标，不冒称原论文表格精确复现。Game已有routing/protocol机制，更接近网络动态，但接入面更广；Scheduling必须检查共享对话是否绕过新无线链路。API兼容声明不等于当前Ollama模型/上下文/JSON约束已通过。

### 4.2 Collab-Overcooked：正式发表、长依赖链强，但成本和侧信道风险高

[PAPER] Sun等，EMNLP2025，pp4922–4951，DOI10.18653/v1/2025.emnlp-main.249。§4.1（PDF pp4–5）说明资源隔离、任务知识不对称、分步协作；**同时每步广播全局环境状态**。任务依赖更强不意味着所有协作信息只能经语言消息传播。Table2中Qwen2.5-7B在较难任务接近性能下限，不能假定本项目小模型可用。[正式论文与元数据](https://aclanthology.org/2025.emnlp-main.249/)、[PDF](https://aclanthology.org/2025.emnlp-main.249.pdf)

[CODE，官方README] 推荐Python3.8/额外游戏依赖，支持本地模型部署说明，未在本项目核验；与当前Python3.11环境不能假设无缝兼容。[仓库](https://github.com/YusaeMeow/Collab-Overcooked/blob/main/README.md)

[HYPOTHESIS] 作为后续长依赖验证候选，优点是有正式发表来源与过程指标；当前不建议第一步全面迁移。必须先审查环境广播、动作可见性和错误反馈的旁路信息，及Full-communication小模型能力；保留公开环境语义，不能偷偷遮蔽global state制造新任务再称原benchmark。主指标优先任务成功/进展，过程TES类指标不能单独证明消息真实价值。

### 4.3 CoLLAB：结构化协调的备选，不提前声称通过私有信息边界

[CODE/官方介绍] Mahmud、Bagdasarian、Zilberstein的CoLLAB提供DCOP问题层、通信层、agent层分离与symbolic参照，包含meeting scheduling等问题。[项目页](https://agents-collab.github.io/)、[官方README](https://github.com/Saad-Mahmud/CoLLAB_SEA/blob/main/README.md)

论文OpenReview正文访问受验证页阻断，搜索预览有SEA@NeurIPS2025 workshop抬头；**不将其写作NeurIPS主会成果或全文已核验**。私有因子、全局utility和边界信息是否进入agent prompt，尚需逐文件检查。优势是客观symbolic评价和较清晰分层，风险是决策已被结构化求解器覆盖、LLM必要性和消息依赖不足。当前列为备选，不承担最终主benchmark的研究保证。

## 5. 路线B必须解决的无线适配问题

[HYPOTHESIS/未来规格要求，未实施] “保留GOSC无线模型”应明确保留`Channel.mean_snr/success_prob/decodes`的路径损耗、Rayleigh/outage或FBL、合法CSI与rate/channel-use单位；**不等于原Obs codec、Planner、wire/服务假设可直接用于文本任务**。至少需要另审：

1. **唯一接收边界**：agent只读自己的私有证据、已投递消息和公开规则；ground-truth评价器与全局日历/答案隔离。共享transcript、共享memory、调度器metadata、日志工具和环境广播都要列出，不能在语言消息丢失时从旁路免费补齐。
2. **序列化与完整性**：按实际UTF-8/结构化payload+envelope/CRC计bytes，明确长文本分片/重组、ACK、过期与重传；token不是无线bit。当前100symbols/slot下普通文本可能跨很多slot，不能静默截断文本或提高W挽救模型。
3. **时间与决策规则**：LLM轮次和无线slot的映射、消息未到时等待/继续策略、过期消息是否进context、任务时限如何推进都须预先固定。模型推理/消息生成/评价器成本分开，不用固定.001s冒充LLM实测。
4. **拓扑/信道归属**：非空间QA任务若无位置，明确使用公开固定链路条件或外生位置，不能拿答题成绩决定SNR；上行至edge与下行/点对点接收范围分别建模。若采用共享上行，新增验收而非沿用正交BF合同。
5. **公平性**：相同任务/模型/prompt/生成预算与候选上限，先固定公共消息接口；任务更换、压缩/候选更换、估值更换、调度更换要分轴。原GOSC-ToM不能直接在QA运行，迁移代理须独立命名，并保留rate-aware FIFO/Periodic等可迁移简单基线。
6. **可复现性**：数据按来源问题/同模板/同配方家族分组划分，保留所有失败/超时/格式错误；LLM随机流按逻辑调用键隔离，temperature0并非保证确定。缓存只能重放相同prompt，改变接收历史后必须视为新输入；静态冻结traffic只能支持冻结receiver设置内的结果。

## 6. 适配性判决

- **Go（保留用途）**：GOSC Search作为受控无线/候选接口诊断、系统合同和论文的简洁边界案例。
- **No-Go（主张）**：仅凭当前Planner Search或其5目标LLM替换，支撑开放式多步LLM接收端任务价值的正式论文主结论；本版G1继续训练/扩大样本。
- **Conditional Go（研究设计建议）**：若真实研究目标保持说明书的LLM多Agent方向，优先路线B的**单一公开benchmark适配静态规格**，先审MASBench Reasoning的私有证据和评价分母；它未获实现/运行放行。Collab-Overcooked与CoLLAB作为具有不同失败风险的备选，不同时开三套工程。
- **停止条件**：若可用本地模型在完整通信下仍处于失败下限，或完整/无通信均饱和且无法辨认通信作用，或信息可从旁路获得、简单规则已覆盖全部收益、原始任务语义必须被大改、成本/许可/复现边界无法固定，则该benchmark No-Go。完整通信本身达到高分不构成失败：仍可研究同质量下减少通信的空间。不能挑任务直到G1有优势；失败同样归档，是否更换由新的研究决策决定。

路线A/B的创新、成本、审稿风险与最终建议见[路线决策报告](research_route_decision_2026-10-30.md)。本轮到此为静态审查；未更换环境、算法、候选或value函数。
