> 当前执行状态见[RQ v2](RQ_v2.md)。以下保留10月20日假设与合同；其未实验描述不覆盖10月22日有界诊断。

# RQ v1 — 2026-10-20

状态：[HYPOTHESIS] 三个可证伪问题及实验合同已写定；不是创新成立、正式统计预登记或训练许可。本轮只恢复原论文实验，没有M0/M1/M2新方法实现、标签采集或训练。完整待测协议、成本上限与seed注册在实现前另立不可变manifest。

## 定位与已有先例

[PAPER] D02 p.5 III-A/B已经提出匹配交互反事实credit与receiver-context decision distortion；GOSC p.4–6已用ToM估值并研究误差鲁棒性；ToM2C p.6用删消息KL监督；BANDMAS p.4–6用RCE+metadata+adaptive prices；iCoTASC p.4离线表支撑轻量online。故本课题不主张首次提出任何上述概念。

候选定位：**可观测且有成本的receiver状态能否在闭环Agent任务中带来超出强简单估值器的净收益，以及什么时候不值得使用。** 贡献是否足够须由实验证据与后续近邻文献核验决定。没有预设“复杂模型一定需要”。

## 信息与干预合同

1. 估值/调度位置固定为原GOSC对应的edge决策位置，候选包/编码/传输选项/channel/Agent策略不变。所有候选方法使用完全相同的信息权限；跨schemes.py/realistic.py的接入需同一映射审查。
2. 公共可观测：已确认公共belief/声明、成功收到且有时间戳的intent/position、候选包type/length/age、已观测信道/队列。先区分现有GOSC已有字段和拟新增摘要，避免把重复字段当额外信息。
3. 新摘要仅可来自receiver实际发送并成功抵达edge的有限字段（例如本地目标/不确定性分桶、状态版本），以本地最后收到值和age为输入。未送达的最新目标、private pending LLR、隐含memory、真实victim/world状态均禁止在线读取。不存在摘要时使用预定义缺失mask与M0回退，不能悄悄查询oracle。
4. 摘要size/量化/刷新规则/失效期限/ACK与DL/UL路径在校准阶段冻结，并与任务消息竞争同一预算；初始化、header、重传、反馈、丢失和推理等待都要计费。即便所有方法都能读取同一摘要，也要给原无摘要baseline计“无需购买”的公平资源选择，而非强迫其承担ours开销。
5. 私有全状态只用于标明privileged的离线上限诊断，不能与deployable ours混标；Genie是理想通信参考而非任务最优上界。
6. 反事实label在同一决策前状态克隆，deliver/drop或规定delay双分支使用同一任务与后续策略。外生world/sensing/channel随机事件按mission、物理时间、Agent、事件种类索引，防止仅设相同RNG seed却因分支消费次序不同失配。分支自适应行动可不同，这是待估效应；外生过程应匹配。
7. 估计到达条件下的增量价值V(m|O,t_arrival)，不混为token相似度、BANDMAS两固定上下文RCE或D10的frontier slope。若标签已乘packet delivery probability，原scheduler不得重复乘一次；正式协议显式固定conditional/unconditional含义。
8. 离线训练可以使用受限oracle标签，但features只由当时在线可观测量构造；反事实rollout成本、查询数、模型tokens及存储全部登记，在线禁止调用未来reward或LLM judge作为免费真值。

## RQ1：额外receiver摘要是否真的提供有效信息？

[HYPOTHESIS H1] 在固定任务/调度器/编码和实际资源匹配下，带时间戳的有限receiver摘要能降低相对于强简单估值器的任务决策错误，并改善mission质量/资源前沿。

- 最小序列：M0（type/size/age/已有公共信息的手工阈值或轻量线性/查表）→M1-same-capacity无新摘要→M1+摘要。所有学习器相同容量、训练样本/调参预算；保留原ToM/bits/AoI/TV/调优periodic。M1不要求LLM。M2昂贵counterfactual online assessor在此阶段不启用。
- 消融：去receiver摘要、摘要shuffle、仅age、真实可达但陈旧摘要、privileged新鲜全状态；receiver通告协议本身与估值器贡献分开。
- 诊断：预测误差/排序只是辅助；重点看原选项/发送阈值附近的错误选择与条件任务收益、原GOSC零值区和无headroom区。用未来真实任务效用验证代理，不能用训练标签一致性循环论证。
- 否定条件：M1只优于弱baseline，不优于同容量M0；shuffle同样好；或privileged信息也无可重复headroom。此时拒绝“receiver状态必需”与复杂估值路线。CI跨0表示证据不足；等价结论必须另外预定义等价界，不能直接宣称等价。

## RQ2：同步、陈旧度和估值延迟何时抹平收益？

[HYPOTHESIS H2] 存在有限工作区间，在计入摘要更新和估值全部成本后仍有正收益；在过高更新频率/过大delay或预算充裕时收益消失甚至为负。

- 执行位置HPC；先按原任务与已定义链路扩展扫摘要刷新/age、loss、delay与实际budget。数值网格、最大任务量和停止规则须先冻结，不能观察test收益再加regime。
- 两个主要报告轴：search的任务完成时间（含未完成的截断/失败，不只分析成功任务）或rescue的saved fraction，以及实际总空口channel uses（UL+DL+控制+摘要）；同时报告payload bytes、packet success、wall-clock推理延迟分布、CPU/GPU、tokens。没有能耗仪表不得把GPU占用当作joules。
- 同任务预冻结质量目标下比较最少实际资源，或同资源上限下比较任务质量；不以同η/同W代表cost matched。frontier插值需保留原始点与不可达区，随机混合若未实施不得称可实现策略。
- 负对照：公共信息已充分、同质policy、预算充裕、摘要严重过期。若只能免费新鲜oracle时有效，或实际同步/等待成本使前沿优势消失，则拒绝部署效率主张。
- 不用任意α·quality−β·tokens的事后加权总分隐藏成本；若需要标量reward，权重必须外生预定，原始质量和各资源仍完整报告。

## RQ3：收益是否由明确的信息失配机制决定，能否迁移？

[HYPOTHESIS H3] 如果H1/H2过关，收益应集中在已预定义的局部知识/意图失配和有限时间关键更新，而非所有消息一律更好。

- 首先只在原search/rescue条件内检验任务、Agent数量/异构policy、公共更新缺失与接收信息age的预声明交互；不要同时改拓扑/任务/压缩以救结果。
- 按消息kind、decision threshold margin、age和可观测不确定性给机制诊断；异构LLM沿用同模型/同候选/同seed，缓存回放与真实调用独立记录。GOSC5选1的通过不支持开放式多轮推理泛化。
- 若效果来自更强LLM、额外tokens、训练任务泄漏或单个有利regime，拒绝一般化主张。新任务与跨模型检验只在前两问有效、预算/协议批准后开展；不在本轮偷偷实现。

## 数据、统计与Go/No-Go

- 当前0–99是公开选参/评估轨道；1000–1079原校准流程缺失；3000–3099被A1与selected-fresh重复用，2000–2019已用于原fidelity。上述及9000–9009 pilot与已登记seed不作为新方法未经说明的“全新测试”。
- 新train/calibration/test按完整mission/world分组、不重叠；同mission的slot、Agent、counterfactual兄弟分支必须同split。未来seed集合先对全部run registry和轨迹指纹查重，再预登记；本文件不编造已检查的新seed段。
- 统计独立单位是mission/task/world，重复决策不是独立N；同world配对、跨mission cluster bootstrap/permutation、预声明主终点/比较族/Holm或Bonferroni，报告N、效应、区间、预算未达/超时/格式失败和所有负结果。
- 定样本量/最小实际有意义效应只可用独立calibration/pilot，在test前冻结。原任务paper target可作复验参照，不能事后变更目标。
- Go顺序：P1公开可执行基线及历史差异边界审计→feature/CRN/成本协议→M0 headroom pilot→H1/H2配对验证→有限泛化。资料缺失单列，不伪造严格独立校准已完成。
- 当前结论：P2文档可审阅，**新方法实现/训练No-Go，科学有效性Pending**；这不阻止继续用户已授权的原论文复验。
