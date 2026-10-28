# GP-ID新校准设计与执行计划（用户已批准，预算关卡有条件执行）

用户批准时间2026-10-27；基线253a14b。此文件落实前述13方案/假设12新world审阅候选，不撤销原GP-v2 No-Go。无正式test/训练授权。

## 冻结科学设计

13方案全部沿用GP-ID-v1的10个机制arm及bits/AoI/periodic k8 eps0，不改变Planner、候选、服务、信道或price。主方法仍为paid-pose；native/paid-age和显式price形式是控制/诊断，不事后换主方法。

| 类型 | Treatment | Control | 识别问题 |
|---|---|---|---|
| 主机制 | paid-age | paid-native-age | 共同购买规则下，使用买来时间戳的增量 |
| 主机制 | paid-pose | paid-ignore | 固定price下，使用位置内容的增量 |
| 主部署 | paid-pose | native-age | 相对不购摘要简单阈值的实际资源/任务表现 |
| 主部署 | paid-pose | periodic_k8_eps0 | 相对已知强周期参照 |
| 主部署 | paid-pose | public-fixed | 相对不购摘要公共ToM |

每比较三个端点：control−treatment的完成slots gain（正为更快）、treatment/control的UL+DL ratio、逻辑CPU ratio。全部5×3=15端点为预设族；配对world bootstrap20000，固定analysis seed，95%探索性区间和Bonferroni族区间分别报告。小N且单工作点，不宣称确认性显著性或完整成本前沿。

统计约定：gain=配对差均值；成本ratio=两arm均值之比（不是逐world比的均值）。analysis seed28200000，NumPy default_rng生成同一20000×12 world索引，所有主/次比较共用该重采样；percentile采用method='linear'。主族双尾分位为.05/(2×15)与1−.05/(2×15)。保守探索screen要求族区间gain下界>=3slots，通信/CPU ratio族上界<=1.05，并单列均值比是否在[.95,1.05]。更省资源但低于.95的观测照实展示，不能说成本匹配已成立；noninferior/Pareto候选与matched-point筛选分列。

主方法进入后续正式协议审阅要求pose_use及三部署比较全部过预定screen/匹配支持；timestamp_use单独判定，不因时间戳失败否定不使用该时间戳的固定paid-pose机制。即使全部过筛也不是确认性成功，仅允许另写正式验证方案。正式test N恒为null，本轮不从12world估算可执行test N，更不以大N救结果。

合法400slot未完成作为restricted completion time min(T,400)纳入，并同时报告完成/未完成数和false declaration；软件异常/进程timeout不是该删失，保存失败并阻断完整矩阵的正向判定。任一主比较缺world、分母均值零、非有限ratio或退化端点/重采样分布均标记未识别/No-Go，不以零宽经验CI证明总体确定性或等价。

预设筛选：任务最小有意义gain3slots、资源非劣比1.05；部署点同时处于通信/CPU均值比[.95,1.05]才称该点有联合成本匹配支持。无支持则该部署主张No-Go，不插值/扩参寻找重叠。gain区间跨0不证明等价/无价值。次要比较（native-age/public、paid-native-age/native-age、paid-pose-native-age/paid-native-age、paid-pose-age/paid-age及数值形式对照）全部探索性，不据其阳性替换主方法。

校准12个独立world是有限探索设计，不是功效保证。候选cal28000000–28000011、budget28100000–28100001在任何新任务结果前查重/冻结；原作者种子及4000–4099/20000000–20000199/24000000–24000199封存，旧校准不合并为新N。无test执行入口。

## 实现与成本预算

新runner复用已有InformationSimulation，完整保存逐任务result、全观测和同目录数值诊断，输出无损gzip；独立审计以解压流重算，不删候选/字段/失败。合同覆盖gzip解压内容、采样不跨mission、预算包含序列化/重选、统计符号/比值/族规则、固定方案和权限门槛。

在156任务前做26个96slot预算fixture；以包含mission+观测输出+数值重选+压缩的端到端case时间作2倍外推。投影<=1080s，压缩产物预测<=256MiB、足够磁盘、无运行任务及source SHA一致，才执行timeout1200校准。超门槛停止，不自动增加预算/减少N/更换方案。每任务上限60s，失败/超时原件保留；不丢弃不利seed。

完整公式：P_wall=2×(400/96)×12×Σ_case max_budget_world(end_to_end_wall)；P_bytes同样按每case最大实际压缩产物bytes求和后乘2×400/96×12。不得把单个全局case最大值当整个13方案预算。可用磁盘至少671088640bytes（两倍产物上限+128MiB余量）；文件系统free不等于用户quota，未测quota明确单列。256MiB为本轮校准产物硬上限，超限保留已写产物并停止，不删除原始记录。

| 阶段 | 硬上限秒 | 前置 |
|---|---:|---|
| 新合同与必要回归 | 240 | HPC环境/资源/同步 |
| prepare/freeze | 60 | 成功JUnit、相同源码SHA、历史查重 |
| budget probe | 180 | 既有13方案、两预算world、96slot |
| 新校准 | 1200 | 已批协议、独立预算核验、source/world一致 |
| 配对分析 | 120 | 完整矩阵或明确保留失败/截断处理 |
| 独立账本/统计审计 | 120 | 原始gzip/result、冻结协议 |

同步/回传不包含在上述模型/分析时间内，按manifest/receipt另报；每次默认100MiB，若不足在256MiB产物上限内显式512MiB拉取。世界/方法/配置/源文件SHA、dirty身份、资源、命令与输出哈希全部登记。新统计输出只在HPC计算。

## 任务顺序

1. 读取指令与旧交付，核验本地SHA、SSH身份/配额/环境/无running与最新同步。
2. 实现新协议/runner/独立统计与审计，独立审阅后以HPC合同验收；新功能先失败用例再实现，不修改原baseline。
3. 在新任务结果前freeze14个候选world、13方案、源码/统计/预算/授权；运行预算probe并独立复算。
4. 仅预算通过才执行156校准任务；不动态加arm/price/seed，过程失败保留新runID，软件修复不得改变科学输入或假装增加独立N。
5. 计算固定比较的均值/分位数/CI/成本支持与否定证据；独立从每任务原件/事件复算，核对source/world/矩阵/字节账本及统计。不得在线读取未来reward。
6. 回传全部已登记产物与receipt，更新研究/写作入口；最终报告Go/No-Go/Pending及原作者P1缺口。正式test、训练、公共发布和Git提交不属于本次授权。
