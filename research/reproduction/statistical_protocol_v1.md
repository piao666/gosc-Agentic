# R4-S1：获批的统计复现协议（2026-10-15）

## 身份与范围

这是用户批准后的修订协议，不替换 `repro_protocol.md` 的严格逐seed验收。旧R4仍失败；作者历史环境与轨迹仍未核验。已观察旧1399条记录和seed0数值探针，因此不是完全盲法预注册；以下规则在本轮新增5200条结果之前固定。不得由本轮结果反向调整界限、样本量或方法。

[CODE] 原版 `387b49389385b51c275dc5a22ec1672087edda1d`；工作起点 `8e97bc66e395f3e4887bf38d3b22533e1d23fe9f`。固定主Windows CPython3.12.10 / requirements-windows.lock.txt（NumPy2.5.3），不修复或替换原数值调度实现。原source、results、cache、PDF不改。

## 固定样本

沿用原始 `run_revision.experiments()` 与 `validate_headline.select()`，对照作者冻结标签核验配置，禁止重新用fresh结果挑点。

| 面板 | 点数 | seeds | 次数 |
|---|---:|---|---:|
| W100 frontier，ToM/TV/bits/AoI/periodic全部原点 | 34 | 0–99 | 3400 |
| private，default/W50/snr-5 × shared/joint oracle | 6 | 0–99 | 600 |
| 原六headline设置 × GOSC/periodic冻结点 | 12 | 3000–3099 | 1200 |

共5200次重新执行，不复用1399条旧结果充作新运行。所有方法、seed、无线预算/信道/候选/Planner与原配置相同；完整curve和每seed输出保留。Calibration1000–1079不用于本轮调参，历史calibration过程仍未重新运行，不能声称完整R1–R6全部复现。

## 主要统计关卡：104项同时等价区间

每个操作点N=100、按seed显式对齐。52点各有两个主要终点：task（search completion_time，rescue saved_fraction）与UL数据symbols。将fresh−author的配对差归一化：search和symbols除以固定作者面板均值；saved_fraction保持原单位。固定实际界限为search±0.05、symbols±0.05、saved_fraction±0.02。5%与既有receiver诊断实用阈值一致；rescue为绝对2个百分点的研究判断，不能声称来源于原论文或行业标准。

用20000次seed-level bootstrap，统计随机种子20261015。同一seed面板内所有方法/配置共用bootstrap索引，0–99与3000–3099面板分别抽样；不能按消息或时间片抽样。对104个归一化配对均值，使用各自原样本标准误标准化bootstrap中心偏差，取每次最大绝对值的95%分位q，构成 `delta_mean ± q * SE` 的近似family95%同时区间。零方差项按观察到的恒定差处理，不将此表述为所有未来seed恒等的证明。另报未校正95%percentile区间、N、均值与分位数。该bootstrap是有限样本近似，不能宣称精确覆盖率。

- **equivalent**：整个同时区间在对应闭合等价范围内。
- **incompatible**：整个同时区间在范围之外的一侧。
- **inconclusive**：其余跨界情况；不得用P>0.05或区间重叠宣布成功。
- 所有104项equivalent且5200条有效完整、原输入未改变，才标记 **R4-S1 scoped statistical agreement**。否则保持Pending/No-Go，不启动新receiver实验。

这是对这两个保存seed面板的均值稳定性审计；不保证所有分布、尾部、成功率或原论文全部claim成立。实际界限是已暴露数据后的修订判断，不能补写成最初预注册。

## 强制补充输出与公平性

全部逐seed字段差异（1e-9仅用于记录精确差异，不作停止条件）、最大偏差、正/负/零差、成功/失败/false declarations、bits/delivered_bits/DL/latency等可用字段及缺失项都报告。作者headline仅保存task与symbols，其他指标不能凭空补成历史参考。

报告六headline的同seed GOSC/periodic效果及资源比，原private shared/oracle效果与UL/DL开销；固定eta不等于实际等成本，oracle是未计价的特权信息，不是可部署方法或任务最优上界。任何显著方向不自动构成新贡献。

对W100绘制全部操作点，并重建5000/10000/20000 uses的原log-linear lower-envelope matched frontier。使用相同seed重采样（20000次）；不外推；明确每预算有效bootstrap数。可保留原作者Bonferroni15口径作对照，但该插值比较不是每mission等成本干预，不能替代实际匹配资源实验。原作者保存面板与fresh面板均用相同分析重算，不能手工改点。

## 执行与后续

新runner不改旧strict runner，不伪造旧成功manifest。先执行完整tests及统计性质测试；plan包含所有expected、配置、protocol/source/deps哈希；结果目录exclusive-create。最多4workers、每进程1数值线程、R4最多45分钟。异常/缺seed/非有限数/预算破坏/原输入哈希变化失败并保留证据；不因中途结果有利提前停止。完成后才一次性分析，不中途调参。

仅当R4-S1关卡通过，可按先前冻结的`diagnostic_preregistration.json`与adapter contract进行4000–4099、3设置×4模式=1200次receiver因子诊断。该阶段保持六个主要单因素比较、原阈值与成本解释；不改变任务或开发估值器。R5 cached/live、重新校准、训练、新模型、发布/发送消息均不在本轮。
