# 变量可观测性、成本边界与强简单对照

## 变量可用性矩阵

[CODE] 参照ef78565的gosc/voi.py、simulator.py、schemes.py和extensions/counterfactual.py；行锚见evidence_index.md。本表不是已实现在线数据管道。

|变量|当前sender在线是否可得|本批日志保存什么|使用边界/代价|
|---|---|---|---|
|候选type/content/records、payload bits、发送rate/symbols|本地可得|selected packet全描述|估值比较须保留相同候选/调度/rate；selected-only存在选择偏差|
|sender位置/target/私有记录|本地可得|白名单sender_position/target、内容；没有完整私有矩阵导出|sender_target不是receiver_target|
|时间t、消息记录age、ToM/TV/AoI/bits|本地/共享计算可得|全部14点白名单|AoI是此源码定义；TV是belief shift不是本轮先验真实任务价值|
|共享Lc、declared、team_pos/team_intent|原生ideal DL假设下可读；team位置/意图是最后公开值|point只存派生特征，旧checkpoint含完整矩阵但本轮未加载|已有广播成本在native DL账本；不能把共享状态称全局真实状态|
|统计CSI/ps|csit=false下已知mean SNR；ps为信道模型预测|known_snr、ps|不是测得decoder置信度/LLM正确率|
|瞬时SNR/自然decode|当前调度时不知（csit=false）|离线attempt记录|不能新增给在线估值器，或须改变CSI设定并重新计费/对照|
|receiver真实当前pos/target、是否到达旧目标|不保证最新公开；只有team_pos/intent近似|current_targets离线数组，shadow/next上下文|若同步须新增timestamp/version/ID/量化/headers、更新频率、丢包/陈旧/等待；不能免费查询sim.agents|
|receiver真实local belief、完整pending_llr、confirmed_pending|sender不可直接读|本轮JSON不含完整矩阵，仅shadow/next private_llr_l1/分数|norm不能重建belief，下一时刻norm也不是当前特征；需独立同步机制或只作offline oracle|
|真实next target/score/margin|当前消息发送前不可得|shadow与t+1实际context|post-treatment变量，不能作为当前训练输入/在线触发；不含best cell ID与tie draw|
|完整后续target、belief/感知/packet流|当前不可知|未逐slot记录|不能由trajectory倒推或用未记录写“已验证”；下一阶段可观测回放再采|
|未来path/curve/completion/false declarations/总资源|发送前不可得|全部896分支结果/位置轨迹|只作离线标签/分析；不得在线决定value|
|真实survivor地图|sender不可得|JSON无完整真值；本轮未读取pickle|det列表是有噪声观测，不能当truth|

[CODE/HYPOTHESIS] 当前基础模型payload内置8bit type/id header及32×32 cell的10bit索引，INTENT为18bits（messages.py:8–19,64–65）；这并不意味着新receiver-state同步仅需18bits。时间/version、位置/目标、聚合/量化、CRC/ACK/下行广播、重传与等待的完整codec尚未设计。不能把“只加一个target”写成零成本或已实测低成本。状态同步必须先明确序列化与信道服务流程，再做cost-matched UL+DL+sync+compute frontier。

## 最强简单对照与反证条件（提案，未实现/运行）

|候选对照|现有依据与必要条件|什么结果会否定新增复杂度|
|---|---|---|
|保留原GOSC-ToM|冻结原候选/调度/channel/Planner；不改价校准/训练划分|新增runtime特征的收益区间跨零、成本更高则不应升级模型|
|原GOSC-AoI/Throughput（bits）、TV|现有schemes.py已有模式；R32白名单已有点分值，INTENT bits/TV为常量导致rho不可定义|简单分值的未见任务cost-matched结果同样好，则无复杂估值必要；当前selected14点不能替代policy实验|
|常零任务效果预测/保持原策略|标签噪声大时为估值预测的零成本参照，不是声称零发送策略优越|新增predictor未超过校准后常量/简单排序或不确定性门槛，停止训练复杂模型|
|只用sender/shared已公开状态的廉价M0|如本地age/size、当前公开意图的陈旧度；不能使用真实next-plan或receiver最新私有状态|加入receiver字段后的增益可由age/size解释，或获取字段的同步成本抵消收益|
|带成本同步receiver当前target/position摘要的M0|必须事先写同步codec/时延/陈旧/失败，并固定预算公平分摊|免费oracle有收益但带成本/陈旧版本消失，则不可部署；若目标差不改善任务也不成立|
|离线history/private/position/time-order诊断对照|仅在补足日志并审定拆分协议后运行，不当成online policy|拆分后差异不稳定或与任务无关，则不应继续宣称该机制是主要性能瓶颈|

[PAPER] GOSC已有复杂ToM与简单估值不稳定优劣、ToM2C已有动作敏感监督、BANDMAS已有离线标签到metadata predictor。详见2026-10-16/prior_art.md，未在本轮重做论文查新。目标敏感/receiver-aware/离线反事实三者本身均不是新贡献。

[HYPOTHESIS] 只有对当前真实任务具有可证伪联系、特征可在线取得且成本公平，才进入M0。当前不学习、不调参、不新增seed、不更换任务，不把本表作为已运行baseline成绩。
