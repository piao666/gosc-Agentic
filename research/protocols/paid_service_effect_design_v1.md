# 付费服务链后的效果设计与执行关卡（2026-10-23）

状态：design_contract，**非已冻结的效果实验manifest**。本稿固定比较逻辑，不编造world查重、方差、功效或预算实测。合同测试协议paid_service_contract_v1.json独立于本文，不能替代效果预登记。

[CODE] 原生gosc/messages.py提供CONF/INTENT/EVID的bit长度公式与Python Packet，未提供完整对应wire codec。新paid_receiver_service仅对输入bytes和已有摘要codec计费；要对原任务报告公平净收益，还须原生task适配、按真实长度重建options/prefix，以及让实际收到的task广播更新原View/ledger。不能简单加CRC成本却保留原包适配/成功率不变。

## 信息/服务合同

- UL：原任务优先、每Agent固定共同容量；摘要只用剩余资源。每次失败/重传计完整帧开销。task采用逐slot重试，summary采用RTT lane；两者是明确不同的重试规则，task规则须在所有arm固定，不称相同最优HARQ。
- DL：task ACK、summary ACK、task广播、summary快照共用固定容量，按该顺序优先级及FIFO排队；允许低优先级饥饿，必须报告等待/未送达。服务内核使用分slot的codeword容量账本，不等于已实现真实分片PHY；不能省略实际分片头却称真实MAC成本。
- 收包：广播发射只收费一次，各receiver独立是否成功；CPU解码完成前不可更新cache。snapshot中created不随重播刷新，TTL从原生成时间计。edge成功不是所有peer收到；ACK也要排队、过信道和解码。
- CPU：单Agent共享编码/解码队列，以显式slot_seconds/encode_seconds/decode_seconds模拟忙碌与排队；这些是场景假设，非硬件实测。CPU预算与wall性能分报。校准前不得把测试用1秒slot和0秒处理当部署事实。
- 时序：外部提交当前本地输入→处理实际到达的DL/CPU作业→原任务UL→summary剩余UL→edge→共享DL→至少下一slot到达。只有通过CRC且完成接收处理的帧可供估值；不改原Planner代码，不读peer私有地图/未来随机数。
- 事件触发：只用自身pose与上次生成值；不变不生成，不靠heartbeat伪造新created。快照按固定间隔catch-up，重复成功不刷新edge generation。捎带须另编码/成功语义后实施，暂不进入主实验。

## 对照与识别

1. M0star：在独立calibration里从原bits/AoI/tuned periodic选择，允许不购买摘要并使用全部预算。
2. public-ToM：不购摘要原公共估值。
3. paid-ignore：真实发送和计费，估值忽略摘要。闭环下不同轨迹导致实际通信事件也不同，不能单靠此arm识别纯信息因果效应。
4. paid-pose：只对估值副本用已收到且比本地EVID新的pose，保留原候选/Planner。它本身就是直接位置刷新对照，不另设同实现别名制造多一个baseline或重复N。
5. age-only：待校准前登记确定规则；拟将公共ToM乘1/(1+有效peer平均age)，无cache回退native。此为人为简单启发式，非概率/正确率估计；必须独立选price并与同规模pose估值对比。未审核实现前不得执行。
6. shuffle：仅在本发送者已收到且有效的peer项之间，用独立任务seed/slot/发送者索引PRNG重排pose值；保持身份/时间/长度与传输不变，不访问未收到项或别的world。

主要检验预设paid-pose相对M0star与public-ToM两项；其他为机制消融。成本前沿须有实际UL+DL及CPU重叠支持区间，无支持时报不可比，不由同W/eta推等实际成本。若需额外Planner刷新arm，另标联合策略实验，不纳入只改估值的主归因。

## 新世界、N与统计

禁止重用原评估/校准划分及已曝光pilot/合同seed。未来从新的候选seed空间生成清单，先对HPC全部登记manifest/config/world指纹查重，再在结果前锁定calibration/test与manifest SHA；当前**没有声称完成查重或使用任何新world**。

最终N不能由本轮合成字节测试估计。顺序为：native adapter合同→有硬上限的成本探测→仅独立calibration估方差及成本→按预设最小任务改善/成本非劣门槛做功效计算→固定N与一次test。任务改善3slots、成本比1.05仅为沿用前pilot的候选阈值，须在新结果前审核；若采用两主比较×任务/成本4端点，预先Bonferroni或相应族校正，不能事后切换。

固定max_steps与失败惩罚/成功率；保留全部超时、格式错误和未完成任务。跨W共用世界按world聚类，时间片/重传不是独立N。拟20000次配对bootstrap需与最终比较族一起冻结。不显著不推等价，只有通信下降/任务变慢不算任务Go。

## 预算和停止

本轮只授权并冻结HPC合同测试<=300s、单线程、0LLM/0训练；**没有效果campaign预算**。后续适配测试可用相同级别有界预算提案，但本稿不自动启动。成本探测、calibration与最终test须分别列配置×唯一arm×独立world数量、单任务上限、总timeout、CPU/RAM预算，再执行。

一旦接口泄漏、cost超预算、DL/CPU服务绕过、source变化或合同失败，停止依赖运行并保留失败。若paid主方法无显著任务收益且成本更高，按AGENTS关卡报告，不自动增N、换任务或训练复杂模型。
