# 有限摘要低成本同步与最简单估值接口 — v1审阅稿

> 2026-10-23实施更新：[合同协议](receiver_pose_contract_tests_v1.json)已在运行前冻结，HPC129测试及文件审计通过，见[报告](../reports/minimal_interface_delivery_2026-10-23.md)。只完成pose/ledger/双路径估值接口与单sender RTT合同，未完成付费系统服务链、事件/合并/捎带和任务收益验证。下文审阅稿的原始未执行状态保留为设计时快照；它不能充当已执行的效果预登记。

- 日期：2026-10-23，Asia/Shanghai。
- 状态：**review_candidate / not_implemented / not_run**。本文件固定本轮设计提案，不能称为已冻结的实验预登记；精确实现、world清单、样本量、预算及统计manifest仍须在新结果产生前冻结。
- [CODE] 审查基准：4ff4147654c07781d77a42acee3f31c0b8792f38；原GOSC基线387b493。不修改既有冻结协议、核心或结果。
- 范围：只讨论原search/Planner下的有限摘要；不引入LLM、学习器、反事实标签采集、新任务或共享上行主张。

## 1. 问题与已有反证

[HYPOTHESIS] 在真实送达、陈旧和同步开销下，仅改善估值器看到的位置，能否优于不购买摘要的强简单基线？RTT等待和去重能否降低旧立即重试协议的成本？两个问题分开检验。

[RUN] 既有免费特权诊断0/6通过；96条件回放使用固定任务轨迹、逐slot立即重试，cache未参与策略。它们不证明付费摘要有效，也不证明所有同步方案成本都高。证据见[特权诊断](../reports/receiver_headroom_pilot_2026-10-22.md)和[摘要审计](../reports/receiver_summary_information_cost_audit_2026-10-22.md)。

[PAPER] 已有阅读记录：GOSC p5 Eq4已用接收者模型；ToM2C p6 §3.3/Eq6已有消息移除后的目标敏感性，p16说明pose可见性边界，见[D08](../literature/reading_notes/D08.md)。本提案不主张首次receiver-aware/反事实/事件触发，也未重新检索协议标准；以下均为待测试的本项目设计。

## 2. 静态源码发现与双路径约束

| [CODE] 基准路径/函数 | 已确认事实 | 设计约束 |
|---|---|---|
| extensions/receiver_transport_replay.py:41 replay | 每slot处理到达帧后生成摘要，pending只要可装就尝试；没有next_retry定时器 | 旧协议保留作T0，不覆盖旧结果 |
| 同文件 replay/feedback/batch | 成功ACK只到发送者才清pending；重复成功也可触发全快照 | lane释放、代际确认、快照去重分开定义 |
| gosc/voi.py:30 TeamModel.__init__、:65 _points、:88 _belief_mass | pose影响距离和位置排斥；oracle还读取完整私有数组和确认集 | 聚合桶不能当私有belief；pose改动须覆盖这两项且只在估值副本 |
| gosc/schemes.py:407 build_groups/:471 transmit | 构建TeamModel后选包/速率 | 候选、原消息尺寸、rates、价格规则、lagrangian_select保持一致 |
| gosc/realistic.py:84 build_groups/:153 apply/:403 _uplink_gosc/:429 _uplink_gosc_price | 平行路径独立建值；shared还含请求/grant/price | 不能只改普通路径即声称支持现实/共享路径；首个task试验仅正交UL |
| gosc/simulator.py:107 _snapshot/:130 deliver/:167 _downlink/:214 phase_decide | 快照仅存Lc/declared/位置/意图；EVID位置来自末条record；先决定再上传 | 原生位置缺独立时间ledger；摘要不可同slot反向改变已做决策 |

## 3. 最简单估值接口：pose-cache-ToM（候选标识）

[HYPOTHESIS] 首个接口只用显式送达的pose，不消费三bit桶。桶虽然可能包含增量信息，但没有空间方向，当前不定义乘数、正确率或完整LLR重建。旧novelty+pose帧可在诊断中复用，但须照付被忽略桶的成本；专用pose帧如要删字段，另定义codec、长度和测试，不把旧6byte偷偷改成更短。

输入合同：`value_view(sender_local_public_view, received_cache[sender], native_pose_ledger[sender], now)`。仅给TeamModel构造估值副本，不传给Planner、motion、候选消息生成、公共belief更新或任务声明。

- cache项至少含source agent、created_slot、received_slot、pose、valid_until和传输generation/session身份；后两类身份若只是固定mission命名空间假设必须明示，跨mission需另序列化计费。
- 只允许使用CRC通过、已送达当前发送者、未过TTL且received_slot≤now的条目；本slot UL生成项最早t+1+额外delay可用。不能读取edge未分发cache或其他Agent当前内存。
- 以发送者**实际收到的**原生EVID最后record.t维护估值专用native_pose_ledger，随其真正接收的快照更新；禁止直接用edge最新时间。初始化位置作为共同已知t=-1单列。较晚到达但较旧的EVID也需记录“当前公共位置对应的时间”，不能仅用最大时间冒充该位置的时间。
- 仅当摘要created比当前本地公共位置时间严格新，才替换估值副本team_pos中已有peer键；相同时间相同值用原值，冲突记错误并禁用；时间未知时回退原值。不得增加原来未知的mate集合。
- 投影改变TeamModel距离与_points中的位置项；team_intent、Lc、declared、sender本地pending、CONF值保持原口径。tom_oracle必须false，禁止恢复其他人的pending/confirmed或当前pose。候选EVID本身reveals sender位置的原规则保持。
- 输出依旧为原INTENT/EVID非负裁剪前的同单位价值，原裁剪、率选项与调度规则不变。无有效cache时必须逐字段回退native结果。审计记录原值/新值与所用cache身份，不把差值称为真实任务效用。

这只是既有位置机制的及时刷新对照，不是新语义表示或创新证明。若连时间ledger和只读隔离都不能实现，停止task试验，而非开启oracle兜底。

## 4. 同步协议对照与因果时序

所有计时只使用发送者本地状态与事先给定的模型时延；不读未来信道/ACK。每slot顺序：消费到达反馈/快照→过期→冻结可用估值视图→原任务决定→生成本地摘要→按可用预算发送→edge解码/合并→排期下行→下一slot才可能消费。

| 候选 | 相对变化 | 必须计费及失败情况 |
|---|---|---|
| T0 immediate | 完整保留旧逐slot规则 | 参考协议，旧96结果不重新命名 |
| T1 RTT wait | 每发送者至多一条未决attempt；next_retry=last_tx+1+configured_extra_delay+固定slack；首次提案slack=0 | ACK丢失后到期才重试；已收到NACK可在当前新发送阶段重试；无重叠attempt |
| T2 T1+change | 只在pose变化生成；未ACK时替换待发送latest，不重置未决attempt的timer；每generation保持原created | 触发使用本地pose及自身已发/已确认状态，不读edge；无变化时不为保持TTL制造虚假新状态 |
| T3 piggyback | 仅作独立可行性对照：等已有UL或DL载体，不强迫发送载体 | 延迟/饥饿/期末未送达照报；附加长度、CRC覆盖、ceil边界、解码率必须重算 |

T1必须分开`inflight_attempt`与`latest_pending`。新生成不得绕过旧attempt等待；旧ACK只确认其实际generation并释放lane，不清掉较新的pending。TTL到期取消相应代数据但不误认旧反馈属于新代；需用实际发送时记录的(sender,tx_slot)映射，不能从无法解码的payload偷读身份。未知/可变RTT不得从未来实际反馈取值，另立有上限的RTO规则后再验收。

合并原则：edge同generation重复decode仍需反馈，但不自动制造一份内容相同的全快照；多个新项同slot合并为一帧。快照重播/catch-up需独立定时（提案每5slot、TTL20），否则无新UL时丢失接收者可能永远落后；heartbeat只重复真实created，不刷新age。ACK用于确认edge接收，不能宣称所有peer已收到。比较T0/T1时固定快照规则，比较合并时另做开关消融，避免混因。

捎带会改变原packet长度、可装prefix、速率选择及FBL成功概率，不能实现为“原任务先选好再免费append”。首个task主比较暂不纳入T3；实施前须另冻组合wire格式及原子/分段CRC成功语义，在选项构造前计附加长度，并证明和对照共用相同候选/预算接口。没有载体时允许不发，不将等待成本删掉。

## 5. 成本与资源公平合同

每次attempt累计实际UL字节/uses；DL逐真实广播帧计一次发射成本，逐接收者分别记丢失和cache状态；unicast补发单列。头、CRC、ACK、快照、请求/grant/price（若启用）各只计一次。相同H/CRC语义适用于全部task与summary帧，不把旧H0 task与带CRC摘要的混合账本当公平主实验。

task主试验先用正交UL：固定每Agent每slot总上限W、相同rates/信道；原任务优先，摘要仅消费实际剩余容量。所有arm原任务调度器相同，日志同时保留请求量、占用量、未发摘要。不得额外叠一条免费摘要UL。DL须固定公共时隙容量/服务队列与反馈优先级并让原task广播也竞争；该容量尚未核验，**不填猜测值**。若只事后累计DL而不模拟其等待，仅能报告会计成本，不能称完整时延净收益。

共同W和硬上限只是同资源机会，并不保证实际uses相当。最终需在独立calibration上冻结各arm多个工作点，按实际UL+DL/控制成本区间比较；无重叠支持区间时报告不可比较，不外推或用同eta代替。无摘要M0可不购买信息并利用全部原预算；另设相同保留容量/真实padding空载消融，已用padding须过同信道、同计费，未用容量只记reservation不能算发射。

CPU实测wall/CPU/RSS与逻辑任务slot分开报告。physical slot时长与部署CPU未冻结前不换算等待、不宣称部署净收益。任何以0计算等待为条件的任务结果必须显式标为理想计算时序；进入部署结论前另验收时钟/计算服务模型。0LLM只是本方案范围，助手tokens不冒报0。

## 6. 分阶段验证提案（均未运行）

**A 实施合同。** 先实现独立扩展与HPC测试：无cache回退native；拒绝oracle/跨Agent内存；t+1最早可见；乱序/重复/旧ACK；未决中supersede不绕RTO；TTL和期末截断；UL/DL边界与CRC；本地EVID时间ledger；投影不改Planner/原消息与公开状态；两条build_groups对同一输入投影一致。分支数不当独立N。任一合同失败先修复，禁止进入效果运行。

**B 有界传输诊断。** 可复用旧4条轨迹比较T0/T1及事件/合并开关；其任务固定，不估任务收益。未来运行前精确列出网格、成本指标、源码SHA及上限；不能沿用旧96个case数量冒称新设计完整。验证timer的成本/可达性取舍；仅在calibration选传输方案。

**C 真正闭环任务试验。** 使用新world与event-index外生噪声，Planner/候选/调度与原网络口径固定；task/summary真实改变容量与时序。必须含以下arm：

| arm | 信息与用途 |
|---|---|
| M0star | 独立校准选择bits/AoI/periodic，可不购买摘要 |
| public-ToM | 原公共估值，不购买摘要 |
| transport-only | 同一真实协议付费送达，但估值忽略cache，用于系统总效果分解 |
| pose-cache-ToM | 同协议、仅估值位置投影 |
| age-only | 同一生成与送达协议，估值只按事前定义的年龄规则；规则未定前不可执行 |
| shuffle | 同长度/同本地到达时序，仅在已收到且有效peer项中按独立固定PRNG打乱pose，缺项回退，不从其他world取值 |
| direct-refresh | 位置刷新机制的简单对照；若需新pose帧或不同语义更新，先冻结格式，不能伪称已有INTENT传pose |

闭环中不同arm轨迹/负载不同，transport-only与主要arm不会自然得到相同已实现通信事件；它是总系统对照，不能仅凭它识别“纯信息”因果效应。辅助固定前状态/相同送达流诊断才可识别接口差异，且不得冒称独立world；全部对照需匹配预算前沿。age-only的确定规则、direct-refresh的格式与统计比较族是执行前待决事项。

## 7. 划分、统计与停止条件

原0–99、1000–1079、3000–3099，旧5000–5007、9000系列及11000000–14000002已预留/使用部分均不直接复用。新seed不在本稿拍定；先读取完整登记world/seed账本，生成无冲突calibration/test清单及world fingerprint，结果前冻结。跨W复用world仍按一个world聚类。

先用独立calibration估计方差/配对相关与成本，不查看test来定N。预设任务效应下限提案3slots、成本非劣阈值提案1.05，均承接前pilot作为待审参数，不事后按结果改。主要终点为截至固定max_steps的完成slots（未完成保留为截断并另报成功率）；如把截断当惩罚分数须在机器manifest明确，不能丢失败。预算/协议参数、对照、主要比较、族校正方法、bootstrap次数、功效与N冻结后只评一次test。不把“不显著”称等价。

Go标准必须同时包含预定任务改善和资源非劣/匹配区间，同时披露计算成本。仅通信下降而任务变慢不算通过；shuffle/age不劣于真摘要则不支持pose语义贡献；免费特权结果不是付费上界。未达门槛保留负结果，不自动加N、改world或切任务，不启动M1/M2训练。

## 8. 预算与执行关卡

| 项目 | 状态 |
|---|---|
| 本轮静态审查 | 已完成文档设计；0科学运行 |
| HPC合同测试/有界传输 | 提案，未实现/未测速/未启动 |
| closed-loop calibration/test | 未冻结N/精确seed/功效/DL时钟/成本网格；执行No-Go |
| GPU、LLM、训练、下载 | 不在此协议范围 |

预算公式为各配置×各arm×各world及前沿点数量之和，实际计数需去除arm别名重复，再乘HPC有界成本探测的保守单次上界；当前没有可信wall估计，不冒用旧580s作为新闭环预算。后续执行必须先完成具体实现与合同、HPC身份/配额/sync manifest核验，登记run并设置硬timeout/outputs目录，再申请对应实验预算；本稿不授权自动计算。

本稿可Go到独立最小实现设计；执行Pending；复杂训练No-Go。P1历史校准/cache/数值缺口独立保留。
