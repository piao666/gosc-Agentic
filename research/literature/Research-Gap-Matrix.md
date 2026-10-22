> 2026-10-22更新见[42篇范围明确的矩阵](Research-Gap-Matrix-2026-10-22.md)与[官方材料核查](official_material_audit_2026-10-22.md)。以下为10月20日历史快照，本轮已有独立有界诊断。

# Research Gap Matrix — 2026-10-20

状态：启动10篇加D08/D10/B10共13篇形成可追溯笔记；两篇长综述和B04/AgentComm按明确章节重点阅读。不是42篇全部精读，也不是全球最新文献的穷尽新颖性检索。各PDF物理页、SHA和阅读范围见reading_manifest_2026-10-20.json及reading_notes/；私人PDF与完整提取文本不进入同步。

[PAPER] 表中“未报告/未核验”只界定本轮证据，不等于方法不存在。没有跨论文合并不同数据集、模型、设备、单位或CI。候选差异均为[HYPOTHESIS]，还没有新算法实验。

| 工作与锚点 | Agent/任务及动作 | 接收者/推理状态 | 语义价值及标签 | 无线/调度 | 资源与成本边界 | 对本课题已占据的机制 |
|---|---|---|---|---|---|---|
| [D01 GOSC](reading_notes/D01.md) p.3–6 Eq.3–5/Alg.1 | 多UAV search/rescue；planner及5候选LLM行动 | 公共belief、已宣布intent；理想/最后快照，ToM近似对方 | ToM/TV/bits/AoI，非全局mission最优 | payload/rate/price，多选择背包；现实DL/共享上行扩展 | channel uses、UL/DL/控制；估值计算也需另外计量 | 已有receiver-aware、联合what/when/reliability、反事实与估值鲁棒性 |
| [A02 BANDMAS](reading_notes/A02.md) p.3–6 Eq.3/6/9/10 | 固定producer packet，receiver准入后QA/证据 | task、type/route、turn、receiver context资源、queue/deadline | 两上下文RCE，离线profile+shrinkage；test不用gold/RCE | lossless容量/FCFS延迟，adaptive prices | 紧凑JSONL bytes含envelope，不含transport/link headers；tokens/latency | 已有counterfactual-inspired标签、metadata低成本估值、receiver资源及动态价格 |
| [D08 ToM2C](reading_notes/D08.md) p.4–9/16 Eq.1–6 | CTDE/RL多Agent协作目标 | 预测对方目标/观察，可见pose假设 | 去消息后receiver subgoal KL伪标签 | GNN何时/向谁通信；非GOSC PHY | 向量浮点长度，不是空口bits；训练与pose获取口径不同 | 已有对方意图预测、receiver决策变化、删消息学习 |
| [D02 joint design](reading_notes/D02.md) p.5 III-A/B | LLM协作，V2X示意来源/内容选择 | 明确receiver context与reasoning dependency | 匹配提供/撤回/延迟的边际interaction credit，运行时预测 | interaction/resource、content/fidelity、topology联合设计建议 | V2I带宽、RSU计算/内存；完整可执行细节未核验 | 概念直接覆盖拟议核心，不能主张首次提出receiver反事实任务价值 |
| [D04 reasoning native](reading_notes/D04.md) p.3–7 | 异构policy Agent案例 | shared ontology/RBE、belief演化 | 预测receiver行动、belief divergence触发 | 协调/数据双平面与稀疏信号 | 概念KPI及聚合仿真图；完整seed/配置缺口 | receiver-aware、reasoning alignment、静默、近似递归均已有 |
| [A03 AgentComm](reading_notes/A03.md) p.3–6/8–12 | BS/robot多轮巡检/清理；异构LLM | BS历史更全、robot受限，KB更新 | key items/句子/其余分级，LLM提取 | OFDM不同子信道保护/码率与semantic codec | UL/DL Kb、SR/Complete；KB初始化非零；LLM调用成本不等同空口 | 已有Agent消息压缩、重要性保护、KB与任务闭环；Im也会降低SR |
| [A01 JTCM](reading_notes/A01.md) p.3–6 Eq.1–11 | 两Agent视觉VQA | 任务prompt条件接收LLM/LoRA | 语义层cosine+任务CE，端到端学习 | learned complex symbols，SNR MoE、MIMO | complex symbols与准确率；训练/LoRA能力需匹配 | 已有任务条件token/PHY联合表示；不是可替代消息准入的同任务基线 |
| [B01 DeepSC](reading_notes/B01.md) p.3–6/8–12 | 文本传输/句意重建，非闭环协作 | Transformer decoder，非动态私有Agent memory | CE+MI估计；BLEU/BERT相似度 | AWGN/Rayleigh，端到端JSCC | matched symbols；传统runtime未含全部源编码 | 语义编解码/MI/迁移不新；低SNR强不等于所有SNR胜 |
| [B04 ASC](reading_notes/B04.md) p.3–10 Eq.11/14/19 | 多用户STL10分类至edge | 模型/任务共享importance KB | 梯度重要性、η(o)离线拟合，SLA权重 | 压缩率+功率/带宽+user选择，SCA/分支界定 | task success×timely delivery；假定共享索引知识 | 压缩资源联合、非凸分块与低维importance均已有 |
| [B10 iCoTASC](reading_notes/B10.md) p.2–6 Eq.1–8 | 多encoder融合图像分类 | 融合receiver/已知slot容量 | IG+Weibull量化utility，离线表 | shared RB/维度/量化greedy；非凹不保证最优 | online时间排除训练；RB/bit非LLM token | 离线重工作＋在线轻量查表已有；TableI有不胜CVX的点 |
| [D10 Pareto](reading_notes/D10.md) p.4–7/11–14 | Markov远程估计，send/no-send | MAP receiver规则已知、error-free ACK | long-run成本，value=最优前沿斜率 | iid loss，约束MDP/SPLIT/RVI | 频率F与长期成本J；非任意有限任务 | 已有成本前沿/边际价值；定理不能直接迁移LLM环境 |
| [C02 survey](reading_notes/C02.md) p.5–9/17–18/25–28/38–39 | 三层四实体四阶段 | memory/KB动态演化与一致性 | intention/semantic/task分层，引用多类VoI/AoSI | 多类无线技术综述；非唯一算法 | 计算/存储/KB管理挑战 | 接收方知识、记忆及生命周期已是明确问题空间 |
| [D03 survey](reading_notes/D03.md) p.7–8/14–15/25–26/29–30 | intuition/reasoning/agentic分类 | KB/world model/session memory | task/effectiveness单位与推理代价 | taxonomy本身channel-agnostic | 明确system boundary和alignment–overhead | 同步/陈旧与净收益是已有方向，综述vision不证明新颖性 |

## 有限候选缺口与最强反证

[HYPOTHESIS] 候选不是“提出接收者感知”，而是：**在固定GOSC候选消息、表示、调度器和channel下，仅允许edge看到已成功传达的有限receiver摘要，检验在摘要延迟/丢失、全同步开销与估值延迟均计费时，是否仍能改善闭环任务的实际成本前沿。** D02已有概念、GOSC/ToM2C已有相关机制、BANDMAS/iCoTASC已有离线轻量化。是否有可发表的新算法或理论差异，目前未成立。

| 假设 | 已有直接挑战 | 最小验证 | 若失败应怎样收缩 |
|---|---|---|---|
| receiver摘要有额外信息 | GOSC已有intent/common belief；bits/AoI常相近 | matched容量的M0 metadata与M1+摘要，shuffle/age/privileged-oracle消融 | 无headroom则放弃复杂receiver estimator，报告信息冗余 |
| 闭环标签优于静态RCE/目标KL | D02已提出；GOSC counterfactual低排序与正负收益 | 克隆同决策状态、事件索引共同随机数，mission分组split；看threshold regret和完整任务 | 不因MSE变好宣称任务变好，终止昂贵标签路线 |
| 高精度值得总成本 | 原GOSC multiplicative-error鲁棒；D03强调alignment成本 | actual UL+DL+控制资源、同步/估值latency与tokens同报，匹配前沿 | 增益被成本抹平则拒绝部署性主张 |
| 在异构/陈旧情形有特定收益 | D04、C02、D03已有动机 | 原任务内预声明regime，简单同质/充裕预算负对照，校正多重比较 | 仅保留支持的局部结论；不追加新任务挑点救结果 |

## Baseline、代码与复现状态边界

[CODE/RUN] 只有GOSC拥有本项目已运行的源码/数据/测试/mission证据；HEAD876fc523，上游387b493。其他12篇本轮是原文阅读，没有声称运行官方代码。BANDMAS-style metadata/ToM2C-style removal proxy/iCoTASC-style lookup若后续实现，须标“机制适配”，验证接口/训练预算，不能标为官方全系统复现。

必须同时保留：调优periodic、bits、AoI、TV、原ToM；同容量不带receiver摘要、带age、shuffle摘要、privileged oracle；固定payload/rates/预算，按实际资源匹配。不得让ours多调用LLM或免费读真实receiver private state。

## 尚未完成的文献工作

其余29篇未在本轮深读；D06/A10/A08/D11/B05/B07/B09/C03等方法深入路线继续按具体问题推进。其他官方repo可执行性、出版主页、跨任务迁移和完整最新SOTA检索未验收。GOSC独立1000–1079校准材料缺失，当前历史差异不通过改论文或选版本强行消除。
