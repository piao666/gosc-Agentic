# Research Gap Matrix — 2026-10-22

[PAPER/RUN] 42篇均有范围明确的记录：旧13份保持原范围，新29篇为方法/实验选段。非全库通读、代码可执行验收或全球穷尽新颖性检索。

## 原13篇机制对照（保留原文锚点）

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

## 新增29篇的机制与反证

| 工作 | 已有机制 | 本项目应检验/避免 |
|---|---|---|
| [A04 A Token/KV-Cache Communication Media Selection and Resource Allocation Strategy for Multi-Agent Collaboration](reading_notes/A04.md) | 按发送量、接收端历史上下文和算力比较 NL token 与 KV cache 的边际时延；JMSRA 外层双向贪心选媒体、内层二分分配带宽。 | 接收端状态影响成本已有明确先例；本项目需区分信息对任务效用和对推理时延的作用。 |
| [A05 Wireless Agentic AI with Retrieval-Augmented Multimodal Semantic Perception](reading_notes/A05.md) | RAMSemCom 先传低分辨率语义摘要，接收端按查询请求高分辨率 patches，DRL 调整每轮 top-k 数。 | 接收方按不确定性请求更多信息和迭代 refinement 已有；拟议摘要需与按需请求的简单方案比较。 |
| [A06 Transmission With Machine Language Tokens: A Paradigm for Task-Oriented Agent Communication](reading_notes/A06.md) | 训练任务专用 machine-language embeddings，将多模态 token 经微调 LLM 后压缩，以联合 token/channel 模块传输并作为接收端前缀。 | 这是表示/编解码的近邻，不能把其效果当只替换 GOSC 估值器的同任务基线；浮点 embedding 不等于免费数字 token。 |
| [A07 Joint Semantic-Channel Coding and Modulation for Token Communications](reading_notes/A07.md) | PointTC 面向点云几何；含 token/JSCC 编码、可选 rate allocator/channel adapter、数字调制与重构。 | 资源匹配调制消融值得借鉴；新估值实验应保持表示/信道与候选包固定。 |
| [A08 Heterogeneity-Aware Belief Synchronization for Semantic Communication in AI-Native 6G Networks](reading_notes/A08.md) | MEC latent translator 将 belief updates 映射到异构 Agent 空间，变化时触发、只向相关接收者转发，新 Agent 以校准样本训练小 adapter。 | belief 同步和异构接收端适配已被直接提出；可检验缺口只能落在有成本、陈旧摘要对闭环任务的净效用。 |
| [A09 Intention-Aware Semantic Agent Communications for AI Glasses](reading_notes/A09.md) | 眼镜端 OCR/裁剪/检测预处理，服务端 VLM 从当前内容与历史命令推断意图并选择语义处理。 | 接收侧历史/意图已用于通信压缩；必须报告意图获取与推理开销，并给显式任务信息对照。 |
| [A10 Goal-Oriented Semantic Communication for Logical Decision Making](reading_notes/A10.md) | FOL 世界与目标层，通过语义信息瓶颈/率失真原则选 k 条证据，最小化目标命题加权不确定性。 | 可解释目标选择已存在；LogiCity 公开环境不自动等于该论文算法/全部实验的官方实现。 |
| [A11 AgentComm-Bench: Stress-Testing Cooperative Embodied AI Under Latency, Packet Loss, and Bandwidth Collapse](reading_notes/A11.md) | 六类链路/内容扰动；轻量 ResilientComm 使用双份发送和按陈旧度融合，与无通信、全通信、量化和触发对比。 | 采用多扰动及无通信负对照；避免编码导致基线退化或等价后夸大选择机制。 |
| [B02 Task-Oriented Multi-User Semantic Communications](reading_notes/B02.md) | 统一 DeepSC-IR/MT/VQA，图像和文本用户各自编码，经多用户接收与 Transformer 融合直接完成任务。 | 作为 task-oriented、多用户融合背景；不宣称可直接替换 GOSC 闭环消息调度。 |
| [B03 Task-Oriented Multi-User Semantic Communications for VQA Task](reading_notes/B03.md) | MU-DeepSC 图像 ResNet 与文本 Bi-LSTM 编码，经多天线接收检测与 MAC network 回答问题。 | 体现任务损失驱动联合通信的已有路线；不可将任务重要性原则写成新贡献。 |
| [B05 Semantic Importance-Aware Communications Using Pre-trained Language Models](reading_notes/B05.md) | ChatGPT/BERT 识别词/帧重要性，跨层管理器实施重要性感知功率分配。 | 额外推理并非天然免费；在本项目需保留低成本 metadata/阈值基线及真实增量时延。 |
| [B06 Semantic Importance-Aware Communications with Semantic Correction Using Large Language Models](reading_notes/B06.md) | ICNN 将视觉转换成自然语言，以 LLM 量化帧重要性、AMC 传输并在接收端语义纠错，可再用生成模型重建图像。 | 接收端 LLM 修复已有先例；不能把猜测缺失内容当任务真值。 |
| [B07 OFDM-Based Digital Semantic Communication with Importance Awareness](reading_notes/B07.md) | 语义特征标量量化后走数字 OFDM，以任务梯度和特征相关性量化重要性，分配子载波与量化 bits。 | 支持与物理资源匹配的强 importance 基线；同时改变编码和资源策略会破坏估值归因。 |
| [B08 Large-Language-Model-Enabled Text Semantic Communication Systems](reading_notes/B08.md) | LLM-SC 结合文本概率建模与语义通信，比较传统源/信道编码、JSCC 和 DeepSC。 | 保留低SNR负结果；同 bits/symbol 并不代替完整延迟、算力和任务成本口径。 |
| [B09 Task-Oriented Semantic Communication with Importance-Aware Rate Control](reading_notes/B09.md) | IRCSC 排序特征重要性，STII 结合 BER 与保留的重要度，经拟合选择随 SNR 变化的特征数量。 | 低成本查表/曲线拟合调率已有；新任务阈值和拟合点须在独立 calibration 冻结。 |
| [B11 Bandwidth-Efficient Multi-Agent Communication through Information Bottleneck and Vector Quantization](reading_notes/B11.md) | GVQ 联合信息瓶颈、离散 VQ codebook 和门控；根据本地观测、历史消息、通信上下文决定发送。 | 单纯 IB+VQ+gate 并非新组合；无线 headers、错误及同步成本不能用4bit code index完全代表。 |
| [C01 Goal-Oriented Multi-Agent Semantic Networking: Unifying Intents, Semantics, and Intelligence](reading_notes/C01.md) | GoAgentNet 将感知、通信、计算、执行与编排 Agent 分层，用知识图谱支撑跨层任务目标与闭环反馈。 | 跨层闭环与意图接口已有；须把具体可观测字段/计费协议落地，而非重复架构图。 |
| [C03 On the Rate-Distortion-Complexity Tradeoff for Semantic Communication](reading_notes/C03.md) | RDC 将 distortion、语义分布差异和 I(X;U) 复杂度纳入框架；Gaussian/Binary 特例及变分实现。 | 为推理成本提供理论背景；本项目须直接记录 wall/CPU/tokens，不能以 MI 直接折算 GPU时间。 |
| [C04 WirelessAgent++: Automated Agentic Workflow Design and Benchmarking for Wireless Networks](reading_notes/C04.md) | 把 wireless agent workflow 表达为模块化程序，MCTS+LLM 搜索工作流，WirelessBench 覆盖知识、切片、移动服务。 | 需要区分通信服务 Agent 与 Agent 之间通信；工作流搜索的验证成本和清洗后评分须透明。 |
| [C05 HMS-SCP: Task-Oriented Multi-Scale Semantic Communication for V2X Cooperative Perception](reading_notes/C05.md) | 多尺度 BEV 语义表示、空间重要区域与噪声鲁棒传输，融合邻车信息完成检测。 | 多尺度/置信图选区已有；新方法需同视野与同实际payload，不能用此结果支持LLM私有状态估值。 |
| [D05 Agentic AI-Empowered Wireless Agent Networks With Semantic-Aware Collaboration via ILAC](reading_notes/D05.md) | 知识聚合联合压缩、发射功率与运动轨迹；H-MAP 内层资源求解、外层图匹配决定聚合与方向。 | 通信、计算、控制协同与接收状态依赖已有；首轮估值试验不同时改运动/配对。 |
| [D06 Pragmatic Communication in Multi-Agent Collaborative Perception](reading_notes/D06.md) | PragComm 联合时空稀疏选区、共享字典整数索引和 collaborator 选择；用接收方上轮空间需求筛消息。 | 这是拟议方法最直接近邻之一；可发表区别须在闭环Agent、信息权限及同步成本下成立，不能只换任务。 |
| [D07 Logic-Driven Semantic Communication for Resilient Multi-Agent Systems](reading_notes/D07.md) | 用 temporal epistemic logic/Kripke 模型表述知识恢复和持续性，将 belief-change 消息与协作行动关联。 | 知识状态与动作状态恢复可作为机制端点，但任务指标与可观测状态必须具体定义。 |
| [D09 Embodied Semantic Communication for Collective Autonomous Agents: A Tutorial on Representation, Wireless Delivery, and Closed-Loop Coordination](reading_notes/D09.md) | ESC 教程连接自身/环境/任务/关系状态、语义可靠性与闭环行动，讨论语义补偿、共享和置信交互。 | “receiver不确定性+歧义触发”已有清楚动机，需证明具体低成本估计可测和有净收益。 |
| [D11 From Information Freshness to Semantics of Information and Goal-oriented Communications](reading_notes/D11.md) | 以 AoI、内容/版本、上下文错误和持续错误成本统一梳理 goal-oriented communication；含Markov/MDP与gossip实例。 | 年龄不是任务价值；必须用带内容/任务的简单baseline，且不把年龄改名当新型语义效用。 |
| [D12 Generative Semantic HARQ: Latent-Space Text Retransmission and Combining](reading_notes/D12.md) | Transformer-VAE 在统一 latent空间生成多次表示；接收端质量估计触发重传、加权/MRC等组合。 | 强烈支持各估值器分别调参、按实际成本匹配；uncertainty/self-consistency不能直接当正确率。 |
| [D13 Proxifield: Decentralized Multi-Agent Communication through Semantic Proximity](reading_notes/D13.md) | 推理时用direct address、need matching、plan alignment、information complementarity构造稀疏图，再peer evaluation与action commitment。 | 无训练语义路由和接收需求已有；必须比较简单需求/陈旧度机制，而非把embedding相似度当原创价值。 |
| [D14 Learning to Communicate with Deep Multi-Agent Reinforcement Learning](reading_notes/D14.md) | RIAL 把离散消息当强化学习动作；DIAL 在训练中通过噪声通信路径反传，部署时离散分布式执行。 | 通信策略端到端学习已有基础；新估值器若改变行动策略必须另轨归因。 |
| [D15 Semantic Communication and Control Co-Design for Multi-Objective Distinct Systems](reading_notes/D15.md) | DSK/LSK Koopman AE 在低维latent预测不同动力学，并以STL将系统特定规则融入控制。 | 异构状态和任务规则适配已有；性能必须含微调成本和真正任务约束，不能只报告latent误差。 |

## 当前可检验缺口与否定证据

[HYPOTHESIS] 只能收缩为：固定GOSC候选包/表示/调度/Agent，在仅允许成功送达的有限receiver摘要下，计入获取、丢失、陈旧、headers/ACK及估值等待，是否改善实际闭环资源前沿。D06已有历史需求筛选，A08已有变化触发同步，D13已有need/plan/complementarity路由；只换任务或加摘要不构成贡献。

[RUN] 本轮免费特权诊断1248校准+260验证，6个主要比较0个满足预设联合门槛。W50both均值改善但任务区间跨零；W100存在省通信/变慢取舍。不是等价证明或无信息价值证明。付费摘要、同容量/shuffle/age、反事实标签和训练仍未执行。见[实测报告](../reports/receiver_headroom_pilot_2026-10-22.md)。

当前复杂训练No-Go，部署性收益Pending。保留最强简单baseline，不自动放大样本或挑regime。官方实现/版本边界见[材料核查](official_material_audit_2026-10-22.md)；P1历史校准/cache/逐seed差异独立保留。
