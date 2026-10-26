# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 摘要费用哪些可精确识别，age是否主要改变有效价格？[RUN/CODE] 当前证据支持优先分离“本地age调价”与“付费时间戳/位置内容”，不支持直接扩N或复杂训练。未新跑任何任务仿真。
- **已核验前人工作**：[PAPER] 本轮未新增论文原文或出版状态核验；沿用纸码映射和前一份GP-v2校准审计。这里是本仓库机制分析，不是动态定价/语义价值的新颖性证明。作者原校准/cache生成链/历史数值差异仍单列未解决。
- **实际阅读源码**：[CODE] 基线47389eba9c6e2838139df3aa47863ab88634e97a、dirty源码按原frozen SHA核验。`causal_paid_simulation.py:23/31/41/55`的eligibility/public view/age缩放，`schemes.py:266/277/289`的price目标与40次二分；`receiver_summary_audit.py:14`编码；`receiver_transport_replay.py:9/25`反馈/快照帧；`paid_receiver_service.py:74/92/108/151/186/190` CPU、摘要提交、所有receiver解码、ACK/快照入队；`repro_causal_service.py:100`导出字段范围。未改gosc或冻结extensions。
- **本轮新增或修改**：[CODE] `review_summary_age.py`纯现有数据分析/固定选择器诊断；`audit_summary_age_review.py`独立算术/原始事件核对；18项`test_summary_age_review.py`；事前`summary_age_review_v1.json`、本报告和`summary_age_revision_review_2026-10-25.md`审阅候选。未写新任务策略。
- **实际运行**：[RUN] HPC n1、Python3.11.15、单worker/数值线程1，2CPU/24GiB配额；18合同通过；原252结果/950281事件分析，两版输出保留，最终版收紧不买摘要分支的DL上界为已知0、补充编码生成预留诊断。固定128个合成候选目录×4factor×3price=1536次选择器比较，0 signature不一致；不是1536个mission或新独立N。
- **测试与结果**：[RUN] 理想目标缩放、反馈header/分批/censor费用界等18合同通过。独立复算252个任务的UL/DL界与汇总、固定轨迹费用敏感性；未重跑原190测试，不能将旧证据合并成本轮新测试。详细命令/数据SHA在各manifest、review.json和本任务actual_commands.json。
- **失败/负面证据**：[RUN] 本轮无新增mission/训练/正式test、无软件失败；旧No-Go原样保持。缺失历史DL类型、逐决策age factor/候选，不能报告伪精确DL构成或实际effective-price分布。合成选择器0不一致不是普遍逐位等价证明；实际age price0与public price0在2/12world的curve不同，也不能单凭该差异归因浮点。
- **与原GOSC的差异**：[CODE] 审查的是本项目GP-v2服务和原ToM/选择器复用路径，非作者旧wire精确复现或真实LLM收益。原`realistic.py`/`schemes.py`实验实现未修改；本轮没有新closed-loop结果。
- **公平性与泄露检查**：[RUN] 输入仍是已曝光12world的21候选；新独立N=0。原方法/配置/decision SHA未变，预留test未执行。纯分析不将原数据改称新校准或验证；账本删费只是假设费用核算，不改原资源值或宣称任务因果不变。新协议只是review_candidate，不赋予新执行授权。
- **成本**：[RUN] 合同1.167857s（pytest0.30s）；首版分析3.516355s、最终分析3.316556s；独立复算另登记。0GPU/0新LLM/API/token调用/0训练。本地仅文档/Git/轻量哈希与同步，所有合同、统计和数值诊断均在HPC。
- **可否进入下一阶段**：现有协议正式test/扩N/训练仍 **No-Go**；审查交付可Go。新协议 **Pending / review_candidate_not_executable**，尚无新world/N/执行预算。
- **用户需要批准的下一步**：本轮审查交付无需新增批准；建议先审阅最小native-age/显式动态price对照和前瞻观测合同，决定后再实施，不直接扫参/做下一收益campaign。

## 摘要成本：精确项、可证明界、未观测项

[RUN] 下表为选中`pose_p0.0001`的12world均值；channel uses均含当前wire/CRC/重试的实际计费口径。

| 项目 | 均值 | 证据边界 |
|---|---:|---|
| 全通信 | 59,857.75 uses | 原UL+DL实际服务账本 |
| 摘要UL | **20,516.00 uses，34.27%全通信** | 427.4167次×6bytes×8bits/rate1；精确 |
| 任务UL | 14,026.08 uses | 总UL减精确摘要UL |
| 全DL | 25,315.67 uses | 精确，但旧日志缺frame kind映射 |
| 摘要DL | **[4,564.67, 19,365.33] uses** | 可证明的保守识别界，非置信区间或精确拆分 |
| 摘要直接UL+DL | **[25,080.67, 39,881.33] uses，即[41.90%,66.63%]全通信** | 同一账本的保守界，不是相对baseline增量的因果占比 |
| 任务历史重播DL | 3,427.33 uses | 原replay offer bytes与mission末未服务账本推得；本组DL未服务量0，故界重合为实际服务量 |

[CODE] pose app4bytes、CRC2bytes，所以独立UL每帧6bytes。summary ACK批为`4+2m`bytes，snapshot为`4+4k`bytes；在DLrate2下分别为`16+8m`和`16+16k`uses。消息丢失仍收费；不能通过删除CRC、头或ACK成本宣称原协议变省。

[CODE/RUN] ACK下界来自M次摘要UL必入队反馈、每批最多6项：offered至少`8M+16*ceil(M/6)`uses；扣除整个DL尚未服务工作量，得到已服务ACK保守下界。上界从全DL扣去可证明的任务初传/最小ACK/重播已服务下界。没有DL kind，所以不能把上界当实际摘要费。旧成本界首版对不购买摘要分支过松，最终版用代码证明其摘要UL/DL恰为0；原始结果和首版均保留。

[RUN] 选中pose的12mission在截断时已提供DL帧的未服务工作量均为0；仍可有传播/CPU未完成及receiver丢失，不等于每个peer已收到，也不证明过程中无排队。新GP-v2不能继续引用旧GP-v1“paid DL77.46%历史重播”作为本批解释；版本和world均不同，不能把两版差值写成修订的因果效果。

## CPU：生成编码、实际UL和接收处理要分开

[RUN] 选中pose每mission平均843.25个摘要编码预留作业、427.4167次摘要UL尝试。至少415.8333个生成预留在任务截断前不能对应不同的UL尝试；可能等待/过期/合并取代或pending，不全等于可无代价取消的无用工作，重传也使真实未尝试生成数可能更多。

| 逻辑CPU预留项 | 均值秒 | 边界 |
|---|---:|---|
| 摘要编码 | 0.84325 | 包含已预约但未必完成/发送的生成作业 |
| 所有估值admission | 0.41517 | 固定每次.001s的场景假设 |
| 所有received解码 | 1.96000 | 未记录task/summary/ACK类型，不能全部算摘要 |
| 逻辑CPU总预留 | 3.24167 | 不等于mission elapsed或硬件CPU时间 |
| 实测mission process / selection process | 4.09484 / 3.69051 | 另口径；selection计时不包含valuation_view投影的全部开销 |

[CODE] 当前广播对所有6个receiver排解码作业，ACK最终仅对应source更新状态；这是潜在优化点，不是已实测可省掉的全部解码。地址识别/CRC/头解码仍有成本，不能免费跳过所有非目标处理。延后编码/合并也必须保留因果生成时间、TTL和失败风险。

## 仅把摘要UL变便宜还不够

[RUN] 在**固定当前任务轨迹、其余费用不变**的账本敏感性核算中：

| 不付费对照 | 允许通信上限（1.05×对照） | 当前pose需减少 | 全通信需降比例 | 删去全部摘要UL后 |
|---|---:|---:|---:|---:|
| periodic k8/eps0 | 39,118.71 | 20,739.04 | 34.65% | 39,341.75，仍超上限 |
| selected public | 20,821.76 | 39,035.99 | 65.21% | 39,341.75，仍超上限 |

这是费用敏感性，不是实现了免费UL、捎带或相同任务结果的新协议。它既不保证降低服务成本后收益保持，也不证明所有更便宜协议不可能成功；当前数据不能据此放行新campaign。

## age机制：确实是动态price，尚未证明买来的信息必要

[CODE] age从本发送者可见的native时间戳或已实际收到、有效且更新的摘要时间戳计算`mean_age`，不改位置视图，然后将CONF/INTENT/EVID的全部Option.value同乘

`f = 1/(1+mean_age) > 0`。

原选择目标`sum(V)-p*C`变为`f*sum(V)-p*C`；除以f，理想最优集等价于原ToM值搭配

**`p_eff = p/f = p*(1+mean_age)`**。

这保留同决策候选价值的相对排序，主要改变是否值得付费发送/预算权衡；不是消息特异的语义价值重估。时间戳仍是信息，其是否值得购买必须另作对照，不能说“age不需要信息”。p=0时理想目标仅整体缩放，不代表实际闭环必然完全相同。

[RUN] 18项合同包括可行集合目标排序的穷举小例子；固定128合成目录、4factor、3price的1536次数值选择器比较全相同。有限样本不构成普遍逐位等价证明；原选择器有40次二分、浮点/破同分及贪心补充。

[RUN] 原age_p0与public_p0的任务curve在10/12world相同、2/12不同；这些arm还有是否付费摘要及CPU服务的差异，没有paid-ignore price0，也没有predecision factor/候选日志，不能单凭差异归因浮点或age语义信息。

原paid-age虽表现更好，但**native-age（只看实际native EVID时间戳，不购买摘要）/显式native动态price对照尚未运行**。缺少这项不能回答购买摘要时间戳是否必要；不事后替换主方法或立即扩样本。

## paid-ignore检查及仍缺的历史观测

[RUN] 在price1e-5的12对world中，paid-ignore/public的已登记任务字段（完成/发现/curve/false declaration/确认latency）、task尝试日志、任务编码CPU日志、重播offer日志与task UL总bytes全部一致。付费摘要在这些已记录任务口径下没有改善结果，却增加账本。它是控制路径的有用一致性证据，**不证明未记录的payload、DL成功或所有receiver私有轨迹逐位相同**，也不把全部DL差值冒称精确摘要分类。

现有导出没有DL enqueue kind/wire映射、CPU received kind、每次age因子/时间戳来源、基础候选/选包signature。实际p_eff分布、精确摘要DL/解码占比、age优势的信息/动态价格归因目前均**未核验**；本轮没有重仿真伪造这些历史字段。

## 审阅建议与交付

优先顺序是：先给出native-age/显式动态price的最小强简单对照；再用前瞻观测合同分开时间戳信息、位置内容与付费服务；然后才讨论可真实计价的延后编码/合并/捎带/控制反馈优化。具体审阅候选见`research/protocols/summary_age_revision_review_2026-10-25.md`，不是已冻结实验或授权。

证据run：`hpc-summary-age-contract-20261025`、`hpc-summary-age-existing-data-review-20261025`、`hpc-summary-age-existing-data-review-v2-20261025`、`hpc-summary-age-review-audit-20261025`、`hpc-summary-age-review-audit-v2-20261025`。最终以v2 review.json、selector_diagnostic.json、input_event_hashes.json和v2独立audit.json为准；最后独立审计重新解析252个事件文件，核对原始UL/DL、重播bytes、CPU action及其预留秒，2.496631s通过（先前纯算术/哈希审计0.133076s也保留）。精确命令、receipt与源码/输入SHA在`research/logs/summary-age-review-2026-10-25/`。本轮无新mission、新独立N、正式test、训练、Git提交或push。

[RUN] 最终回传receipt `research/sync/receipts/20261025T140226Z-a6af80.json`确认all_outputs_mirrored=true；首次新增86,886,719bytes，最终补拉21,587,725bytes（均含运行源码快照/补丁等管理产物，不是仅分析JSON大小），HPC原件保留。实际命令与配置/source_sync身份已汇入本任务`actual_commands.json`，最终两端报告/源码SHA交付记录为`delivery.json`。
