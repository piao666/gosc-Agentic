# Research Task Report — 同格式 periodic / CRN 与独立校准

- **Research Question / Hypothesis**：[HYPOTHESIS] 在相同GP-v1消息格式、付费UL/DL/CPU服务和外生随机场下，pose估值刷新能否超越有限候选族中选出的简单对照，并支持可负担的一次验证？
- **已核验前人工作**：本轮未新增PDF全文阅读/新文献主张。[CODE] 原仓库已有SemanticAggregated、SemanticRateAware、Filtered/Suppress；本轮承接其聚合、语义过滤、周期与goodput适配机制，不宣称首次提出这些思想。
- **实际阅读源码**：[CODE] base `4ff4147654c07781d77a42acee3f31c0b8792f38`，`gosc/schemes.py`上述periodic类及GOSC.on_step/lagrangian_select、`channel.py`success_prob/decodes/fbl_error、`simulator.py`初始化/phase_decide/result；读取既有paid service、GP-v1、pose投影和历史event-index诊断。原生/realistic平行路径映射沿用前序报告，本轮不扩展到realistic/shared/rescue/LLM。
- **本轮新增或修改**：新增`extensions/wire_periodic.py`、`paired_paid_simulation.py`、`tests_ext/test_paired_paid_simulation.py`、`scripts/repro_periodic_calibration.py`、`audit_periodic_calibration.py`、事前JSON及brief；`native_paid_adapter.py`仅增加选择与物理噪声hook，默认行为保留。更新研究入口/状态/下一步。未修改原gosc、experiments、tests、results或LICENSE；没有Git提交/推送。
- **实际运行**：[RUN] HPC `n1`、UID8301880、项目`.venv/bin/python`3.11.15；2CPU/24GiB，单进程、单数值线程。合同v1/v2失败保留，v3通过；world冻结、成本probe、独立calibration和独立产物算术审计均已完成。精确argv、源码快照、sync SHA、环境、每个seed和退出码见下列manifest/status。
- **测试与结果**：[RUN] **156 passed in33.82s**（85原生+26 pose/RTT+17服务+17原生适配+11新增）。新合同含周期准入/立即CONF、FIFO真实prefix与rate/预算、无关随机流消费、重叠感知footprint、FBL/DL可复现、完整短任务重复、全丢DL无免费状态/ACK等。成本probe24条/2world，独立calibration144条/**12world**全部完成，各候选12/12任务成功；不可把144当独立N。独立审计退出0，通过配对、成本/选择/N公式和停止门槛核验。
- **失败/负面证据**：[RUN] 合同v1/v2各155通过/1失败。最初夹具隐含“初始EVID未过滤且有剩余容量”；显式隔离后又审查短INTENT选率，将原来的最大成功概率改为有效bits/channel-use，保留失败run，不弱化过滤/预算。独立校准触发预设No-Go：付费pose两个主要比较的平均任务改善均<=0且成本比>1.05；规划N15419超过200world上限。
- **与原 GOSC 的差异**：[CODE] 共用新GP-v1无损语义格式及服务，非作者SEMA/fragmentation或历史wire精确复现。periodic按`(t+1)%k==0`准入INTENT/EVID，CONF严格优先，FIFO EVID取可装前缀，按实际n最大化有效bits/channel-use；共享原语义过滤，重传不受准入周期限制。没有用弱固定速率periodic替代原强对照；但只审查本轮冻结的有限候选族，不能称全局最强。
- **公平性与泄露检查**：[RUN/CODE] 事前冻结12候选与214world指纹；131份登记manifest/协议/原pool参数/selection/pilot结果清单扫描，无seed冲突。2probe、12calibration和200预留test世界互斥；原split、旧pilot/合同域排除。seed扫描是保守整数匹配，指纹仅覆盖已登记且可发现的历史记录，不能排除未登记外部实验/未记历史指纹。预留world只初始化身份，**test任务0次**。所有arm共用Planner、候选语义、wire、每Agent UL100/共享DL2000、服务规则；pose只进实际送达cache的估值副本。相同W并不代表实际成本匹配，本轮没有完整配对成本前沿/估值硬件CPU测量/age-shuffle等消融，不作纯信息因果或部署净收益结论。
- **成本**：[RUN] 成本probe wall2.132627s；线性外推加2倍余量358.630398s，低于事前480s门槛；独立calibration wall160.674965s、child CPU user160.069341/system0.303560s、maxRSS68288KiB，低于600s硬上限。合同v3 wall34.309335s；world冻结2.236653s；独立审计0.286694s。包括runner子进程，非模型独占峰值；0新LLM/收费API/下载/训练，未测助手tokens和GPU峰值。
- **可否进入下一阶段**：**Go：同格式periodic/CRN实现、HPC合同与独立calibration交付。No-Go：当前设定的正式收益验证和复杂训练。** 已冻结的是负结果与停止判决；**没有冻结可执行的最终N/验证预算**，不能把15419解释为应追加的样本数。
- **用户需要批准的下一步**：本阶段已授权工作完成。后续若要改变价格、CPU/DL设定、协议或任务，应先解释本次负结果并另立有界设计；不自动换任务、扩N或付费调用。当前只建议先审查已有账本的同步/下行/等待成本及估值实际改变率，不能从这一小校准断言pose状态普遍无价值。

## 校准结果与停止判决

[RUN] 同一12个新world。T为固定400slots下的完成时间（失败原定计400；本轮各候选均12/12完成）；资源为各任务实际UL+DL channel uses总量。选择规则在结果前固定：从bits、AoI和8个periodic设置中取平均T最小者，成本与id破同分。选中`periodic_k8_eps0.0`；`eps0.02`在本轮12个world的结果相同，不视为额外独立重复。

| 校准arm | 平均T / slots | 平均UL uses | 平均DL uses | 平均总uses | 模拟编解码CPU秒 |
|---|---:|---:|---:|---:|---:|
| 选中periodic k8 / eps0 | 141.6667 | 42498.6667 | 70557.0000 | 113055.6667 | 5.3240 |
| public-ToM | 144.0000 | 38556.9167 | 80161.0000 | 118717.9167 | 4.5357 |
| paid-pose | 145.5000 | 59139.1667 | 102078.6667 | 161217.8333 | 7.3851 |

[RUN] 全12候选结果均在decision.json，未删除不利的bits/AoI/其他periodic结果。只列三arm便于阅读，不意味着只运行这三项。

| paid-pose 相对对照 | 对照T−poseT（正为改善） | 探索性95%配对bootstrap CI | 平均成本比pose/对照 | 探索性95% CI |
|---|---:|---|---:|---|
| periodic k8 / eps0 | -3.8333 slots | [-48.0000, 37.0833] | 1.426004 | [0.953819, 2.213220] |
| public-ToM | -1.5000 slots | [-29.3333, 23.2500] | 1.357991 | [1.112426, 1.787666] |

[RUN] 这些CI仅为小样本校准描述，**不是正式多重校正验证，也不是显著变差/普遍无效的判决**。No-Go使用事前可行性停止规则：均值无任务改善且成本>1.05。选中的baseline来自本calibration，不能以其校准优势冒称独立验证。

[RUN/HYPOTHESIS] N规划按两个主要比较×两个端点Bonferroni（单侧alpha0.0125），联合功效目标0.8对应各端点0.95；任务门槛3slot、设计备择6slot，成本比门槛1.05/备择1。用20000次bootstrap的SD95%分位与观测SD较大者作规划量、正态近似计算，非保证功效：periodic比较N_task15419/N_cost5515，public-ToM比较6446/1948。最大15419远超事前200上限，因此`executable_test_N=null`、`test_seeds=[]`、最终验证预算null，不运行test、不事后调小门槛或加样本。

## 服务/随机场范围与替代解释

[CODE/HYPOTHESIS] 场景时钟是明确假设：slot1秒、编/解码各0.001秒，CPU就绪按slot边界向上取整，非硬件时延测量；UL100 uses/agent、DL2000 uses/slot、DL rate2、额外delay0、接收者独立丢失0.05、TTL20、历史catchup5。CPU秒是模拟编解码服务总量，未将估值器实测CPU成本完整折入任务slot；算法wall另报，不作部署净收益主张。

[CODE] 感知用(seed,201,t,agent,globalcell)潜在均匀场；fading域202，Planner域203，FBL域204，DL域205。FBL按slot/sender/kind/完整wire hash，DL按到达slot/receiver/kind/完整wire hash；不同排队id/不同内容可能对应不同hash，不承诺所有相似语义packet共享同一随机数。不同策略的路径损耗、收到的内容和动作仍可不同；这是共同外生场耦合，非强制轨迹相同，也非作者原随机流复现。主calibration使用默认outage；FBL仅合同验收，不推广效果。

[RUN] paid-pose平均摘要UL2413.5bytes，终点存储cache条目合计均值36（含self/可能陈旧项）；平均待服务DL4.9167帧。终点cache非空证明摘要经过服务后到达过，不证明每次估值都用了有效更新，不能据此归因负结果。历史重播、优先级、CPU量化和队列路径可能影响成本/任务；尚未识别单一原因，未用新结果反向修改协议。

## 冻结文件、原始证据与命令

- [事前协议](../protocols/periodic_crn_stage_v1.json)、[任务brief](../logs/periodic-crn-2026-10-23/task_brief.md)。
- [合同v1失败](../sync/runs/hpc-periodic-crn-contract-20261023/stdout.log)、[合同v2失败](../sync/runs/hpc-periodic-crn-contract-v2-20261023/stdout.log)、[v3 JUnit](../sync/runs/hpc-periodic-crn-contract-v3-20261023/outputs/pytest.xml)。
- [world/source事前冻结](../sync/runs/hpc-periodic-world-freeze-20261023/outputs/frozen.json)，含具体case配置/源码SHA/214world指纹/131清单哈希。
- [probe预算](../sync/runs/hpc-periodic-cost-probe-20261023/outputs/budget.json)、[24条原始结果](../sync/runs/hpc-periodic-cost-probe-20261023/outputs/results.json)。
- [校准全部结果](../sync/runs/hpc-periodic-independent-calibration-20261023/outputs/results.json)、[判决与全候选汇总](../sync/runs/hpc-periodic-independent-calibration-20261023/outputs/decision.json)；同目录每seed/candidate独立JSON保留原curve/成本/右截断队列/指纹/运行成本。
- [独立产物审计](../sync/runs/hpc-periodic-calibration-artifact-audit-20261023/outputs/audit.json)。这是另一脚本的算术/配对审计，不是另一研究者重新执行实验或独立作者复现。
- [完整回传回执](../sync/receipts/20261023T070802Z-44cd7f.json)：all_outputs_mirrored=true，新增下载15015591bytes，各文件SHA核验通过；包含本轮失败/成功记录与全部原始输出。
- 各run同目录`manifest.json/status.json`为执行权威；回传与最终文档交付见`research/logs/periodic-crn-2026-10-23/delivery.json`，不得用执行退出0代替两端同步完成。

```text
python scripts/sync_hpc.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-periodic-crn-contract[-v2/-v3]-20261023 --kind test ... -- env [数值线程1] timeout 300 {python} -m pytest -q tests [前序合同及test_paired_paid_simulation.py] ...
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-periodic-world-freeze-20261023 --kind analysis ... -- env [数值线程1] timeout 120 {python} scripts/repro_periodic_calibration.py --mode prepare
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-periodic-cost-probe-20261023 --kind simulation ... -- env [数值线程1] timeout 120 {python} scripts/repro_periodic_calibration.py --mode probe --frozen <freeze-output>/frozen.json
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-periodic-independent-calibration-20261023 --kind simulation ... -- env [数值线程1] timeout 600 {python} scripts/repro_periodic_calibration.py --mode calibrate --frozen <freeze-output>/frozen.json --budget <probe-output>/budget.json
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-periodic-calibration-artifact-audit-20261023 --kind analysis ... -- env [数值线程1] timeout 60 {python} scripts/audit_periodic_calibration.py --frozen ... --probe ... --calibration ...
python scripts/hpc_runs.py pull --max-bytes 104857600
```

上列缩写用于阅读，精确命令以各manifest argv为准。运行源码sync20261023T070146Z（合同最终版sync20261023T065947Z），均0哈希差；独立审计脚本增补sync20261023T070706Z。原有未提交文件全部保留；GitHub未更新。研究关卡现在是审查负结果，而非已经获准训练/投稿。
