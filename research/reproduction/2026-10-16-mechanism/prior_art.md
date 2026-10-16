# 定向文献证据卡与机制边界

2026-10-16。本轮对 **4 篇本地 PDF 的相关章节**作定向精读，并核对公式页图像；不等同四篇全文复现实验或新的全网查新。页码统一为 PDF 物理页（1-based）。Obsidian 原件只读，全文提取和页图仅存 `.local/reproduction/2026-10-16-mechanism-v1/papers/`，不提交/上传。元数据空缺时使用首页标题/作者，不将文件名当标题。出版状态未向出版社外部核验；下述 arXiv/ICLR 信息只是本地 PDF 自报，不能扩展成已验证的期刊发表或最新版本。

## D01 / GOSC

**真实标题**：Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams。
作者：Farhad Rezazadeh; Hatim Chergui; Lingjia Liu; Merouane Debbah。
本地：`E:\Obsidian\Papers\99-附件\论文原文\D01-Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams.pdf`。
13页；SHA256 `e99130b27965bc4b6c06ccca8fc2dd9a3fd8b2dd5f6880964b6e0a4003c01923`。
PDF metadata：arXiv2609.39477v1，DOI10.48550/arXiv.2609.39477；不是出版社论文 DOI 核验。

- [PAPER] p3 Eq1 给搜索目标、距离与队友排斥；p5 Eq4 给 Boltzmann receiver policy 下 sender-belief utility 增量；Algorithm1 是 sensing/planning→UL→edge/ACK/broadcast。source filter、value-aware rate/packet scheduling 是共同系统，不能将已有 ToM 或消息/速率选择归为新工作。
- [PAPER] p9 §V-D 已报告914个 sampled decisions 的消息反事实、双向 completion-time 效应及估值排序弱，另有1800 paired missions 的 joint valuation 对照。因此“精确 ToM 不一定改善任务”是作者已有结论。
- [CODE] 本地实现还含 planner hysteresis、sender partial/private evidence、CONF 固定优先价值。作者 diagnostic `gt_utility` 是立即重规划后的真实幸存者覆盖效用；`changed` 来自该效用非零，未直接保存 target-change count。后者是本轮核查发现的**证据语义边界**，不能据此认定作者另有未公开计数一定不存在。
- [RUN] 本轮重分析 saved rows，不是新仿真；914条来自20个 mission，全部 `n_teammate_changes=null`。统计详情见 saved_diagnostic_audit.json。原作者关于低估值保真度的定性结论没有被本轮推翻。
- 未做：重新生成原反事实样本、重跑1800 joint任务、验证 live LLM。本地源码/结果能追溯不等同所有原论文数值已严格重现。

**五句记忆**：它以任务价值协同选择语义消息和速率。ToM 根据共享状态预测队友 softmax 行动，并以 sender 信念评价。实际执行器带目标迟滞，且交付在规划后生效。作者已经检查精确估值和消息反事实的局限。本研究只能在已知局限之上提出可归因、可计费的新检验。

## D08 / ToM2C

**真实标题**：ToM2C: Target-oriented Multi-agent Communication and Cooperation with Theory of Mind。
作者：首页 Yuanfei Wang; Fangwei Zhong; Jing Xu; Yizhou Wang（PDF metadata Title/Author 为空）。
本地：`E:\Obsidian\Papers\99-附件\论文原文\D08.pdf`。
17页；SHA256 `baee633fcc46d4d61749d3fad62d3f86850aee9fe2d02690a0cc61e8ddfebfc8`。
页眉声明 ICLR2022；本轮没有外部核验会议记录/DOI。

- [PAPER] p5 §3.2 Eq1–3：学习 observation estimation 和 goal inference，以训练时的观察/目标监督 ToM；不是 GOSC 的手工共享 belief 代理。
- [PAPER] p6 §3.3 Eq6：通过移除 receiver 的接收消息，比较 subgoal 分布的 KL，阈值生成 cut/retain pseudo label，训练 communication reduction。**动作敏感的消息消融已有先例**，不能声称首次通过目标变化判断消息有用。
- [PAPER] p6 §3.4：先接收信息再生成目标；CTDE 的 centralized critic 与 decentralized execution 分离。该时序不同于 GOSC 的本时隙先规划后融合，不能直接移植标签含义。
- [HYPOTHESIS] goal-distribution KL 不等于任务 completion-time effect；这是我们比较指标的边界，不冒称作者明确承认的 limitation。若做对照，要考虑训练/推理/消息状态获取成本和任务适配。
- 实验具体 benchmark 数值、全部成本/强 baseline、独立源码复现：本轮未核验；不引用未经核验的提升百分比。

**五句记忆**：ToM2C 通过推断队友观察和目标帮助通信。它已有移除消息后的 receiver 决策敏感性监督。标签是子目标分布变化而非长期任务反事实收益。训练时特权监督与执行时局部信息要区分。与 GOSC 比较必须先对齐时序和可用状态。

## D06 / PragComm

**真实标题**：Pragmatic Communication in Multi-Agent Collaborative Perception。
作者：首页 Yue Hu; Xianghe Pang; Xiaoqi Qin; Yonina C. Eldar; Siheng Chen; Ping Zhang; Wenjun Zhang（metadata Title/Author 为空）。
本地：`E:\Obsidian\Papers\99-附件\论文原文\D06-Pragmatic Communication in Multi-Agent Collaborative Perception（PragComm）.pdf`。
18页；SHA256 `ce5490ab0ab6a193dbab83726584b2db9c7a605a09f4e832caf53d8b4b630cb2`。
本轮未核验出版社/DOI。

- [PAPER] p5 Eq3/4 组织 pragmatic message selection/representation；p9 Eq12：sender 可用空间/时间信息与 receiver 上一轮信息 mask 的补集相乘，得到 receiver-demand-aware 稀疏 feature map。**接收方已有什么/还缺什么**不是新研究概念。
- [PAPER] p9–10 §4.2.3：共享 codebook 将特征表示为 code indices；p10 Eq15 只有存在互补信息才建立合作边，Eq16融合当前/历史信息。这里确实有特征重构，不能把 GOSC 结构化日志编码同称新 DeepSC codec。
- [HYPOTHESIS] receiver mask 的可得性/陈旧性是将该思路用于本研究时需审计的成本，不据此断言原作者遗漏反馈开销。本轮未完整核算其反馈/headers、端到端 latency 或基线数值。
- 任务是协作感知，区别于 GOSC search 和 LLM 多 agent 推理；未完成任务适配前不能当成可直接运行的同预算 baseline。

**五句记忆**：PragComm 以支持者供给和协作者需求决定通信。上一轮信息的补集明确表示 receiver 需求。它联合稀疏选择与 codebook 表示来支持感知。其需求机制值得借鉴，但状态成本仍需按我们的系统计量。它不能直接证明本研究的低成本 receiver runtime 估值新颖或有效。

## A02 / BANDMAS（本地文件编号2）

**真实标题**：BANDMAS: Causality-Inspired Semantic Packet Scheduling for Bandwidth-Efficient Multi-Agent Collaboration。
作者：Jiangwen Dong; Wanyu Lin。
本地：`E:\Obsidian\Papers\99-附件\论文原文\2-Causality-Inspired Semantic Packet Scheduling for Bandwidth-Efficient Multi-Agent Collaboration.pdf`。
11页；SHA256 `f21bc0cb4d1521f33adf6ab38b56f36f4ce2d8009a6e733cf4ae130d79a6ead3`。
PDF metadata：arXiv2608.00458v1，DOI10.48550/arXiv.2608.00458；发表状态未外部核验。

- [PAPER] p3 Eq6：RCE 为 sufficiency（single packet vs empty）和 necessity（full vs full-minus-packet）的平均，固定 task、producer messages、receiver、prompt、decode policy 和 utility。作者明确限定这是上下文相关的 bounded replay label，不是 unrestricted causal effect，也不覆盖任意高阶交互。
- [PAPER] p4 §IV-C Eq7：profile-train/validation 离线生成标签，冻结 hierarchical shrinkage predictor（alpha6）；只用 packet type/route/lexical/size/turn 等 pre-outcome metadata，禁止 final-test outcome/RCE。**离线反事实→廉价 online metadata predictor**已经直接覆盖说明书的一种通用实现路线。
- [PAPER] p3 Eq3 与 p4 serializer：真实 compact UTF-8 application record 的 envelope 计费，transport/link headers 排除；delay 与 receiver-context token 是另两类资源，不能将其 wire bytes 等同 GOSC 的 RF channel uses。
- [PAPER] p5 的 resource-adaptive scheduling 涉及 byte/context/queue/deadline；本轮阅读未发现其主模型直接复现 GOSC 的 Rayleigh RF/动态移动任务，因此不宣称能直接比较优劣。论文结果、源码及最新发表情况未独立复现/查新。
- [HYPOTHESIS] 若要在它之外形成贡献，需明确处理动态 receiver 状态、真实任务未来效果、状态获取成本及固定无线 scheduler 的因果归因，并通过强简单 baseline；这些尚非本研究已实现结果。

**五句记忆**：BANDMAS 已做 LLM 多 agent 的语义 packet scheduling。它通过有限上下文 replay 定义离线贡献标签。它把昂贵标签训练成廉价、冻结的 metadata predictor。字节、排队时延与上下文成本各有边界。新工作不能重包装这条流程，必须检验具体新增机制及其净成本。

## 冲突与缺口矩阵

| 本研究可能主张 | 已核验先例 | 本轮结论 |
|---|---|---|
| ToM/receiver-aware 消息估值 | D01、D08、D06 | 已有；不可单独作贡献 |
| 同状态反事实消息诊断 | D01 p9 + diagnose_value.py | 原项目已经实现；需说明新干预边界 |
| 移除消息后按 receiver 动作差打标签 | D08 p6 | 已有；动作变化不等于长期任务收益 |
| 离线反事实标签训练便宜 online estimator | A02 p3–4 | 直接机制重叠，必须作为紧邻先例 |
| receiver 旧目标/迟滞 + 原生交付时序造成可修复任务损失 | 当前 [CODE] 机制存在，但任务收益未证实 | [HYPOTHESIS]；本轮仅形成可检验协议 |
| 加状态后在等无线总成本下稳定改善任务 | 当前没有证据 | Pending；原 receiver1200 主要区间仍跨零 |

这里没有做全球新颖性判定，也未发现足以声称“新方法已成立”的证据。外部补查 BANDMAS/相关方法的最新版本与出版记录，应在决定方法前另做；本轮没有向外部服务发送本地PDF或研究数据。
