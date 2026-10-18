# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 能否由已有日志识别“代理估值→receiver实际目标→轨迹→任务/资源”的断点？[RUN] 完成14点/448对只读审查；即时shadow不能替代真实next-plan，真实next-target差也不能替代任务标签。尚未定位经独立干预验证的可修复性能缺陷。
- **已核验前人工作**：[PAPER] 沿用[2026-10-16证据卡](../2026-10-16-mechanism/prior_art.md)：GOSC p5 Eq4/p9 §V-D已有ToM与反事实；ToM2C p5–6已有消息移除后的目标分布敏感性；BANDMAS p3–4已有离线replay→廉价冻结估值。本文未新增查新/PDF精读/出版核验，不主张新颖性。
- **实际阅读源码**：[CODE] 启动commit **ef78565f78ac095d4bb11c1f6dcb8b4c21752a42**（clean）；原GOSC核心387b493，原pilot执行48404fd，精度扩张执行83338a3。本轮重读Agent.plan/step、TeamModel、Simulation.phase_decide/communicate/deliver/result、GOSC队列/选择及旧branch/日志；锚点见[evidence_index.md](evidence_index.md)。本轮分析时有自身新增文件，manifest如实记录dirty=true并固定源码SHA，没有冒充clean执行。
- **本轮新增或修改**：仅新增[只读审查脚本](../../../experiments_ext/review_saved_receiver_trajectories.py)、[7项日志对齐契约](../../../tests_ext/test_saved_receiver_trajectories.py)、本目录报告/矩阵/案例/协议/审计、task brief与任务日志。原核心、旧raw/报告、results/cache、Obsidian不写。未反序列化checkpoint、未调用Simulation/Planner/Channel。
- **实际运行**：[RUN] Python3.12.10，输入为既有8个开发world seeds5000–5007的14点×32对，合计896分支日志；当前只读计算 **0条新分支、0个新world**。精确入口见[command_ledger.json](command_ledger.json)。不训练、不改评估指标/划分、不访问外部服务。
- **测试与结果**：[RUN] 初版6项契约通过0.88s；修复后 **7项通过0.04s**（替代集合，不相加）。全448对原始日志独立核查、14点mean/MCSE与R32存档相等；262项输入SHA核验且结束不变。**94/448对**的shadow/actual receiver改变集合不一致，其中72对“有无改变”不一致。302对next-target未变中，140对后续receiver轨迹不同、118对完成时间不同；另外36对轨迹不同但完成时间相同。新统计仅描述，非独立样本推断；原R32整体+.63867 slots、探索95%CI[-2.54326,3.09375]保留，未新增CI/显著性检验。
- **失败/负面证据**：首版审查把全部current_cost强制相同，误包含解码依赖的delivered_bits/dl_bits而断言失败；修正只比较发送attempt bits/symbols，并新增回归契约，旧数据不变。失败保留于[failed-review.log](failed-review.log)及[implementation_repairs.json](implementation_repairs.json)。预定正点案例的最近均值rep实际DeltaT=0，照规则保留，没有换有利rep。日志未保存next-plan之后完整逐slot目标/信念/传输，机制仍不能拆分归因。
- **与原 GOSC 的差异**：仅重新解释已生成的native条件解码日志，未引入策略。EVID成功不仅融合证据，还刷新sender最后位置、ACK并清发送队列，未来重传也会改变；不能将总条件效应全部命名为迟滞或belief收益。realistic平行路径没有接入，当前成本仍为base账本。
- **公平性与泄露检查**：原14点/packet/全部32rep保留，无按好坏删样本；分支当前发送bits/symbols、其他packet、初始future RNG匹配，干预slot运动前缀一致。真实next-plan、hysteresis margin、未来路径/结果均为离线诊断，不能作为当前在线特征。8个world已曝光，448对不是448个独立world；事后分组/案例不作中介因果或泛化声明。
- **成本**：[RUN] 成功只读分析脚本wall **0.584531s**、CPU **0.500000s**（不含进程启动、测试、独立审计/归档）；7项契约另0.04s。原仿真成本不重复计作本轮新增；本轮新通信/LLM/API调用均无。真实wire bytes、ACK/CRC/PHY与状态同步仍未建模，不写实测0；助手tokens未计量。
- **可否进入下一阶段**：**Go：已有轨迹审查完成；Pending：中介变量、可修复性与代表性；No-Go：直接训练新估值器、把目标变化当gold标签、宣称稳定缺陷/净收益。** 原严格R4失败/R4-S1 inconclusive及限定诊断准入保持。
- **用户需要批准的下一步**：建议先审定[28分支观测回放协议](next_stage_protocol.md)，只在原14点rep0记录后续逐slot日志并严格匹配原结果，不做机制消融/策略修改。协议为提案，**未运行**；本轮完成后停止。

## 断点：shadow、下一次实际目标与任务结果

[RUN] “目标改变”统一指同point/rep的success与failure之间receiver目标不同，排除sender；不是某单分支自身相对old_target的重规划次数。下表以“是否至少有一个receiver不同”计数：

|即时shadow分支间有无目标差|真实next-plan无目标差|真实next-plan有目标差|合计|
|---|---:|---:|---:|
|无|275|45|320|
|有|27|101|128|
|合计|302|146|448|

[RUN] 另有22对两者都有差，但不同receiver的身份集合不一样，故集合不一致数为72+22=94。shadow在融合后、运动前用旧规划RNG的拷贝重算；真实next-plan在运动及新感知后使用各rep的future stream。两者的时序、输入与随机流不同，差异不能归因为单一因素，更不说明shadow代码错误。

[RUN] 302对无next-target差中，140对后来出现receiver位置差，118对最终DeltaT非零。故**一次未改目标不能识别为无用消息**。有next-target差的146对中126对DeltaT非零，20对为零；280对receiver轨迹分叉中36对DeltaT为零。故**改目标/改路径不能识别为有任务收益的消息**。各条件组受解码干预影响，是post-treatment分组，不对组均值作中介效应或“多改目标更有害”的因果解释；详见summary.json与paired_chain.csv。

[CODE/RUN] trajectory[0]为初始位置，index k表示slot k−1运动之后。t时隙在交付前已选好目标，干预不改该目标；448对在index≤t+1的前缀全部相同。只比较两分支都实际记录的重叠段，较长尾部本身不叫轨迹分叉；当前completed search终止slot跳过motion，轨迹长度=completion_time，逐分支核对通过。当前数据中无receiver重叠路径差而DeltaT非零的对数为0，仅是本批观察，不能外推为普遍必要条件。

## 全点矩阵与三个事后说明案例

[RUN] 完整[14点矩阵](point_matrix.md)、[矩阵CSV](point_matrix.csv)与[448对明细](paired_chain.csv)均由脚本生成，没有只保留极端例子。每点32对，任务均值/MCSE与原R32精确重建；统计泛化仍只有8worlds。

案例按task brief中公开的事后规则：点均值最大正值、最小负值、绝对值最小；配对rep选DeltaT最靠近该点均值，平局取小rep。**标签中的正/负只是点估计，不是置信分类；案例不构成代表性或机制确认检验。** packet描述/分支context/首分叉坐标见[cases.json](cases.json)。

|案例|point/kind|R32 mean±MCSE / slots|rep|failure→success完成slots|next receiver目标差|首receiver运动差slot|首次found-count差slot|总记录uses差 S−F|
|---|---|---:|---:|---|---|---:|---:|---:|
|正点估计|5001:24 EVID|+7.96875±5.34354|0|93→93|无|未观察到|未观察到|−80|
|负点估计|5005:24 EVID|−15.93750±5.15954|17|41→57|0、2|25|31|+3770|
|近零点估计|5006:8 INTENT|+0.21875±3.71183|3|40→40|5|9|27|−1865|

[RUN] 正点5001:24，sender2发送单条t24、pos(8,7)、det=[293]记录，39bits/39UL uses；ToM=.00104030。rep0两分支目标和完整位置轨迹一致、完成时间一致，通信uses相差−80。该点32对为9正/16零/7负；最靠近均值的rep恰为零，因此不能将这个案例写成“一条确定有益消息”。检测cell293是观测，不是真实survivor标签，本轮没有读取world truth。

[RUN] 负点5005:24，sender5发送t20–24五条EVID记录，118bits/79UL uses、ToM=.0614265。rep17 receiver0旧目标226：failure保持226，margin−.0058910；success改742，margin+.0705368。receiver2旧866：failure保持866，success改742。receiver0最先在slot25由共同位置(9,7)分别走向(9,6)/(10,7)，found曲线在slot31首次不同，最后41/57 slots。所见符合原Planner规则，但没有将迟滞单独关掉；证据、位置刷新及后续通信耦合，**不能称迟滞导致16-slot损失**。全点32对8正/5零/19负，保留了相反结果。

[RUN] 近零点5006:8，sender4广播INTENT438，18bits/36UL uses、ToM=.0989787。rep3 receiver5从旧566在failure保持566，在success选943，首次运动差slot9，found曲线首次差slot27，但两者均40 slots完成；uses差−1865。该点32对16正/4零/12负，任务均值靠近零不能等同没有行为或通信影响。

## 可识别与尚不可识别

[CODE/RUN] 原生planner的旧目标/位置、best/old score（不含1e−12 tie jitter）、margin、private_llr_l1只在shadow和next-plan有日志。next-plan receiver context中1738个分支×receiver决策符合“存在略优目标但未越过迟滞阈值且保持旧目标”（tolerance1e−9），这是规则可见性，不是1738个独立样本或迟滞效应。到达旧目标时即使margin为负也允许换目标；测试保留该例外。

[HYPOTHESIS] 代理softmax与history-dependent Planner失配有源码依据，但要说明其对任务的独立贡献，至少仍缺：后续第一次改目标的时刻/原因、每次新感知/阈值声明、shared/private belief变化、逐slot消息与位置刷新、同时间外生draw对应。不能从全路径/终点倒推这些变量。future RNG最终hash相等也不保证在不同位置取到了相同语义观测；不等也可能仅因任务长度不同导致消费量不同。

完整[变量可观测性与强简单对照](observability_and_baselines.md)区分sender本地、已公开但陈旧、需要带成本同步、离线oracle/未来标签。原TeamModel没有history只是结构差异，不自动成为可发表贡献。下一步只建议补足观测证据，不自动加M0/M1/M2。

## 成本、重建与状态

[RUN] 输入262项SHA全部前后核对；执行时dirty=true仅因本轮新增文件，其确切source hashes在experiment_manifest.json。独立核查不导入审查器或仿真，复算全部448对receiver变化集合、轨迹分叉时刻及14点均值，见[independent_audit.json](independent_audit.json)。仅运行7项新日志契约，未重复完整135项仿真测试；135是上阶段记录，不能当本轮通过。

本机输出根为 `E:\gosc-agentic-teams\.local\reproduction\2026-10-18-trajectory-review-v1`；旧输入根保持不变。可在一个尚不存在的本机目录重建：

```powershell
.\.venv\Scripts\python.exe -m experiments_ext.review_saved_receiver_trajectories --run-dir .local/reproduction/2026-10-18-cf-precision-v1 --output-dir .local/reproduction/<new-review-directory>
```

重建是saved-data review，不产生新任务仿真。需要原始old/new JSONL，不需要pickle；索引不能替代数据。完整命令/失败/修复/测试日志均附本目录。只作本地提交，未推送；归档commit与clean核验见本地Git及忽略输出根closure.json。本轮停止，不执行下阶段协议。
