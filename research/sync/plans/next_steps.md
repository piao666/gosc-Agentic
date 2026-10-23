# 下一步（2026-10-23同步成本/估值改变率审查后）

归档更新：实现/文档/运行元数据及R2/R3白名单包随[当日本地提交说明](../../../commit/2026-10-23-01-paid-pose-calibration-and-cost-review.md)归档，未push；下方前序任务中的“未提交”保留历史时点含义。当前No-Go不变。

[RUN] [最新审查](../../reports/sync_cost_value_review_2026-10-23.md)：最终51合同通过，24/24观察回放原结果完全匹配，独立审计及主统计版本一致性通过。观察两版共48条重复记录，只用v2统计，新独立N=0。辅助同slot接收计数修正、v1记录保留。

1. 摘要不是未接入：3927次估值中96.49%改变pose投影、79.35%改变超过诊断容差的期望价值、10.54%改变选包。该漏斗不代表真实reward或因果任务净收益。
2. 下一优先为统一task/summary反馈时钟与CPU可见边界：4503条summary反馈实际2slot而RTO1slot。不得用未来实际ACK设置超时；协议变更所有对照一致。
3. 再审查有界catchup：盲目task历史重播占paid DL77.46%，重复task接收94.55%；但DL排队p90=1slot/max3，不能声称严重排队致退化。若需receiver反馈须真实计费，禁止免费窥探接收者状态。
4. 这些是待实施建议；当前正式test、扩N、训练仍No-Go。原校准/样本/price/服务未改，R2/R3包及本轮资产未Git提交/推送。实施服务协议修订需另立有界关卡，不自动启动效果实验。

---

以下保留前一任务快照：

# 下一步（2026-10-23同格式periodic/CRN独立校准后）

[RUN] [最新报告](../../reports/periodic_crn_calibration_2026-10-23.md)：156HPC测试、24成本probe、144校准任务（独立N12）与独立产物审计已完成并回传。10个简单候选选中periodic k8/eps0；付费pose相对其平均多3.8333slot、成本比1.426004，相对public-ToM多1.5slot、成本比1.357991。探索性小样本，不能宣称普遍无效。

1. **当前No-Go**：任务均值无改善且成本超阈值，规划N15419也超事前200world上限。未冻结可执行test N/预算，预留test未运行，不追加样本、训练或切任务。
2. 先向用户报告负结果，后续优先审查已有账本：摘要新鲜覆盖/估值实际改变率、UL重试与DL历史catchup/等待成本。当前数据不支持单一机制归因；不以终点cache非空推断有效估值改变。
3. 价格/DL/CPU/协议修改或新增消融需明确为何能解释问题并另立有界方案；完整成本前沿、age/shuffle/paid-ignore等消融及部署时钟仍未验收。当前不自动启动。
4. R2/R3包及本轮源/报告未Git提交/推送；0新增LLM/API/下载/训练。

---

以下为前序任务快照：

# 下一步（2026-10-23原生适配验收后）

[RUN] [原生适配](../../reports/native_adapter_progress_2026-10-23.md)已通过HPC145测试及3份重复短fixture原始账本。原生语义→GP-v1 wire→真实长度选包→付费服务→局部接收→下一slot规划闭环已在支持范围内接通；不是作者旧wire精确复现或收益实验。

1. 下一步在相同wire/服务/任务下补强periodic基线和事件索引配对噪声，不能只拿已有bits/AoI就宣称最强M0已齐。
2. 再准备有上限的成本探测/独立calibration预算，查重新world并排除已曝光合同seed16000000–16000002等；以方差/功效冻结N、比较族、成本前沿和一次test。
3. 目前未运行收益campaign、LLM或训练，复杂训练No-Go，Git未提交/推送。新wire、自描述记录与stop-and-wait/历史重播的代价和拥塞须披露。

---

以下保留上一任务完成时快照：

# 下一步（2026-10-23字节服务合同验收后）

[RUN] 付费UL→edge→共享容量DL→接收CPU→pose cache已在显式bytes服务内核接通，HPC128测试通过；首轮账本缺零值字段失败保留。见[报告](../../reports/paid_service_progress_2026-10-23.md)。不将此阶段称为原GOSC任务完整闭环。

1. 下一步完成原生CONF/INTENT/EVID wire适配、真实长度下的options/prefix和接收后View/ledger更新；不能只给bit账本加CRC。
2. 服务模型已有可配置UL/DL/CPU队列与时钟；实际部署参数未校准。DL分slot账本不等于真实分片PHY。
3. 对照与停止规则见[效果设计](../../protocols/paid_service_effect_design_v1.md)。新world先查重，N按独立calibration方差/功效确定，不复用旧test救结果；精确样本与预算未冻结。
4. 当前无任务收益campaign、LLM或训练；复杂训练No-Go；Git未提交/推送。

---

以下保留上一步完成时快照：

# 下一步（2026-10-23最小接口HPC合同验收后）

[RUN] 交付包、最小接口和合同验收已完成；详见[报告](../../reports/minimal_interface_delivery_2026-10-23.md)。HPC129测试通过（85原生+26新增+18既有codec），独立stdlib入口核验源码/47份交付哈希通过。两个run均退出0并已完整回传；无LLM/训练/效果campaign。

1. R2/R3白名单包已准备（47文件/1,330,880bytes，原TableVI补件单列），尚未Git提交/推送；原run outputs不强制入Git。
2. 已实现：每observer送达pose cache、原生EVID可见时间ledger、两条估值路径的只读投影、RTT未决attempt/新代/旧ACK/TTL/预算状态机。仅默认exact/H0合同范围，尚无完整paid任务系统。
3. 下一工程任务是将付费UL→edge→有容量/延迟/丢失的DL→本地cache接成统一服务链，给原task与summary相同H/CRC与服务规则。还需事件/合并/捎带对照，不能把现有单lane合同冒充完整传输验证。
4. 再冻结age/direct-refresh规则、M0和shuffle对照、新world排除清单（含合同seed15000000–15000002）、N/功效/比较族、成本前沿与HPC预算。DL/CPU时钟和这些设计未完成前，效果实验不启动。
5. 复杂训练No-Go；P1原校准/cache/历史差异继续保留。不会根据旧test追加样本救结果。

---

以下为上一步静态审查完成时快照：

# 下一步（2026-10-23静态协议审查后）

[CODE] 当前入口：[研究导航](../../README.md)；[协议审阅稿](../../protocols/receiver_summary_minimal_protocol_v1.md)。本轮未新增科学运行、同步或Git提交；HPC实时进程未重新核验。

1. 已完成文档工作：统一入口、分离23阶段当前计数与续跑前快照，标明说明书/README的旧状态和本地计算示例。
2. 已完成静态审查：RTT未决attempt与latest pending分离；事件生成不重置timer；快照合并与catch-up单列；捎带改变packet尺寸/率/成功概率，暂不纳入首个task主比较。
3. 最小候选只用已送达、TTL内且比本地EVID位置更鲜的pose更新估值副本；不改Planner、不开oracle、不消费三bit桶。原生EVID的本地时间ledger是前置条件。
4. 待实施合同：权限、无cache回退、两条build_groups、乱序/旧ACK/expiry/右截断和完整字节账本。后续测试只能在HPC运行；本轮未实现策略。
5. 执行前仍须冻结DL容量/等待与计算时钟、age/direct-refresh对照、新world/seed、N/功效/比较族、成本前沿、源码SHA和HPC预算。review_candidate不等于可执行预登记或实验授权。
6. 复杂训练No-Go；P1原校准/cache/历史差异独立保留，不盲目重跑或追加样本。

---

以下保留2026-10-22制定时快照，非当前待办完成状态：

# 下一步（2026-10-22摘要信息与条件同步成本核查后）

[RUN] 本轮核查已完成；23测试、4对原策略/观测完整轨迹、4条补payload观测、96组通信回放及独立审计通过。复杂训练No-Go；当前没有自动排程。

1. 字段判断已明确：target/pose有既有INTENT/EVID机制，新鲜值可能未送达，须与直接刷新既有信息对照；三bit私有差异桶不等于正确率、任务效用或完整空间belief。
2. 应用帧和CRC字节已实测，反馈/快照也实际编码；receiver摘要要先到edge再到发送端，不能同slot反向影响原决策。时钟/跨mission/真实PHY和CPU等待仍有边界。
3. 条件传输回放已计剩余UL容量、付费重传、ACK丢失、DL快照/丢失/额外delay、TTL与右截断；cache未用于任务策略。它不是付费方法收益实验或完整同开销前沿。
4. 下一步先审查RTT-aware重传timer、捎带/合并/事件触发等低成本协议对照，避免把朴素逐slot重试造成的高成本说成同步的本质缺陷；本轮尚未测试这些优化。
5. 再定义可审阅的最简单估值接口：保持原Planner/候选包/调度不变，只消费真正收到的cache；三bit不能靠开启oracle变成完整私有地图。需要另冻同信息/同成本任务效果验证、无摘要/age/shuffle强对照和新world，才决定是否值得实验；不自动训练。
6. P1原1000–1079校准、作者cache生成链和frontier/where等历史差异继续独立保留。本次成本审计不能将它们改写为已解决。

入口：research/reports/receiver_summary_information_cost_audit_2026-10-22.md；证据及同步见research/logs/summary-cost-2026-10-22/。计算仍HPC，workers≤2，不本地回退。

---

以下保留上一阶段制定时的计划快照：

# 下一步（2026-10-22验收与有界诊断后）

[RUN] 当前无新计算排程。本轮顺序任务：逐图表/575范围验收、必要补项、协议冻结、HPC改进空间pilot以及文献增补均已推进到本轮有界验收点；完整历史复现和新方法贡献仍未全部通过。

1. 已完成：17个native PDF目视、论文5图/13表/式/算法主张矩阵；9张数值表405格中44格有差异；575记录为当前公开网格外，不是漏跑，不改变39有效noise选点；不补跑无关配置。仅改刻度的rescue展示版已核验，原图保留。
2. 已完成：独立seed/world、权限、事件索引噪声、成本/比较族/停止规则在结果前冻结；HPC5测试+独立审计通过。1248校准含5未达400步目标的记录，全部保留；260验证完成，0/6达到预设联合门槛。
3. 已完成：旧13份文献记录+29份明确范围的选段笔记，更新42篇Gap Matrix、官方材料核查、RQv2与拒稿自查。非42篇全通读或官方代码全可运行/全球新颖性证明。
4. 当前No-Go：复杂模型训练；免费oracle、小N不显著、同校准上限都不能支持部署收益/等价结论，也不能自动扩大样本挑点。
5. 后续先本地做receiver字段增量与真实成本审查；仅当不重复intent、信息可达且成本可控，另写付费摘要最小实现/验证协议。需固定最强不购摘要M0、同容量无摘要、age/shuffle、headers/ACK/重传/丢失/等待、全新world与停止条件，再决定是否值得计算。新试验尚未启动。
6. P1原校准1000–1079材料缺口、作者cache生成链、frontier/where等历史差异仍保留。不再盲目重跑完整队列、换版本或用新cache替代原作者cache宣称完成。

入口：research/reports/acceptance_and_pilot_progress_2026-10-22.md。计算继续HPC，CPU并行≤2。本地文献/编辑/同步允许；新方法训练未开始。

---

以下为旧总审计及续跑计划快照，不是当前运行队列：

# 下一步（2026-10-22总审计后）

[RUN] 当前主队列已结束；23阶段已评估，22正常退出、作者cached回放失败。全部登记产物已完整回传并核验回执；最新交付见research/logs/final-audit-2026-10-22/delivery.json。234420条原始job账本核验通过，38项历史比较已用含.gz参考的v2审计重算。

1. 完成：总审计、作者缓存390任务缺key覆盖诊断、新缓存570/570离线指标重现、15个受限环境/排序诊断、两张LLM缺表补齐。新集合17PDF/18TeX；旧失败、旧图和作者结果均保留。
2. P1科学验收仍部分通过：frontier/where等历史差异、作者cache的prompt生成链、原1000–1079校准过程未恢复。新缓存可重放不等于恢复作者缓存；不再盲目换版本或重复完整实验来掩盖差异。
3. 真实LLM有390混合任务+180Planner对照。tokens/延迟/质量/通信/负结果已入报告；Qwen两组任务收益区间跨零，不宣称跨模型稳定任务增益或等预算优势。
4. 当前不运行新方法训练。后续研究试验须先冻结可复现子集、独立calibration、估值成本、强简单baseline、否定条件；既有13篇文献精读/RQ/Gap Matrix继续作为待验证资产。
5. 图件文件和表格内容清单已核对，但此次未进行逐图目视/完整论文编译验收；这与数值/运行审计分开。

报告：research/reports/final_reproduction_audit_2026-10-22.md。测试/统计/仿真/训练仍强制HPC，不能本地回退。

---

以下为保留的启动前计划快照，不代表当前仍有运行队列：

# 下一步（2026-10-20顺序续跑）

这是完整续跑启动前的源码快照，动态状态请读research/sync/runs/hpc-ordered-resume-20261020/outputs/pipeline_status.json与各子run/status.json；完成回传另看receipts，不能把planned文字当作实际执行完成。

1. 已完成：覆盖比较保护、36项数值诊断；C-belief1400项完整历史匹配，C成本匹配/配对统计。六个原阶段执行完成，frontier/where差异未全部解释，科学一致性Pending。
2. HPC已授权继续：noise23400→overhead82600→shared18400候选，再fresh。fresh按原0–99结果选点，固定3000–3099，上限10300项；启动前冻结精确config/scheme/seed清单，与原生pool目录逐项核验。
3. 原顺序main-sweeps→revision-rest→joint→scheduler→theory→value-fidelity→fidelity-analysis；再cached-llm（禁HTTP）→live-llm（3实际模型/独立新缓存/真实调用）；再sensitivity→sensitivity-fresh→genie-fresh→final-replot。
4. 源码冻结、workers2/数值线程1，沿用原72h截止2026-10-22T10:36:15.888633Z；失败保留并停依赖阶段。cached/live如受材料/服务限制，记录失败，只有独立后续敏感性可继续。每阶段完成由本地管理镜像取回完整日志/输出与校验回执。
5. 本轮并行P2资产已经完成：13篇笔记、Gap Matrix、3 RQ、拒稿自查及数学/基线/负证据/开放问题清单；见research/literature/reading_review_2026-10-20.md。其余29篇、出版页/官方代码及更广新颖性检索仍待做。新方法实现/训练未开始。

保留：1000–1079原校准材料缺口；A1/selected-fresh重复3000–3099不计独立N；原结果/缓存/失败记录不覆盖。候选创新不成立的证据必须保留；所有统计与推理仍在HPC。
