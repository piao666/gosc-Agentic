# Research Task Report

**[RUN] 已完成1200次独立接收端诊断。未确证稳定且实用的接收端状态收益，不能据此宣称发现可支撑新方法的代表性性能缺陷。也没有证明receiver state无效。**

- **Research Question / Hypothesis**：[HYPOTHESIS] 固定原ToM、Planner、scheduler/channel与eta，分别开放receiver私有证据或真实位置，能否在default/W50/snr-5三设置稳定缩短任务时间至少5%？joint与交互为次要。
- **已核验前人工作**：[PAPER] 沿用此前D01 *Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams*，arXiv:2609.39477v1，p.8 Table VI、p.11私有信息对照的核验；本轮未重新精读PDF或核验发表状态，无新增文献/新颖性主张。[CODE] 原run_revision.experiments已含shared/joint oracle，两因素拆分不是作者已有对照缺失的证明。
- **实际阅读源码**：[CODE] 上游387b49389385b51c275dc5a22ec1672087edda1d；执行与冻结分析commit 491b1878dfc50a439c055703f598212862079bfc。gosc/voi.py TeamModel.__init__/_belief_mass/_expected_utility（29–105行）；gosc/simulator.py Simulation.__init__/phase_decide/phase_communicate/result；gosc/config.py；extensions/receiver_oracle.py model_factory/receiver_oracle；experiments_ext/campaign.py diagnostic_jobs/_job、run_receiver_factorial.execute、receiver_admission.verify_admission、summarize.diagnostic/paired/plots。所有代码位置以本次commit核验，不将代理效用称为真实任务效用。
- **本轮新增或修改**：显式限定准入验证/runner及门控测试、批准绑定记录、冻结准入协议、brief；继续任务新增receiver_report证据导出器、本报告/CSV/图/manifest/证据索引与日志。原gosc/experiments/tests/results/cache/License与Obsidian未改，adapter和冻结summarize未改。
- **实际运行**：[RUN] 2026-10-15执行3设置×4模式×100 seeds4000–4099，1200次纯Planner；2026-10-16继续校验及一次冻结统计。完整命令见command_ledger.json；零重跑mission、零模型/依赖下载、零LLM调用。
- **测试与结果**：[RUN] 运行前契约/门控11 passed in6.04s；完整105 passed in47.77s（两个独立调用，不能相加为116个独立测试）。继续任务未重复执行测试；仅导出器为后加报告工具。原始1200条身份/配置/seed/有限值/400步curve与哈希核验通过，3×4组各N100。全部任务找到8个目标，false declarations合计45，均保留。主分析6项family CI全跨零，0项下界>5%阈值。
- **失败/负面证据**：[RUN] default/private的未校正95% CI为[0.45,11.82] slots，校正后[-1.41,13.92]，不能只摘录前者。W50/position点估计慢3.23 slots，但区间跨零，不能称确证伤害。joint三个设置与交互CI均跨零。所有6项family上界仍高于5%阈值，不能排除有实际收益，也不能宣称统计等价。[RUN] 原strict R4失败、R4-S1四项不确定均原样保留。
- **与原 GOSC 的差异**：只改变TeamModel可见状态的诊断view；shared与joint对应原tom_oracle False/True，新增private/position两个mask。未实现新估值器、改变真实Agent行为规则、scheduler或channel；不存在可投稿方法贡献的既定结论。
- **公平性与泄露检查**：相同mission seeds/初始世界/随机流生成、原配置/每时隙资源；轨迹分叉后观察/候选消息会内生分叉，不是每次通信前同状态的deliver/drop反事实。4000–4099未用于训练/调参，也未替换原eval/calibration。共享资源参数shared_budget=0，即正交上行，不能外推网络共享调度。oracle显式使用当前私有状态、未使用未来奖励；访问/同步免费且不可部署，固定eta不保证实际UL/DL成本匹配。
- **成本**：[RUN] 仿真墙钟730.807s（12.18min），4workers，每worker1数值线程；mission墙钟求和2916.455s，仅为并发任务耗时求和、不是测得CPU时间。raw 2,086,897字节。测试/分析/报告另计；无GPU/收费API/LLM。无线bits是模型payload、不是实测序列化字节；packet-success、tokens、CPU/RAM峰值、估值器分项耗时未测。
- **可否进入下一阶段**：**No-Go for方法开发/收益主张；Pending for接收端假设。** 已批准的Receiver-D1执行和证据归档完成；总体R4仍未通过。不能用“执行passed”覆盖科学假设不成立/未确证的边界。
- **用户需要批准的下一步**：建议先审查估值代理与真实Planner行为的机制差异，起草同决策前状态、匹配外生随机流的离线反事实小实验与成本口径，再决定是否值得开发M0。此为[HYPOTHESIS]后续研究建议，尚未执行；不因本轮弱信号自动扩seed、改任务或增加模型。作者环境询问仍为未发送草稿。本轮到此停止。

## 1. 六个主要比较

[RUN] 正收益=shared completion_time−intervention completion_time，单位slots；百分比=均值差/shared均值。N=100 paired missions每模式。统计seed0，paired bootstrap4000，六个private/position比较用Bonferroni6 percentile区间（family近似95%；单项约99.167%）；4000次的极端尾部仅约17个重采样，存在Monte Carlo误差，不声称精确覆盖。5%阈值相对于观察到的shared样本均值固定；百分比为点估计，未给独立比率CI。正/负/零seed指任务时间差的方向。

| 设置 | 干预 | 收益slots | 收益% | 未校正95% CI | family CI | 5%阈值slots | 正/负/零seed |
|---|---|---:|---:|---|---|---:|---|
| default | private | +6.16 | +8.48% | [0.45, 11.82] | [-1.41, 13.92] | 3.631 | 54/45/1 |
| default | position | +2.25 | +3.10% | [-3.38, 8.13] | [-4.83, 10.30] | 3.631 | 44/50/6 |
| W50 | private | +0.59 | +0.74% | [-8.60, 9.57] | [-11.98, 12.65] | 3.973 | 51/44/5 |
| W50 | position | -3.23 | -4.06% | [-11.37, 5.13] | [-14.39, 7.34] | 3.973 | 46/51/3 |
| snr-5 | private | +0.87 | +0.87% | [-10.72, 12.96] | [-15.17, 16.42] | 4.998 | 49/49/2 |
| snr-5 | position | +3.09 | +3.09% | [-7.01, 12.86] | [-10.32, 17.32] | 4.998 | 49/45/6 |

[RUN] 点估计≥5%为1/6；family下界>0为0/6；family下界>5%为0/6；family上界<5%为0/6。private或position均未满足“三设置family下界均>5%”的冻结稳定实用标准。这是证据不足，不能推断因果效应为零或永远无法提升。

## 2. 全部模式的任务和资源分布

[RUN] completion_time均值的区间为正态近似边际95%，不用于主要显著性判断；Q25/median/Q75为样本分位数。statistics.json保留各指标N/均值/分位数/正态区间半宽；其mean_ci_normal95字段是半宽，表中已转换为端点。所有组completed=1.00，不把45次false declarations隐藏在完成率后。6 agents、32×32、8 victims、search、horizon400；default W100/SNR+5dB，W50 W50/+5dB，snr-5 W100/−5dB；原eta1e-5。

| 设置 | 模式 | N | 时间均值 | 均值边际95% CI | 时间Q25/median/Q75 | UL uses均值 | 记录DL uses均值 | payload bits均值 | false declarations均值 |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| default | shared | 100 | 72.62 | [66.96, 78.28] | 53.00/64.00/90.25 | 12246.33 | 3425.35 | 12058.35 | 0.04 |
| default | private | 100 | 66.46 | [61.76, 71.16] | 50.50/62.00/80.00 | 12566.70 | 3412.00 | 11841.00 | 0.02 |
| default | position | 100 | 70.37 | [65.23, 75.51] | 53.75/65.50/80.25 | 11864.15 | 3356.76 | 11955.75 | 0.01 |
| default | joint | 100 | 71.22 | [64.78, 77.66] | 49.75/61.00/83.25 | 12507.00 | 3419.63 | 12278.05 | 0.03 |
| W50 | shared | 100 | 79.46 | [72.37, 86.55] | 51.75/71.00/93.00 | 7530.84 | 2714.10 | 10190.42 | 0.04 |
| W50 | private | 100 | 78.87 | [71.29, 86.45] | 52.00/64.00/99.00 | 8033.20 | 2832.46 | 11022.75 | 0.06 |
| W50 | position | 100 | 82.69 | [75.66, 89.72] | 56.00/79.50/100.00 | 8089.72 | 2955.67 | 11129.92 | 0.05 |
| W50 | joint | 100 | 78.33 | [70.24, 86.42] | 54.25/67.50/91.25 | 8015.03 | 2808.90 | 11035.41 | 0.05 |
| snr-5 | shared | 100 | 99.96 | [89.88, 110.04] | 63.00/80.00/130.25 | 11997.26 | 1388.40 | 5744.93 | 0.03 |
| snr-5 | private | 100 | 99.09 | [90.72, 107.46] | 71.75/90.50/126.75 | 11499.18 | 1490.41 | 6153.44 | 0.03 |
| snr-5 | position | 100 | 96.87 | [88.06, 105.68] | 62.50/91.00/124.50 | 13167.78 | 1577.18 | 6734.42 | 0.05 |
| snr-5 | joint | 100 | 97.50 | [87.62, 107.38] | 63.75/84.00/123.50 | 11320.86 | 1446.01 | 5968.63 | 0.04 |

## 3. 通信差异与次要联合干预

[RUN] 下表差值=intervention−shared，正值为更多开销。括号为未校正、仅描述性的paired95% CI（不是主要六项family区间）。UL+DL是原base模拟器记录的data UL + common-knowledge广播DL；未增加oracle同步bits/时延/失败、packet headers或真实协议栈成本。模型ack_bits默认字段不意味着base实际包含ACK，应以simulator._downlink/result为准。

| 设置 | 干预 | ΔUL uses [95% CI] | Δ(记录UL+DL) uses [95% CI] |
|---|---|---|---|
| default | private | +320.37 [-408.31, 1049.26] | +307.02 [-588.24, 1207.51] |
| default | position | -382.18 [-1012.28, 248.29] | -450.77 [-1235.59, 334.72] |
| default | joint | +260.67 [-544.10, 1077.80] | +254.95 [-739.96, 1282.78] |
| W50 | private | +502.36 [25.48, 980.92] | +620.72 [-28.33, 1276.45] |
| W50 | position | +558.88 [-22.43, 1103.35] | +800.45 [28.04, 1534.28] |
| W50 | joint | +484.19 [-49.48, 1001.10] | +578.99 [-127.73, 1263.67] |
| snr-5 | private | -498.08 [-1305.14, 320.70] | -396.07 [-1339.18, 550.53] |
| snr-5 | position | +1170.52 [321.05, 2034.03] | +1359.30 [410.44, 2333.92] |
| snr-5 | joint | -676.40 [-1459.92, 87.05] | -618.79 [-1504.25, 258.30] |

[RUN] W50/private的UL与snr-5/position的UL点估计增加；虽部分边际成本CI排除零，也不是经过联合资源family校正的确证主张。不能将default/private的8.48%直接写为等成本净收益。bits/8不等于真实线路序列化字节。

以下joint仅次要、未校正95%，表中family列等于95%列，不能当作六项family结果：

| 设置 | 干预 | 收益slots | 收益% | 95% CI | 同一95% CI | 5%阈值slots | 正/负/零seed |
|---|---|---:|---:|---|---|---:|---|
| default | joint | +1.40 | +1.93% | [-6.30, 8.86] | [-6.30, 8.86] | 3.631 | 53/45/2 |
| W50 | joint | +1.13 | +1.42% | [-7.50, 9.51] | [-7.50, 9.51] | 3.973 | 45/54/1 |
| snr-5 | joint | +2.46 | +2.46% | [-8.98, 13.15] | [-8.98, 13.15] | 4.998 | 50/44/6 |

交互=joint收益−private收益−position收益，以下为次要未校正95% CI：

- [RUN] default: -7.01 slots, 95% CI [-16.16, 1.53].
- [RUN] W50: +3.77 slots, 95% CI [-10.08, 17.61].
- [RUN] snr-5: -1.50 slots, 95% CI [-17.18, 14.28].

## 4. 机制解释与外推限制

- [CODE] voi.py:46–57/97–105中dist同时进入预测policy分数和sender侧u_true；position干预不是只修正policy预测误差，不能将其差异唯一归因“接收者位置不准确”。private同时开放pending_llr和confirmed_pending，不等于只改变单个belief标量。
- [CODE] joint仍用Boltzmann softmax代理、sender侧belief效用和shared deconfliction信息；实际Agent.plan有argmax与hysteresis。原joint不是最优决策oracle，也不是真实任务收益上界；增加信息可能改变错误代理的排序，单因素收益不保证可加。
- [CODE] simulator.phase_decide的private_tv为未归一化概率图L1差的时间平均代理，不能当作接收者任务正确率或标准归一化TV。其变化也可能随轨迹/通信变化，未做中介效应识别。
- [HYPOTHESIS] 代理目标、决策规则差异、轨迹非线性和资源变化均可能解释信号不稳定；本轮未分别识别，不可断言某一个原因已证实。
- [RUN] 仅一个网格search任务的三参数设置、纯Planner，不能推广为开放式多轮LLM任务、rescue任务或共享无线系统的结论。未执行LLM cached/live、重新calibration、等成本frontier或新方法。
- [RUN] 接收端诊断是用户批准的ToM路径限定准入；前置1900条ToM已有保存字段匹配，不能将此改写成原5200全部精确复现。此前throughput数值敏感性与本receiver假设是不同问题。

## 5. 证据与重建

- 原始完整raw/curve、source/config/plan/approval/log保留在 `E:\gosc-agentic-teams\.local\reproduction\2026-10-15-receiver-v1`；raw SHA256 `74b89a22cc6e1226fc85b944e850813b090a7fa82dbab6fefab384953b5b7483`。
- 所有1200逐seed标量（含不利seed与错误声明）在per_seed_outcomes.csv；总体/配对统计由冻结experiments_ext.summarize计算，无手工改图点。time_contrasts为主要区间加次要joint；time_and_resources为边际95%的描述散点，不能用于family显著性判定。
- preanalysis_audit.json与experiment_manifest.json记录身份/配置/哈希/原准入/76项保护；原statistical-v1的raw和gate哈希保持不变。复制的历史approval日期与运行日期保留，不以继续日期冒充新运行。
- command_ledger.json列真实命令。`summarize diagnostic`和本导出器均拒绝已有输出；重建时复制完整run证据到新隔离目录并选择新的输出实现，不覆盖本次完成记录。
- 测试日志：contract-tests.log、full-tests.log；继续任务不重复耗时测试，报告工具没有作为已通过105项的一部分。图PNG已目视检查：标签/区间/图例完整，未修改冻结绘图结果。
