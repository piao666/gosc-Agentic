# 实验协议与停止规则

> 最新工程验收：[BF-selector-v1报告](../reports/budget_selector_acceptance_2026-10-27.md)覆盖485测试、7旧违规与192可行目录、52短fixture及7派生wire合同；原始行/预算/组/成员/实际服务审计通过，新增效果N0。派生合同映射时间/发送者且只留控制组，不是历史闭环任务重跑。原156任务No-Go不重算，不扩N/正式test/训练。

> 最新校准2026-10-27：[GP-ID-CAL-v1设计](../protocols/information_calibration_design_2026-10-27.md)及[执行结果](../reports/information_calibration_results_2026-10-27.md)已冻结并运行13×12新world，5主要比较/15端点、20000配对bootstrap和资源修订全有独立身份。统计No-Go，正式test N仍null；bits/AoI选包违规使全轮工程验收阻断，诊断统计复算不豁免违规。不扩N/price或事后换主方法，任何修订另立协议。下方“尚未冻结”是此前快照。

> 2026-10-27执行补充：下表合同/prepare/短probe/独立审计已完成，见[执行报告](../reports/information_identifiability_acceptance_2026-10-27.md)。表内“未运行”为10月26日设计快照；新收益校准仍未制定可执行N/完整预算，正式test/训练No-Go保持。

2026-10-26；状态：技术内核草稿。当前仅GP-ID-v1合同/成本probe实现，HPC未执行，不是已冻结的收益实验。

## 已有证据与后续执行分离

[RUN] 原复验23阶段22正常退出/作者cache回放失败；GP-v1与GP-v2的有界校准均No-Go，原两批12world不能合并为独立N24。已有新cache可回放不等于恢复作者cache。历史差异与[P1清单](../reports/p1_evidence_gaps_2026-10-26.md)继续保留。

| 阶段 | 输入/交付 | 执行门槛 | 当前 |
|---|---|---|---|
| 合同 | 新旧fixture、观察开关、权限/TTL/账本、selector有限目录、篡改拒绝 | HPC身份/环境/配额/无running/SHA同步 | 未运行 |
| prepare | 成功JUnit、相同源码SHA、历史seed/world查重、frozen | 全部合同通过，无失败/skip | 未运行 |
| 短probe | 13方案×2world×on/off，24slot，上限52fixture | prepare/source一致、120s硬上限 | 未运行 |
| 独立审计 | 原始typed事件、决策与censor守恒、输入SHA | probe完整成功 | 未运行 |
| 独立校准 | 前瞻新world、有限对照、指标/预算/功效方案 | 以上通过并另行审阅批准 | 未制定可执行N/预算 |
| 正式test/训练 | 冻结独立数据/功效/主要比较 | 新证据支持且明确授权 | No-Go/未运行 |

探测候选seed仅在HPC registry与world指纹核验后冻结，碰撞不静默替换；旧test预留24000000–24000199封存，原0–99/1000–1079/3000–3099不作新方法调参集。时间片/重复观察不增加独立world N。

## 公平性与控制臂

完整arm表、机制差分与HPC命令见[GP-ID协议](../protocols/information_identifiability_v1.md)。所有arm共用Planner、候选生成、实际wire、Channel/CRN与服务配置。bits/AoI/periodic k8/eps0是简单参照；1e-4是既有诊断工作点，不代表成本匹配。不得把paid-age事后转称预登记主方法。

必须分清：native-age vs public的阈值作用；paid-native-age vs native-age的购买服务作用；paid-age vs paid-native-age的时间戳使用；paid-pose vs ignore，以及共同native/paid时间戳下的位置增量。策略差分仍包含内生轨迹，不写单消息因果直接效应。

当前没有与BANDMAS/JTCM/PragComm等兼容外部方案的同设定数值比较。未来实施需核验相同任务/信息/预算，不能拿跨论文数字直接比较；相关机制证据见[Gap Matrix](../literature/Research-Gap-Matrix-2026-10-22.md)。

## 未来收益实验必须事前确定的内容

[HYPOTHESIS] 拟以截断完成slots、成功/失败/false declaration为任务终点；UL+DL真实uses和逻辑CPU、实测process/wall分别报告。选择少量主要比较及其联合任务/资源端点，在新校准前写明最小有意义效应、成本支持/非劣界、比较族、alpha与停止条件。**本文件不事后沿用或改变旧GP-v2功效假设来放行新方法。**

独立world为统计单位；配对bootstrap/permutation的次数、分析seed、多重比较校正、截断/超时/格式错误纳入规则在结果前固定。按校准方差/预算形成正式test N提案，不能为获得显著性自动扩N。若要证明“无需付费信息”，须有等价或最小效应检验及功效，不能用p>0.05代替。

成本支持只根据实际通信/计算观测点判断，不插值捏造重叠，不用同W/price冒充同成本。服务优化改变的协议需独立版本且全部对照共同适用，不能把GP-v1/GP-v2不同world的均值差写成修订收益。

## 运行、审计与数据治理

所有合同/仿真/统计经HPC `hpc_runs`，单worker/数值线程1；本地仅编辑、Git与轻量哈希。每run保留manifest、source SHA/dirty/sync、身份/环境/资源、真实命令、config/seed/model/cache、stdout/stderr、status、原结果和产物SHA；执行完成与receipt镜像完成分开。失败和负结果不可覆盖。

目前无新LLM、收费API、下载、GPU或训练。未来LLM迁移须先过M0关卡并单独授权，记录实际模型digest、prompt/cache key、HTTP attempts/tokens/latency/fallback，禁止Planner回退冒称LLM成功。
