# GOSC 原论文—代码—数据—输出映射

核对日期：2026-10-19。代码 HEAD `876fc523b113b3b65e19f0b730f1573ccc2ee17f`；算法/实验/测试与上游整合基线 `387b493` 相同，本轮未修改。

[PAPER] 精确来源为本地 D01，题名 *Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams*；作者 Farhad Rezazadeh、Hatim Chergui、Lingjia Liu、Merouane Debbah。PDF metadata 为 arXiv:2609.39477v1，13 页；SHA-256 `e99130b27965bc4b6c06ccca8fc2dd9a3fd8b2dd5f6880964b6e0a4003c01923`。路径 `E:/Papers/99-附件/论文原文/D01-Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams.pdf`。以下页码为 PDF 物理页，不推断出版状态；PDF 保持只读且未上传。

[RUN] R2 的原始重建产物统一缩写为 `R2 = research/sync/runs/hpc-r2-20261019/outputs`；补表审计缩写为 `AUDIT = research/sync/runs/hpc-paper-audit-20261019/outputs`。映射不等于已重新运行所有原始 campaign，使用作者保存数据的环节明确标注。

## 五个编号公式

| 论文定位 | 内容与实现 | 数据/实验/测试证据 | 边界 |
|---|---|---|---|
| Eq.(1)，p3，§III-B | `gosc/agent.py:28 Agent.plan`：footprint mass、距离折扣、队友位置/意图 repulsion、hysteresis；`gosc/simulator.py:24 teammate_points` | Config 中 beta/sigma/h；原 R1 测试；所有 baseline 共用 planner | 微小随机 tie-break 与 hysteresis 是实现细节；LLM core 另见下方，不能称 Eq1 本身为 LLM 推理 |
| Eq.(2)，p3，§III-C | `gosc/channel.py:53 mean_snr`、`:60 success_prob`、`:85 decodes`：Rayleigh outage；FBL 为 `:27 fbl_error`、`:38 _fbl_success` | `tests/test_gosc.py:37` outage Monte Carlo、`:45` rate；`tests/test_revision.py:12/20/31` FBL；`results/snr.json` | 统计 CSI 默认，无实际无线设备；FBL 是 normal approximation，非完整 PHY |
| Eq.(3)，p4，§III-E | 任务时间/救援损失加无线成本的全局目标；`gosc/simulator.py:317 result` 给出任务与资源统计；`gosc/realistic.py:505 result` 扩展总成本 | `experiments/validate_headline.py` / `validate_realistic.py`；Table IV、IX–XI | 论文明确不求解全局 POMDP；不能把 myopic 调度称为全任务最优解 |
| Eq.(4)，p5，§IV-B；Appendix p12 | `gosc/voi.py:29 TeamModel`、`:97 _expected_utility`、`:105 evidence_voi`、`:122 intent_voi`、`:136 joint_voi`；`gosc/rescue.py:60 claim_value` | `experiments/diagnose_value.py`、`analyze_fidelity.py`、`run_joint.py`；`rev_value_fidelity/rev_fidelity_analysis/rev_joint.json` | sender belief 下评估 receiver 近似策略；默认不读取真实私有 belief。进入候选的负值截为0（`schemes.py:363`），不能声称真实因果下游收益标签 |
| Eq.(5)，p5，§IV-C | `gosc/schemes.py:251 Option`、`:260 Group`、`:266 lagrangian_select`、`:386 _options`、`:407 build_groups`、`:471 transmit` | `tests/test_gosc.py:63`、`tests/test_revision.py:128/141`；`experiments/analyze_scheduler.py:25 exact`、`analyze_theory.py:71 exact`；`results/theory.json` | 期望净值=payload value×成功概率−价格×ceil channel uses；预算松弛时有最优性结论，绑定时 greedy fill 不保证全局最优 |

## Algorithm 1、命题与定理

| 论文定位 | 代码对应 | 实证/适用边界 |
|---|---|---|
| Algorithm 1，p5，steps1–3 | `simulator.py:214 phase_decide` 更新LLR/自确认/计划；`schemes.py:341 on_step` 的 relevance filter 和 queued_llr | 不是训练流程；仅发送队列是统计候选，不等于每条观测必传 |
| Algorithm 1，steps4–6 | `schemes.py:407 build_groups`、`:266 lagrangian_select`、`:471 transmit` | CONF/INTENT/EVID groups，逐 rate 最长可装 prefix，40轮二分，剩余预算贪心填充 |
| Algorithm 1，step7 | `schemes.py:471 transmit` 的 acked_confirms/acked_intent/移除已送记录；`simulator.py:130 deliver`、`:167 _downlink` | HARQ ack 与 broadcast 分离；丢失/延迟 broadcast 不代表重发已 ACK 内容 |
| Proposition1，p4，§III-D | `simulator.py:114 local_llr`、`:130 deliver`、`:167 _downlink`，`gosc/belief.py:37 SensorModel.apply` | 理想广播为 Lc+pending_llr；非理想广播用各 agent 的 View/snapshot 与 inflight；R1 bookkeeping 测试已通过 |
| Theorem1，pp5–6，阈值/保护结构 | `schemes.py:386 _options`、`:266 pick`、channel Ps；`analyze_theory.py:80 run` | 固定 payload/price 的 decoupled rule；greedy fill 与可变 evidence prefix 需按论文限定解释；代码严格 `u>best_u` 保留首个等值选项，论文指定最大 maximizer，精确平局策略需另作边界检查，不将其掩盖为逐字完全同一 |
| Theorem2，pp5–6，松弛精确性/单消息gap | `schemes.py:266`，`analyze_theory.py:31 pick/:45 lagrangian/:71 exact` | `results/theory.json` 的12246/13125实例与 `R2/figures/numbers.tex` 的95.8/95.2% slack对应论文p6；本轮只核对保存数据，未重做30 missions×2 |
| Proposition2，p6，估值扰动 | `gosc/realistic.py:43 _estimate`，`analyze_theory.py` threshold/gap日志；`plot_realistic.py:101 noise` | common multiplicative factor 的有界命题与 unbounded lognormal / quantized / permuted 实验要分开；分析脚本文档写 Proposition3 是旧编号，当前PDF为 Proposition2 |

## 四条关键实现路径

1. **普通/理想模型**：`run_episode -> Simulation.run -> phase_decide -> phase_communicate -> GOSC.transmit -> GOSC.build_groups -> lagrangian_select -> Channel.decodes -> deliver/_downlink`。
2. **现实无线模型**：`gosc/realistic.py:530 run_realistic -> RealisticSimulation`，独立的 `RealisticGOSC.build_groups:84`、`_options:73`、`apply:153`；H、估值噪声、控制开销不能只改普通路径。
3. **共享上行**：`RealisticSimulation.phase_communicate:369` 分流到 `:429 _uplink_gosc_price` / `:403 _uplink_gosc` 或 `:483 _uplink_fifo`；`:325 waterfill`。default shared_mode=price；central 需上报更多options。price实现对过载指数使用 `min(demand/B-1,3)` 数值限制，论文p6给出的是简写公式，不能据此宣称字面完全一致。
4. **LLM**：`gosc/llm_agent.py:115 _candidates/:142 plan` 接收5个预处理候选并返回JSON字母；`:55 LLMClient.choose` 的cache key含model/prompt/labels。`experiments/run_llm_extended.py` 另有失败中止，不可由普通 LLMAgent fallback 推断 live 成功。

未来修改估值器时，必须同时核对普通 `schemes.py` 和现实 `realistic.py` 两份 group 构造与传输路径，并分别测试共享/非共享；不能把 ToM、TV、bits、AoI 或现有接收者模型记为本课题创新。

## 五张编号图

| 图 / PDF页 | 生成器与数据 | 精确对应的 R2 输出 | 本轮核对状态 |
|---|---|---|---|
| Fig1，p2，闭环系统框图 | 语义结构对应上述四条路径；不是统计曲线 | 无原脚本生成项 | 已核对节点、Q1–Q3、广播闭环；属于论文内架构图，不冒充缺失仿真产物 |
| Fig2，p7，救援frontier | `experiments/plot_revision.py:478 rescue`；`rev_rescue/filtered_periodic/suppress_periodic.json` | `figures/fig_rescue.pdf` | 三场景、saved%/uplink log轴、各价值曲线与periodic envelope及genie参考对应；第三子图minor log标签重叠已记录，未覆盖原PDF |
| Fig3，p9，估值误差 | `plot_realistic.py:101 noise`；`noise.jsonl.gz/validate_noise.json/rev_validation.json` | `figures/fig_noise.pdf` | 6场景、7估值档、log ratio、虚线1、hollow目标未达标记对应；数值支撑为TableVII |
| Fig4，p9，SNR双面板 | `experiments/plot.py:128 sweep_pair_plot`；`results/snr.json` | `figures/fig_snr_pair.pdf` | -10..20dB、均值CI、右侧log资源轴与genie不占无线资源对应；不要误取单图fig_snr.pdf |
| Fig5，p11，共享上行 | `plot_realistic.py:337 shared_column`；`shared.jsonl.gz`、`rev_genie_ref.json` | `figures/fig_shared_col.pdf` | 3个预算B=600/300/150，含请求开销、periodic最佳envelope、1.25Tg目标对应；fig_shared.pdf是额外宽版，非论文精确版式 |

## 十三张编号表

| 表 / PDF页 | 代码 / 输入 | 重建输出与核对范围 |
|---|---|---|
| I，p4，related-work taxonomy | §II相关工作；GOSC列对应上述闭环/估值/无线/LLM路径 | 静态文献定位表，无数值脚本；本轮核对GOSC列机制及引用编号，不冒称独立验证其余论文的全部创新性判断 |
| II，p4，消息长度 | `gosc/messages.py:14 cell_bits/:25 evidence_bits/:50 sem_step_bits/:55 raw_bits/:60 confirm_bits/:64 intent_bits` | AUDIT/static_and_frozen_checks.json；218、18、18、33+5P、evidence base34均核验；NL约1480为示例而非常数；单记录含1个检测实际39 bits |
| III，p7，默认参数 | `gosc/config.py:7 Config`；`run_revision.py:64` rescue显式覆盖deadline | AUDIT/static_and_frozen_checks.json：25项Config字段核验；1s为模型slot标度，无独立slot配置字段；救援60..180不是Config通用100..300 |
| IV，p8，主结果fresh验证 | `plot_revision.py:707 validation_table`；`validate_headline.py`、`results/rev_validation.json` | R2/figures/table_validation.tex：6行全部目标/结果/margin/资源/差分/ratio与印刷值一致 |
| V，p8，表示对比 | `experiments/plot.py:249 default_table`；`results/default.json` | R2/figures/table_default.tex：6行全部均值/CI/差分/载荷/资源/latency/false一致 |
| VI，p8，matched-budget估值 | `plot_revision.py:122 matched/:170 frontier_table/:190 where_tom/:787 merge_value_tables`；`rev_frontier/rev_where_tom.json`和`belief_divergence.jsonl` | R2/figures/table_values.tex初始缺5个belief-div.单元；须在隔离副本追加`python -m experiments.run_belief_divergence --table`；AUDIT/supplements/table_values.tex的10行40单元全部与论文一致 |
| VII，p9，估值精度 | `plot_realistic.py:101 noise`；保存noise/validate_noise/rev_validation | R2/figures/table_noise.tex：7×7单元与rho/CI/†一致；论文目标未达不能只用ratio称优势 |
| VIII，p10，ablation | `plot_revision.py:239 ablation`；`rev_ablation.json` | R2/figures/table_ablation.tex：两预算10行一致；相同price不等于相同实际资源，不能代替成本匹配实验 |
| IX，p10，开销ratio | `plot_realistic.py:180 overhead`；`validate_overhead.json`、rev_validation | R2/figures/table_overhead.tex：UL/UL+DL共12行，ratio/CI/†‡/only GOSC一致 |
| X，p10，总成本 | 同上，`realistic.py:505 result` | R2/figures/table_cost.tex：H0/H32共12行全部数值一致；GOSC H32的†与目标未达含义已读图核对 |
| XI，p12，共享上行 | `plot_realistic.py:264 shared`；`validate_shared.json`及shared原始结果 | R2/figures/table_shared.tex：4行含B150 target not reached一致；总成本含请求/grant/price broadcast |
| XII，p12，LLM POC | `plot_realistic.py:378 llm`；`llm_mixed/llm_extended.jsonl` | R2/figures/table_llm_extended.tex：11行全部统计一致；只是作者已保存LLM结果重分析，未replay/live |
| XIII，p12，冻结点 | `plot_revision.py:707 validation_table`；`rev_validation.json` | R2/figures/table_frozen.tex与AUDIT六组scheme/eta/k/theta检查一致；新的37/38候选族差异另见审计报告 |

## 结果可追溯性与尚未完成范围

[RUN] 本轮 `hpc-paper-audit-20261019` 对405个数值/区间/标记单元作校验；原表8/9全匹配，剩余表VI补齐后匹配。`hpc-r4-preflight-20261019` 核对保存候选seed集合与生成器。普通R2的三个summary匹配并不自动保证表VI已经补齐。

[CODE/RUN] 原主结果搜索候选是37个（4 unfiltered + 5 filtered + 28 suppressing），救援是38个；`run_realistic.PERIODIC`为38。不得混称所有场景均枚举38，严格复现与补候选敏感性实验分轨。

未进行新多seed仿真、校准过程重跑、live/cached-LLM任务执行、理论证明的独立形式化验证或新方法训练。17张PDF中有13张是额外/替代图，不应写成论文有17张编号图。映射已覆盖所有编号项目，但文献表跨论文判断及显示/边界差异保持显式开放。
