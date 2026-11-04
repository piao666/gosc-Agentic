# GOSC候选表达能力与价值—调度耦合审查

日期：2026-10-30。基线`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`及已冻结扩展。**静态结论：FIFO与“每率最长前缀”确实限制可表达的消息；现有Shadow尚不能证明这些限制是G1负结果的主因，更不能证明放宽候选会改善任务。G1 No-Go保持。** 本轮不重算统计、不重选、不新增候选或执行任务。

## 1. 审查对象与源码路径

[CODE] 下列行号来自本地当前文件；原始core及既有native/BF与HEAD一致，新增Native-Information文件身份以`hpc-native-information-freeze-20261030/outputs/frozen.json`为准，而非假称已包含在HEAD提交内。

| 环节 | 文件、函数与行号 | 可核查事实 |
|---|---|---|
| 感知与私有更新 | `gosc/simulator.py:214–258::phase_decide` | 每agent/slot一个Obs，先写pending_llr，再计划、调用on_step |
| 留存/入FIFO | `gosc/schemes.py:341–360::GOSC.on_step` | 在本地view的Lc+queued_llr上按概率变化过滤；保留后append，非按G1排序 |
| 原抽象消息 | `gosc/messages.py:25–47`；`schemes.py:407–469` | anchor/move/JUMP/detection计费；每rate只取最长可装前缀 |
| native实际wire | `extensions/native_task_wire.py:21–67,77–106` | 显式Obs时间/位置/detections、CRC服务外层；与作者抽象wire不同 |
| 组内/组间选择 | `schemes.py:266–305`；`extensions/budget_feasible_selector.py:78–149` | 每组至多一项，整数总预算；拉格朗日二分+贪心，BF保留旧可行返回 |
| 真正提交与ACK | `extensions/native_paid_adapter.py:96–139` | stop-and-wait，packet仍FIFO切片；ACK后逐记录移出，接收后融合另行发生 |
| G0/G1 | `extensions/native_information_value.py:155–246` | 同前缀、同本地基准，G1仅空间加权；没有内容重组能力 |
| Shadow与签名 | `extensions/native_information_shadow.py:46–75,142–228` | 只替换值并同状态重选，signature含kind/cell/rate/bits/symbols/n_records |

[CODE] 平行路径不能遗漏：`gosc/realistic.py:84–151`另建带overhead/noise的目录，`:403–481`有共享上行；它们未接入本轮BF/native支持域。`gosc/joint.py:54–119`已有EVID/INTENT联合估值、打包与枚举，仍是FIFO最长前缀，不能把“联合消息调度/合包”作为全新发现。`extensions/wire_periodic.py:19–56`按**剩余预算**逐次形成前缀，独立于BF；不能将它与一次按完整W建目录的主路径冒称完全同候选。

## 2. 候选集的精确定义

[CODE/推导] 对一个真实可估值入口，记source filter保留的FIFO为`r1,…,rQ`，`P_n=(r1,…,rn)`。原实现只允许

\[
n_r=\max\{n\in\{1,\ldots,Q\}:s(n,r)=\lceil B(n)/r\rceil\le W\},\qquad
\mathcal O_E=\{(P_{n_r},r):n_r\text{存在}\}.
\]

因此EVID Option数至多为rate数R，**唯一内容数**为`|{n_r}|≤min(Q,R)`；同前缀多个rate不是多个内容方案。只有一个EVID Group，单次至多选一个前缀，或不选。CONF每cell一组；INTENT满足target/shared/acked条件时另有一组。每个Option单独可装下W，不意味着所有选中组组合可装下W。

[CODE/推导] 两种wire必须分别计算：

- 原`evidence_sizes`包含anchor、移动链、跳时JUMP与检测step索引位数变化，不能用“每条固定8bytes”解释作者原模型。
- 当前native EVID的**UL服务帧**长度精确为

\[
B(n)=8\left[19+\sum_{k=1}^{n}(8+2|\mathrm{det}(r_k)|)\right]\quad\text{bits}.
\]

这里19bytes=9bytes任务头/record count+10bytes外层服务封装；每Obs固定8bytes再加每正检测2bytes。仅是该native UL帧，不包含后续DL广播、ACK、CPU、重传总成本。`encode_packet`返回的payload本身不含这10bytes，不能重复收取。

**当前诊断的解析容量界，不是新实验统计**：[CODE/推导] 冻结W=100、rate集合`(.25,.5,1,1.5,2,3,4,5,6)`；即使一个Obs没有正检测，帧也至少216bits，因此r≤2全部不能产生EVID。只有3/4/5/6四档可能有EVID，故当前菜单至多4个EVID Option/4种前缀。全为零检测的理论最宽容量分别为2/3/5/7条；实际检测增加字节，只会缩短或消除这些前缀，不能把该上界写成观测到的前缀分布。该限制来自native wire、W与rate配置的共同作用，不应泛化为原GOSC任意配置都只有4种内容。

## 3. 嵌套、覆盖和被排除的消息

[CODE/推导] 因B(n)严格递增，排序后的rate越高，n_r非递减；不同内容按记录集合嵌套。**内容长度与码率没有正交变化**：同一码率只提供一个最长前缀；一个小前缀若在某低rate入选，可在其他rate仍出现，也可能完全没有其更高速版本。不能在现有目录内随意给某固定payload枚举所有rate。

| 当前可以表达 | 当前不能表达 |
|---|---|
| 在少数“更多旧记录/较高rate”与“更少旧记录/较低rate”组合间选择 | 跳过队首发送后面的关键观测；只发最新记录；按区域选任意子集 |
| 不发EVID、发某个已有前缀；同内容在已有不同rate间调整保护 | 同一码率下自由选择更短前缀以给CONF/INTENT留预算 |
| 按真实变长wire费用处理不同检测量 | 删除某Obs的部分cell、只发正证据或只发负证据、生成语言摘要/新表示 |
| 等待后续机会、原ACK移除后让后面的内容成为队首 | 同一入口发送多个不同EVID包、对不同peer定向发送不同内容 |
| 原source filter在入队时去除小变化记录 | 对已经被filter拒绝的记录事后重新估值；G1接管filter或重排FIFO |

[CODE/推导] 任务覆盖至少分三层：①原始footprint并集随n包含更多观测区域；②有效belief变化`d_n=|sigmoid(L+D_n)−sigmoid(L)|`未必随n增加，正负证据可能抵消、概率饱和或cell已declared；③接收端行动/实际任务收益更不保证增加。空det不是空信息，它表达整个传感窗口内的负观测。记录条数、正检测数、区域面积均不能直接替代任务信息覆盖。

[CODE] 一份EVID同时携带证据与**最后一条记录的位置**。`native_paid_adapter.py:74–78`更新native pose；`voi.py:105–119`也将末尾位置带入ToM的避让模型。较长前缀不仅增加belief证据，也可能刷新位置。未来改为子集选择，若末条位置随之改变，不能把所有收益归因于任务证据排序；需要固定pose或计价的独立控制，且必须另审协议。

[HYPOTHESIS/静态反例] 若队列为“旧区域a的记录r1、当前任务区域b的关键记录r2”，菜单只能选`{r1}`或`{r1,r2}`，不能选`{r2}`。这证明动作表达受限；并未证明现有82快照内确有这种高价值/低价值排列，或r2单独真能改善任务。嵌套菜单仍可能足够：若任务价值主要随累计有效证据变化，FIFO简洁性、少元数据和顺序更新可能比重组更划算。

## 4. 支配关系：哪些“直觉优化”不成立

[CODE/推导] 对某一固定估值h，Option的期望代理为`v_h(o)=G_h(n_o)P_s(r_o)`，资源为`s_o`。若同组`v_h(a)≥v_h(b)`且`s_a≤s_b`，至少一个严格，则b对**这一固定加性代理优化问题**被a弱支配（精确平局保留实现顺序）。不能由此前缀包含关系推出长前缀支配短前缀：长者可能证据抵消、更多uses或成功率更低。

同样，“最长前缀必支配同rate的短前缀”也不成立：被省略的短前缀可能有更高G值，或虽价值小一些却腾出资源供INTENT/CONF组合，或者在FBL下有不同长度可靠性。即使G随n增加，较少uses仍可能产生更大净值。对outage，同rate的P_s与长度无关，但这不足以消除资源竞争；不能沿用到FBL。

支配是估值/信道/状态相关的，不是任务真效用的证明。本轮没有运行全候选Pareto剪枝、精确背包或支配计数；不声称原菜单已经丢弃了多少个真正有用候选。

## 5. 现有Shadow究竟说明什么

[RUN，既有HPC结果，只读] 引用[原结果报告](native_information_shadow_results_2026-10-30.md)与[HPC描述性report](../sync/runs/hpc-native-information-shadow-report-20261030/outputs/report.json)，未重算：

| 项目 | world27000000 | world27000001 |
|---|---:|---:|
| 快照数 | 41 | 41 |
| 多前缀快照 | 35 | 34 |
| G1不是统一比例G0的快照 | 35 | 34 |
| 六价格比较数 | 246 | 246 |
| 双方都选EVID而前缀不同 | 0 | 0 |
| EVID仅rate不同 | 8 | 8 |
| EVID开/关不同 | 4 | 5 |
| same_evid类别 | 234 | 233 |
| 完整G1签名未被声明控制集合复现 | 0 | 0 |

[RUN] 既有结果记录不同前缀的raw/expected层鲁棒排序反转均未出现；net层仅world27000000有4条“pair×price”反转记录，并未改变实际所选前缀。它们不代表4个独立事件，82快照/492比较也不是任务效果N。声明六价位、曝光world与24slot范围不排除其他价位/阶段产生差异；不能用本次数据重新调权重或寻找新正结果。

### 5.1 一个按原始顺序读取的反例：same_evid不是全调度不变

[RUN，原件第0条，不按效果挑选] `shadows.json[0]`：world27000000、t0、sender0，快照SHA`c2c407d8dbb82b91e14d2a192251fd1b863ebad94ff0442771a3ac590b343c4a`。唯一prefix1，raw G0=`0.1642694536423836`、G1=`0.2527639961914897`。price0时：

| 方法 | EVID | INTENT | 总uses（原件值） |
|---|---|---|---:|
| G0 | prefix1/rate4/216bits/54uses | rate4/152bits/38uses | 92 |
| G1 | prefix1/rate4/216bits/54uses | rate5/152bits/31uses | 85 |
| 同状态EVID统一缩放 | 与G1相同 | 与G1相同 | 85 |

该条的`same_evid`只描述EVID；非EVID值未变，INTENT选择仍因共享预算耦合而变化。不能从467条same_evid推断467次完整选择不变；先前“16rate/9开关”也仅统计EVID类别，不是所有调度差异的总数。两方法trace都是`legacy_feasible`，**这不说明预算从未触发**：该字段仅表示原legacy返回已可行；原函数内部可能已经执行二分/贪心，其返回uses也不是最初`pick(price)`的需求。当前trace不足以逐例复原全部内部乘子和边际裕量；本轮不调用selector来补算。

## 6. 为什么有数值变化却没有前缀变化：分层解释

[CODE/数学] 在固定净价格λ、固定组和其他组选择条件下，G0选项a对备选b的净值差为

\[
M_0(a,b;\lambda)=G_0(n_a)P_a-G_0(n_b)P_b-\lambda(s_a-s_b).
\]

令`δ_o=[G1(n_o)−G0(n_o)]P_o`，则同λ下差值为`M1=M0+δ_a−δ_b`。非比例变化不必超过原有净值间隔，也不必令最优选项越过离散边界。该式是条件代数，不是本轮测得了M0/M1；两策略预算乘子λ可不同，且贪心填充不等价于单个固定λ的全局最优。

| 因素 | 已能确认 | 现有数据不能确认/替代解释 |
|---|---|---|
| 菜单结构 | 嵌套、每率最长、至多一个EVID；部分只能表达尺度/保护 | 不知道加入任意子集/更多prefix后任务是否改善；未做候选干预 |
| 价值差距 | 非比例变化存在；raw/expected不同prefix次序未反转 | 未形成每次决策的完整margin分布，不能说“所有gap很大” |
| 可靠性 | 同一P_s作用于两方法；outage中高rate的P_s更小 | 未将负结果归约成信道单独贡献；不能把UL P_s当peer最终可用率 |
| 预算与组间竞争 | 个体可行不等于组合可行；首条实际INTENT率改变 | 没有预算松紧/精确最优反事实的新统计，不能说“预算总饱和” |
| BF离散选择 | 严格u>best_u、零阈值、首个tie、二分与贪心会形成分段常值选择区域 | 工程可行不保证最优；未证明BF掩盖了有益G1选择或造成全部失败 |
| 接收/任务反馈 | 所有shadow是同Public-ToM宿主状态的离线选择 | 不是G0/G1实际闭环轨迹；未测接收端动作或任务效应 |

[HYPOTHESIS] 最可信的联合解释是：受限菜单把可比较内容压缩到少数年龄/长度/率组合；有权重变化时，它仍可能只移动发送或保护门槛；原相对排序、成功率与组间竞争共同使前缀落在相同离散选择区域。**这是与证据一致的解释，不是已识别的因果链。** 候选结构、权重辨识力不足、任务代理偏差及预算近似仍是并存解释。

## 7. 研究判决与反证要求

1. **Go：静态命题成立**——当前菜单不能表达任意任务证据子集，也没有完整的payload×rate组合；可在系统模型中准确写出此边界。
2. **No-Go：因果/效果主张**——不能写“FIFO导致G1失败”“改候选即可获益”或“BF工程修复验证了任务价值”。[GP-ID](information_calibration_results_2026-10-27.md)的156任务/原预算阻断与[BF工程验收](budget_selector_acceptance_2026-10-27.md)分开保留；修复7旧违规/192兼容目录不撤销原科学No-Go，485/519是旧工程证据，不是本轮新测试。
3. **Conditional Go：未来路线A规格审查**——仅在用户另行决策后，先定义一个有硬候选上限、真实wire/ACK/重复证据合同和成本的候选轴；固定估值对比生成器，再在共同菜单上比较估值，防止同时改两者归因不清。不直接复活G1，必须另命名研究修订。
4. **反证**——若可表达的新增候选仍无独立内容差异，或仅靠更短wire/更新pose/更多候选搜索解释收益，或强“最新/均匀/区域覆盖/随机子集”已同样好，或成本匹配后优势消失，则新候选路线也No-Go。以上为未来判据，本轮均未执行。

**本轮成本/验证**：只有静态阅读、原报告与第0条既有记录查看、文件SHA/Git/链接检查；无新HPC或本地科研计算、仿真、统计、训练、测试/重选。所有历史负结果、失败run与冻结文档原样保留。进一步路线判断见[路线决策报告](research_route_decision_2026-10-30.md)。
