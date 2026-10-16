# Receiver-CF v1：同状态离线诊断与成本协议

状态：**review_ready / execution_not_authorized / not_run**。2026-10-16。
用户本轮批准机制审查和具体协议制定；本协议中的新 seed、分支执行器和 continuation 批次尚未执行。此文件不是新方法或原始基线复现通过证明。

## 1. 问题、借用和否证

[CODE] base `d1eddaebc63313f222da7b5bb759a3e86a4da4d3`；原 GOSC `387b49389385b51c275dc5a22ec1672087edda1d`。沿用已批准的 ToM 路径诊断限定准入；strict R4 failed、整体 R4-S1 statistically_inconclusive 原样保留。此协议不为所有 baseline 或 LLM 准入。

[PAPER] GOSC PDF p9 §V-D 已有同状态消息反事实；BANDMAS PDF p3–4 已有离线消息移除/单包重放监督与低成本先验。不得把“使用反事实标签”“廉价预测器”“receiver-aware”单独写成贡献。

[HYPOTHESIS] H1：softmax 代理忽略旧目标/迟滞，可能与实际 receiver 的下一次决策不一致。H2：这种不一致可能对应低价值排序保真度；**H1 不蕴含 H2，更不蕴含可部署性能收益**。H3：补充运行状态的预测收益可能被状态同步成本抵消。本轮没有实现或验证修正估值器。

否证：如果真实目标变化稀少、ToM 失配与任务效果无稳定关系、简单 AoI/字节数同样好，或运行状态获取成本超过收益，停止增加该机制复杂度。若诊断支持进一步研究，也先做 M0 和代价匹配；不自动跳到 M1/M2、LLM 或更换任务。

## 2. 三种量必须分开

1. **代理差值**：原 `TeamModel` 的 sender-belief 效用差，记录 unclipped VoI、clipped VoI、成功率和实际 Option.value 四列，不能混作同一个值。`u_true` 的 true 指 sender 自有信念，不是 world truth。
2. **行为诊断**：对实际 Planner 作只读 shadow prediction，保留旧 target、位置、hysteresis、teammate points、confirmed_pending 和 RNG。分别记录当前已定 target、下一次真实 `phase_decide(t+1)` 后 target 及轨迹；假想立即重规划只作独立辅助量，命名 `shadow_pre_motion_replan`。不将覆盖效用差非零当作目标变化计数。
3. **任务影响标签**：下面的固定原生发送尝试，成功与失败分支的未来 capped completion time 之差。离线标签含特权仿真信息，不能进入在线输入、候选选择或调度。

## 3. 干预边界：固定尝试，覆盖一次解码结果

选择**after sense/plan/on_step、before any uplink** 的完整状态。仅使用原生 `GOSC.build_groups`、`lagrangian_select` 实际选择的一个 EVID 或 INTENT packet；CONF 价值固定且路径不同，本 pilot 不混入主分析。不是完整 pending buffer，也不是原生 scheduler 没选的包。若无 E/I 尝试，记录 unavailable，不合成消息或依结果替换样本。

这里保留 **sender→edge→共享状态广播给团队** 的原 GOSC 语义，不改为指定 receiver 的点对点消息。E 还可更新 sender 的 last-known position，I 更新公开 intent；同一 packet 对多个 receivers 的行为影响作为一个向量记录，不能拆成独立任务样本。只采已选尝试有 policy selection bias，可能漏掉被原估值压到零的潜在有用消息；本 pilot 不回答该漏选问题。

所有 agents 的本时隙候选、选择、发射参数、fading draw、逐次解码 RNG 消耗均先从同一初始状态录成可核验 tape。仅对被选 packet 的一次 decoder 结果施加 offline success/failure override；两个分支消费同一个 decoder draw（outage 时没有此 draw），其余 packet 本时隙选择/解码结果完全一致。packet identity 包含 agent/type/rate/prefix record IDs/ordinal，不能仅按函数调用序号随分支漂移。执行器须位于 extensions/experiments_ext，不改 gosc 核心。

- **D-success**：正常 ACK/队列移除，正常 edge fusion 和理想下行，sender 的 pending_llr 在融合时扣除已交付记录。
- **D-failure**：同一次尝试的 bits/symbols 照常计费；不 ACK、不清 queued/pending records、不融合；后续允许原策略自然重传。
- 两分支本时隙其他发送完成后才统一融合，不预先 `force()` 更新共享 belief。后续完全使用原 GOSC/Planner，不能冻结未来行为来制造收益。
- 本时隙 target 已定，正常情况下先按旧 target 移动、下时隙重新 sensing 再 plan；若成功分支本时隙已完成任务，可立即结束，作为真实终止效应记录。不能人为补移动。

该标签为**被原策略选中尝试的条件解码效果**，不是 send/no-send、任意候选的效果或全局最优效用。两分支相同的是当前尝试成本，未来重传、广播、轨迹与总成本可不同。channel outage override 是离线干预，不宣称某相同 SNR 下物理上同时成功和失败；真实成功概率单独保存，不把条件 dT 直接叫 expected Option value。若要评价 unselected candidates 或 send/no-send，需要另定干预与预算。

不直接复用 `diagnose_value.force()`：它免费瞬时交付完整 E/I/EI，并让 sender 本时隙静默，而且更新发生在其他 agents 的 UL 决策前。这是有意义的作者诊断 estimand，但与本协议不同；保留原结果和命名。

## 4. 状态、随机流和执行契约

完整 deepcopy 至少含：cfg、world/mask/deadlines、Lc/declared、所有 agents 的位置/target/shared_intent/confirmed_pending/pending_llr/pending_records/queued_llr/ACK/队列/轨迹；team_pos/intent；scheme price/log；curve、计数/confirm/located time；全部 RNG bit_generator 状态及 channel 与 scheme.channel 的内部别名。`Simulation._snapshot()` 只有四项 broadcast view，不足以作实验快照。避免不可信 pickle；本机 checkpoint 若用 pickle 仅从本执行器可信自产文件读取，原始状态保持本机。

随机规则：world 固定；在干预时隙使用原 native streams/tape；之后每个 replicate 从预先保存的同一状态生成两份 sense/plan/fading/decode/downlink streams，包含全部五流，即使 ideal DL 当前不消费。未来 replicate keys 固定为 `[mission_seed, t, selected_agent, replicate, stream_id]`；同一次干预同一 replicate 共用初始 key。原 `rollout()` 重置四流而未重置 DL，在其默认 ideal DL 中不构成实际 DL 随机误差，不能泛化为其非理想 DL 已验证。

**主协议保留原生顺序随机流**，保证各分支边际模拟机制不变。由于 sensing window 边界裁剪改变 draw 数，相同初始 RNG 不保证分叉轨迹后 `(t,agent,cell)` 的噪声相同；这会影响耦合和方差，不自动构成估计偏差。报告称 stream-coupled，不称逐格相同噪声。若后续改为 event-keyed 全网格噪声，那是独立的敏感性协议，需另审定，不静默改本协议。

上线前必须通过的 gate（**目前只有部分合成机制已核验，执行器尚不存在**）：

- no-op twin 从同一状态继续，完整轨迹/队列/成本/RNG 必须一致；native tape replay 与直接 native continuation 一致。
- 成功和失败 override 的当前选包/非干预 draw 一致；包含多包 E+I、先 CONF 后 E、prefix、无可用消息、终止时隙和 failure-to-retransmission 场景。
- sender local LLR 分解、队列、ACK 与 edge fusion 各只变更一次；无其他 packet 无意受 override 影响。
- 下一实际 decision 和 shadow replan 明确分列；无噪声/空干预应为零差。
- 输出每分支 status/exception/timeout，无吞异常/缺失 seed；已完成 ID 不覆盖，恢复须匹配 source/config/tape hashes。

任一 gate 失败，先定位，不运行 pilot；不能将本轮 8 项合成契约测试说成上述完整执行器通过。

## 5. 待批准的有界 pilot（不是正式效能检验）

提议 Config() 原 search、6 Planner、grid32、W100、eta=1e-5、outage、CSIT false、ideal DL、orthogonal UL、horizon400；不调用 LLM。完整 dataclass config 与 lock、源码 hash 在执行前冻结。

新开发/诊断 seeds **5000–5007**，8 个 missions（提案，尚未分配为已批准数据集）。每 mission 固定 t=8、24，在任务仍存活且存在原生 E/I 尝试时各取一个 packet。选择规则：对该时隙全部已选 E/I 尝试的稳定 ID 计算 SHA256(`Receiver-CF-v1|seed|t|packet_id`)，取最小值；不按 VoI 大小/解码结果/未来收益选。若空缺/已终止，保留原因，不补点、不换 seed；覆盖偏差按 t/type/agent 报告。本 pilot 仅代表该采样规则下已选 E/I，不代表所有可发消息。`t` 为源码 zero-based slot。

每点 R=4 continuation repetitions，D-success/D-failure 两分支：最多 `8×2×1×4×2=128` branch continuations，加 8 条 native 前缀轨迹。2 workers、每 worker 1 numerical thread；预计数分钟至 15 分钟，**不是实测值**。以 wall-clock 15 分钟或 128 branches 为硬上限；超时保留 partial/timeout，不静默删对照或自动扩充。原 1200-run 成本不能直接当有 deepcopy/日志的执行器基准。CPU/RAM/time 实测另记，禁止 GPU/API/model download。

5000–5007 只作开发/协议检查；已曝光的 4000–4099 不可回收为 unseen test。原 calibration1000–1079、evaluation0–99、validation3000–3099 不调参；作者 fidelity2000–2019 保留为已有诊断。不得因为本 pilot 有利就直接作为最终新方法评估；正式数据划分/功效分析另审定。

## 6. 终点、统计单位和反例

主任务终点：`DeltaT = completion_time_failure - completion_time_success`（正值为成功交付更好），completion time capped at400、未完成保持400；同时保留 completed、found/curve、false_declarations、confirmation latency，防止把假阳性或截尾当任务提升。每点先平均其 R 配对差，每 mission 再等权平均已有点，最后 mission 等权汇总。无点 mission 计入 coverage，但效应缺失，不擅自填零。

首要估值诊断：E/I 分类型的 **unclipped ToM 与点级 DeltaT 的 average-tie Spearman**；按 mission cluster bootstrap 4000次（分析 RNG seed0）给95% CI及有效 resamples 数。AoI、payload bits、belief divergence 作同时列出的简单对照，常数/少样本类型输出 undefined。pilot 无显著性/功效承诺；8个 clusters 太少时 CI 不稳定，不能据此宣告稳定缺陷。正式扩展若比较四类估值器，预先固定 family 和调整，不能看完结果挑最优。

行为终点直接逐 receiver 比较两分支下一次真实计划的 target，记录变化数、身份、old target/hysteresis margin、距离、belief/private差及时间。shadow 同步重规划与 native next plan 结果分表。代理忽略 history 是已知机制；仅观察相关性不能归因为它单独导致 completion time 损失。未来要拆分 history/private/position 的因果贡献，需独立诊断 masked models 与预先比较设计，不改变 Planner 保留基线。

报告 N_missions/N_points/N_pairs/N_branches/type availability、均值/中位/分位/CI、正/负/零效果、失败/timeout。R 次、多个 receivers、多个 packets 均不能作为独立 mission 扩样本。负结果全保留，不根据 dT 排除点，不对几条样本作“代表性缺陷”主张。

## 7. 成本与泄露边界

当前 native 模拟的 `bits` 是 bit accounting 模型，**无实际字节串序列化**；`symbols` 为 UL uses；`delivered_bits` 为解码成功负载；`dl_symbols=ceil(dl_bits/dl_rate)`。消息内置8-bit type/id header 已在 payload 计入，额外 CRC/PHY/ACK 不完整。不得写为测得真实网络字节。后续若要真实字节，先实现明确 codec 并逐包按 ceil(bits/8) padding、控制字段和实际序列化计量。

每 attempt 记 agent/type/rate/prefix/bit/symbol/ps/decode/ACK；另账本记广播、ACK、状态同步、header/CRC/padding。base 未建模项标为 **not_modeled**，不可写0或凭空加为“实测成本”。若用 RealisticGOSC 补 ACK/开销，须独立 scope、并验证 schemes.py 和 realistic.py 两路径，不把它替换为本 pilot 后继续标相同 baseline。

本 pilot 不查询 receiver 私有状态作在线调度；仅离线日志读取。未来 state-aware 输入须分：sender 本地可见；已广播但陈旧；需要同步 receiver target/position/summary。同步协议须写 timestamp/version/quantization/header、上报频率、成功概率和陈旧度；先实现串行化再报实测bits/latency。免费 oracle 只作诊断参照，不是可部署上界。未来策略收益必须通过 **paired cost-matched frontier**，包括 UL+DL+sync+compute，不能由本条件解码实验直接推出。

离线原始状态/world truth/future outcomes 与在线 feature CSV 分文件；features 明确白名单，不含 outcome/reward/world mask/true victims/private receiver data，除非独立标记 privileged diagnostic view。无需训练，不调任何模型参数。记录 extra agent calls/tokens=0（仅该 Planner 仿真实验），以及 deepcopy/rollout CPU time、peak RAM、wall time；本助手分析 token 成本未计量，不能写0。

## 8. 实现及归档验收

后续先新增 `extensions/counterfactual.py`、`experiments_ext/run_receiver_cf.py`、`tests_ext/test_receiver_cf.py`（**计划路径，当前不存在**），完成上述 gate，再冻结 manifest 后运行。CLI 必须先审 `--help`/写入；输出新 `.local/reproduction/<approved-id>/`，mkdir exclusive、逐样本 raw JSONL+tape/state hashes；不执行作者 `diagnose_value.main`、不写 `results/`。归档 source/config/lock/全部命令/seed split/采样缺失/原始分支结果/CI脚本，所有结论可重建。

本阶段结论：**Go：机制审查与协议评审；Pending：批准上述有界 pilot 的实现与执行；No-Go：宣称论文创新或部署收益。** 下一次授权只覆盖本协议明确范围；增大 seeds、变任务、LLM、event-keyed噪声和算法训练均另审。
