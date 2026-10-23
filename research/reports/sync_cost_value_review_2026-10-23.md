# Research Task Report — 同步成本与估值实际改变率审查

- **Research Question / Hypothesis**：[HYPOTHESIS] 前轮付费pose负结果，是摘要未进入估值、价值改变未转化为行动，还是同步/服务成本过高？本轮审查机制与账本，不重新检验正式收益。
- **已核验前人工作**：本轮没有新增PDF阅读或新文献主张。[CODE] 原TeamModel本就使用公共位置构造距离/repulsion，原GOSC裁剪价值并做离散选包；本轮只诊断这些已有机制，不主张创新成立。
- **实际阅读源码**：[CODE] base `4ff4147654c07781d77a42acee3f31c0b8792f38`；`gosc/voi.py`TeamModel、`native_task_wire.py`WireGOSC.build_groups、`receiver_pose_interface.py:84`value_view、`native_paid_adapter.py:81/99/113`选择/投影/服务时序、`paid_receiver_service.py:74/126/171`CPU/tick/历史重播、`receiver_rtt_contract.py:76`RTO。以原冻结源码SHA为依据，非假定dirty源码都已提交。
- **本轮新增或修改**：新增只观察模块`extensions/sync_cost_diagnostic.py`、回放与独立审计脚本`review_sync_cost.py`/`audit_sync_cost_review.py`、6项合同测试、事前协议/brief/本报告；更新导航和机器状态。没有修改原策略、服务规则、参数、旧原始结果或冻结校准协议；没有Git提交/推送。
- **实际运行**：[RUN] HPC `n1`、UID8301880、Python3.11.15、2CPU/24GiB、单数值线程。最终51项相关合同/回归通过。观察器有两个版本，每版回放原12world两arm各24条，合计48条重复记录；**最终v2的24/24完整result与原结果完全相同**，原冻结源码SHA一致。独立审计通过24份最终成本账本和3927次决策不变量，并核验两版主要价值/UL/DL/CPU统计完全一致。`new_independent_N=0`，独立world仍12，下文统计仅取v2，不将两版合并扩大样本。
- **测试与结果**：[RUN] **51 passed in0.67s**（6新增观察合同+17服务+17原生适配+11配对噪声）。新增检验纯观察结果相等、无关随机字段相同、ACK尚在CPU时的edge后重传、全历史重播与部分DL右截断、shadow不改pending、同slot不同快照不重复计算未修改cache。下文给出实际改变率与成本分解，不给新的收益显著性或功效判决。
- **失败/负面证据**：[RUN/CODE] 六个登记run均退出0；首轮观察器的`summary_same_generation`辅助计数经静态复查发现会重复计入同slot其他快照的未修改项，已修正并增加合同，原v1保留。该计数没有用于本文主结论，v2独立审计确认主要指标完全不变。旧校准/模型result从未改写；无结果不匹配。摘要大量改变估值，仍未建立任务净收益；前轮No-Go维持。服务RTO与CPU边界未统一、盲目历史重播显著消耗资源，但没有证据把任务变慢完全归因于任一项。
- **与原 GOSC 的差异**：[CODE] 审查对象是新GP-v1/paid服务模型，非作者历史wire。观察包装不改变Planner/估值规则/信道/预算/CPU时钟。shadow仅在paid实际决策前状态比较“同一个sender已有信息加/不加已收到pose”，不推进替代任务轨迹。
- **公平性与泄露检查**：[CODE/RUN] 仅重复原19000000–19000011 calibration，未运行预留test、无新world/调参。shadow不用未来奖励/peer私有证据；逐项验证curve、完成时间、所有服务成本/队列与指纹原样。3927是事件分母，独立world仍12；public-ToM只做成本观察，没有采集其价值漏斗，summary中public的空计数应读作N/A，不是“public没有估值”。
- **成本**：[RUN] 首轮合同/回放/审计wall分别1.274556/125.882817/0.504926s；最终合同1.122086s、回放124.881263s（child CPU user124.668939/system0.164308s、maxRSS91676KiB）、审计0.483015s/maxRSS83048KiB。两版回放合计约250.76s，低于原360s预算；v2使用剩余预算的230s硬上限，合同均<=120s、审计各<=60s。包括shadow、JSON和runner子进程，非部署估值器时延。0新LLM/API/GPU/下载/训练；助手tokens/GPU峰值未测。
- **可否进入下一阶段**：**Go：诊断观察和本轮审查交付。No-Go维持：当前设定正式收益验证、扩N和复杂训练。** 既非摘要未接线，也不能从较少选包变化断言无任务价值。优先审查/统一反馈与CPU时钟、限制盲目重播，再另立协议，不能直接拿旧N计划启动效果实验。
- **用户需要批准的下一步**：本轮审查完成；后续如实施服务协议修改，需按下方具体修订建议另立有界关卡，所有对照同改并重核成本/信息权限。本轮没有自动修改RTO、删重播、换任务、调price或重启校准。

## 1. 摘要确实改变估值，但多数没有改变选包

[RUN] paid-pose实际调用估值共**3927次**；只在未被stop-and-wait阻塞、确实进入候选构建时计数，不是所有agent-slot。每次5个peer机会，共19635项。对同一pre-state、候选语义/长度/率和price，比较当前真实投影视图与原公共视图；candidate身份全一致。

| 漏斗（分母3927个实际估值决策） | 次数 | 比例 |
|---|---:|---:|
| 至少一个peer的投影坐标改变 | 3789 | 96.49% |
| 至少一个候选期望价值浮点值改变 | 3351 | 以次数为准，非显著性检验 |
| 至少一个候选价值改变超过诊断容差 | 3116 | 79.35% |
| 最终选包/率签名改变 | 414 | 10.54% |
| 最终消息类型/cell/record-prefix选择改变 | 411 | 10.47% |

[CODE/RUN] 诊断容差预设为`abs(delta)>1e-12+1e-9*max(abs(values))`，**只用于观察报告**，没有替换原选包阈值。记录的是裁剪后、乘成功概率的Option.value，不是原始未裁剪VoI或真实reward。原CONF价值665个option全部不变，符合仅位置投影的接口合同；INTENT/EVID存在both-zero与价值改变但相同选择情形，不能把“值变了”直接当任务收益。

[RUN] peer机会分类：13259项（67.53%）满足已送达/TTL内/比本地native新且坐标不同，5633项（28.69%）过期或尚不可用，258项（1.31%）更鲜但坐标相同，435项（2.22%）没有cache，50项（0.25%）不比native新；未发现ledger mismatch。被替换项的摘要age均值7.54slots（p50=6、p90=14），对应native位置age均值89.66slots（p50=84、p90=170）。这些是估值机会处的事件统计，不把重复出现的peer当独立样本。

[RUN/HYPOTHESIS] **不是“摘要没接入/全是旧信息”**：新鲜位置实际改变了大量估值。当前瓶颈更接近“更新后的价值经裁剪、离散率/预算/price选择后，多数动作相同，付费流量却持续发生”。这是可检查的接口现象，尚不能推断修改哪些价值/阈值就会改善任务；少量决策也可能影响很长的后续轨迹。

## 2. 同步成本分解：直接摘要项占额外资源的83.28%

[RUN] 以下为同一12world相对public-ToM的**每任务平均uses差异**，不是matched frontier或纯信息因果分解。

| 账本项目 | 平均channel uses |
|---|---:|
| 真实摘要UL（含CRC、失败/重传） | 19308.00 |
| 摘要ACK及快照的真实DL服务 | 16087.33 |
| 原任务UL差异 | 1274.25 |
| 原任务DL差异 | 5830.33 |
| 总差异 | 42499.92 |

[RUN] 前两项占额外总资源**83.28%**；占paid-pose自身全部UL+DL资源**21.95%**。剩余任务流量差包含不同轨迹、选包、任务长度与等待的反馈，不应称为“摘要的间接因果开销”。不同seed方向不一致，原始每seed差异完整保留；不删除19000008的+111slot等不利结果。

## 3. 反馈时钟错配存在，不能把所有发送称作同代重传

[CODE] `receiver_rtt_contract.py:76`使用`next_retry=tx_slot+1+delay`。当前delay=0，RTO=1slot；但`paid_receiver_service.py:74`把正的CPU工作向上取整到slot边界。ACK的DL至少下一slot到达，再经0.001秒解码，实际至少再等一个边界。

[RUN] **4503条已收到的summary反馈全部为2slots，均晚于1slot RTO。** 这说明当前“RTT合同”仅包含传播下界，未与统一服务下的反馈处理时钟对齐。4503不是独立N，未收到反馈的attempt按丢失/截止保留，不推断其时延。

[RUN] paid-pose有4827次summary UL：4743次为该generation首次发送，84次为同代重试（46次edge前、38次edge后）。其中4500次新代首发及84次重试发生在至少一条先前反馈尚未被观察时。**多数是新generation，不是同代重复包**；仅报告lane.retries会漏掉反馈未闭环时的状态刷新负载，但不能把全部新代都判为可删冗余。

[RUN] 原任务edge已接受但发送者还未获得反馈的重传，消耗paid-pose任务UL的11.34%，public-ToM为12.19%；两arm均受影响。任务“首次edge成功→首次self ACK”p50/p90都为2slot，尾部paid最大29、public最大145slot；该口径含反馈丢失后等待再次成功机会，**不是某一帧的物理RTT**，不能归因CPU独占145slot。

[HYPOTHESIS] 因果可用的反馈等待/有界RTO可能减少部分流量，但是否损害摘要新鲜度和任务完成时间尚未验证。不得用未来实际ACK到达时刻设置RTO；也不因观察到2slot就静默改旧协议或宣称直接成本都能省掉。

## 4. 全历史重播占资源，当前队列却没有严重拥塞证据

[CODE] `paid_receiver_service.py:171`每5slot对`task_history.values()`全部重新排队，不依据接收者已知送达状态。只有融合层按(source,id)幂等，wire服务和接收CPU仍实际付费。

[RUN] 12个world合计：paid-pose task历史重播服务948824 DL uses，初始task广播51952 uses；历史重播占其**全部DL的77.46%**。public-ToM相应为890764/44448 uses，历史重播占全部DL的**92.60%**。task接收副本中重复项分别为52222/55233（94.55%）及47141/49650（94.95%）。这是“服务了大量已知副本”的证据，不证明能在不增加控制成本/丢状态风险的前提下免费去掉全部重播。

[RUN] 两arm DL从enqueue到首次服务的p50均0、p90均1、最大均3slots；当前没有“严重下行排队导致任务退化”的证据。**资源低效与排队拥塞要分开**。截止尚未完成的帧继续保留，DL只累计实际served uses，未把全部offered bytes都算已传出。

## 5. CPU模型有量化效应，不能当部署CPU时延结论

[CODE/RUN] 1秒slot内的0.001秒encode/decode在当前合同中都要到下一slot边界可见。所有记录job的ready-minus-submit为1slot；这不表示每个job独占一秒，也不能把所有job的rounding slack相加解释为mission总停顿，多job/多agent可以重叠。

[CODE] CPU job/工作秒是在入队时计账，包含截止尚未完成的job，不能称这些job全部已执行完毕；接收计数则只取实际处理完成事件。原模型该项计费约定未改。

[RUN] 12world的paid-pose含10197个pose编码job、9519个summary ACK解码job、8051个summary snapshot解码job，另有大量重复task解码；public也有50253个task解码job。工作量按显式CPU假设计价，但“1ms却增加一个slot可见延迟”的结果高度依赖时间离散约定。未实测部署slot/编解码/估值器时延，不能把本轮模型等同实际系统净收益。

## 6. 修订优先级与科学结论边界

1. **先统一反馈时钟合同**：UL、DL服务与CPU可见边界共同给出因果的RTO/等待规则；task和summary都审查，所有对照统一规则。固定slack或仅用历史反馈的自适应规则需事前规定；验证旧ACK/新代/超时和丢反馈，不从未来拿实际RTT。
2. **再审查盲目全历史catchup**：考虑有界窗口/预算或明确的接收状态反馈；若需要receiver ACK/位图必须真实编码、收费、丢失和排队，不能免费读取其他接收者状态。先验收状态可达性与右截断，再比较任务质量。
3. **明确CPU/slot时间约定**：按拟研究的真实slot尺度校准，或明确把理想与保守边界作为不同场景；不得把零CPU当测量值。估值器计算成本仍需分开测量并最终计价。
4. **暂不增加估值器复杂度/LLM/训练**：当前已证明接口确实改变值，缺的是这些变化能否在完整成本后产生净任务收益。修改服务后，重新冻结工作点/对照与独立校准，不沿用旧15419规划值，也不扩大旧test救结果。

[HYPOTHESIS] 上述是待审查的修订方案，不是已经验证的收益修复。没有paid-ignore固定前状态/同送达流的reward反事实，本轮不能把1.5slot退化分摊到同步、位置语义或ToM近似。原校准No-Go完整保留；P1历史cache/校准链缺口也未解决。

## 证据、命令与交付

- [任务brief](../logs/sync-cost-review-2026-10-23/task_brief.md)、[事前协议](../protocols/sync_cost_review_v1.json)。
- [最终合同JUnit](../sync/runs/hpc-sync-cost-review-contract-v2-20261023/outputs/pytest.xml)、[最终回放preflight](../sync/runs/hpc-sync-cost-review-replay-v2-20261023/outputs/preflight.json)。
- [最终诊断汇总](../sync/runs/hpc-sync-cost-review-replay-v2-20261023/outputs/summary.json)；同目录24个seed/arm JSON含逐UL attempt、逐DL frame、CPU分类、逐决策peer/双份value/双份selection与原result SHA/精确匹配标志。原校准目录只读。首轮hpc-sync-cost-review-{contract/replay/audit}-20261023同样保留，辅助same-generation计数不用作主证据。
- [最终独立算术审计](../sync/runs/hpc-sync-cost-review-audit-v2-20261023/outputs/audit.json)：重新读取旧结果和原SHA，验证24原结果、24UL/DL/CPU账本、3927决策不变量及主指标版本一致性；事件统计不是独立任务效应验证。
- [首轮完整回传](../sync/receipts/20261023T073207Z-edfad2.json)：all_outputs_mirrored=true，下载29291397bytes。最终v2回执另记于`research/logs/sync-cost-review-2026-10-23/delivery.json`；两端SHA校验，执行与同步完成分列。
- [最终v2完整回传](../sync/receipts/20261023T075044Z-1372cc.json)：all_outputs_mirrored=true，下载29327947bytes，最终逐决策/逐帧记录及审计均已回传并核验SHA。

```text
python scripts/sync_hpc.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-contract-20261023 --kind test ... -- env [数值线程1] timeout 120 {python} -m pytest -q tests_ext/test_sync_cost_diagnostic.py tests_ext/test_paid_receiver_service.py tests_ext/test_native_paid_adapter.py tests_ext/test_paired_paid_simulation.py ...
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-replay-20261023 --kind simulation ... -- env [数值线程1] timeout 360 {python} scripts/review_sync_cost.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-audit-20261023 --kind analysis ... -- env [数值线程1] timeout 60 {python} scripts/audit_sync_cost_review.py --replay research/sync/runs/hpc-sync-cost-review-replay-20261023/outputs
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-contract-v2-20261023 --kind test ... -- timeout 120 {python} -m pytest [同范围加新增针对性合同]
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-replay-v2-20261023 --kind simulation ... -- env [数值线程1] timeout 230 {python} scripts/review_sync_cost.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-sync-cost-review-audit-v2-20261023 --kind analysis ... -- env [数值线程1] timeout 60 {python} scripts/audit_sync_cost_review.py --replay research/sync/runs/hpc-sync-cost-review-replay-v2-20261023/outputs --prior-replay research/sync/runs/hpc-sync-cost-review-replay-20261023/outputs
python scripts/hpc_runs.py pull --max-bytes 104857600
```

精确argv/config/源码快照/环境/配额见各run manifest。首轮回放sync20261023T072557Z，首轮审计sync20261023T073058Z；最终合同sync20261023T073815Z、最终回放/审计sync20261023T073925Z，均0哈希差。本地仅编辑、Git/哈希/同步与看报告，未本地运行测试/分析。
