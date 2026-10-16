# Research Task Report

- **Research Question / Hypothesis**：已完成用户批准的“代理估值与实际 Planner 机制审查＋同状态离线反事实/成本协议制定”。[HYPOTHESIS] receiver 旧目标、迟滞与消息生效时序可能解释估值失配；尚不能断言这些差异造成稳定且可修复的性能缺陷。
- **已核验前人工作**：[PAPER] 本地 D01 p3/p5/p9、ToM2C p5–6、PragComm p5/p9–10、BANDMAS p3–5 的相关机制，见 [证据卡](prior_art.md)。这是定向精读，不是全网查新/四篇全部结果复现。原 GOSC 已有消息反事实诊断；BANDMAS 已有离线 replay 标签与廉价冻结估值器；新颖性风险明确，不能包装为我们的既成贡献。
- **实际阅读源码**：[CODE] 原 commit `387b49389385b51c275dc5a22ec1672087edda1d`；本轮起点 `d1eddaebc63313f222da7b5bb759a3e86a4da4d3`，`codex/baseline-reproduction`，启动工作区 clean。阅读 agent/voi/simulator/environment/belief/messages/schemes 的相关完整实现、realistic 并行路径，以及 diagnose_value/analyze_fidelity/plot_revision 的诊断与统计路径；详见 [逐项源码映射](code_map.csv)。没有改核心代码。
- **本轮新增或修改**：本目录的报告、22项映射、4篇证据卡、saved 数据审计、manifest/命令/证据索引；[具体协议](counterfactual_protocol_v1.md)；[只读审计脚本](../../../experiments_ext/review_receiver_mechanisms.py)；[8项构造测试](../../../tests_ext/test_counterfactual_semantics.py)；本轮 brief/任务日志。全部新增；原报告、算法、缓存和结果不改。
- **实际运行**：[RUN] `.venv\Scripts\python.exe -m pytest tests_ext/test_counterfactual_semantics.py -q`；`.venv\Scripts\python.exe -m experiments_ext.review_receiver_mechanisms --output-dir research/reproduction/2026-10-16-mechanism`；`.venv\Scripts\python.exe -m pytest tests tests_ext -q`（Tee 到本机隔离日志）。本机 Python3.12.10、Windows、既有 lock，不安装依赖。另用已安装 bundled pypdf/Poppler 本机提取4篇 PDF，并视觉核对4页公式。构造 fixture seed991234 不是新性能数据，测试集内的原有 seed 按既有测试运行；没有运行新的 diagnostic mission/rollout 批次。
- **测试与结果**：[RUN] 新构造测试 **8 passed / 1.41s**；完整 **113 passed / 99.18s**（包含这8项，不能相加为121）。日志 `.local/reproduction/2026-10-16-mechanism-v1/full-tests.log`。只读审计：作者 saved **914 rows / 20 missions**，原始数据 SHA256 `333088e4624ad0d69d60eccc6223eac82a6b2a8e3f65383958c5a32ad578752c`；没有新 mission 性能/CI。76项上游受保护输入 SHA256 全匹配，见 [审计JSON](saved_diagnostic_audit.json)。
- **失败/负面证据**：新性能实验未运行；新反事实执行器未实现/未通过 gate；本轮不具备新方法收益证据。继承 [Receiver-D1](../2026-10-15-receiver/report_v2.md) 六项主要校正区间均跨零、strict R4 failed、R4-S1 statistically_inconclusive，不改判。只读命令曾因错误猜测文件路径/Windows rg glob 报错，已定位实际路径；PDF提取文本输出曾遇 gbk 编码错误，使用 stdout UTF-8 后完成，未改文件/依赖。这些不是测试失败，也没有掩盖为通过。
- **与原 GOSC 的差异**：算法/Planner/Channel/Scheduler 均无变化。本轮新增证据审查与合成契约。计划中的固定可行尝试 success/failure，与作者免费完整 E/I/EI 交付实验是不同 estimand；不得拼接两类数据或继续沿用同名结果。
- **公平性与泄露检查**：只读 Obsidian；未调用外部解析/API/模型；没有上传 PDF/研究数据、公开推送或联系作者。旧原始结果/负结果保留。构造反例不估计总体频率；offline world truth/receiver 私有状态不得进入 online 特征。提案5000–5007仅开发/诊断用途，未执行/未认定正式 unseen test，需批准后冻结；原 seed split 不变。
- **成本**：本轮新性能任务 channel uses/tokens 不适用（未运行）；测试中的模拟计数不是论文实验成本。实验 LLM/API 调用0、无模型下载/GPU实验，助手自身 token 成本未计量。新契约测试1.41s、完整测试99.18s是两个独立执行的 wall time，研究阅读/全部 CPU/RAM 未计量，不报0。PDF本机解析采用已有 bundled runtime，未改 `.venv`。未来 pilot 预计≤15min CPU/2workers/每worker1数值线程、≤128 branches，是估算及硬上限，不是实测。
- **可否进入下一阶段**：**Go：本阶段完成，可审协议；Pending：具体 pilot 实现与执行授权；No-Go：宣称稳定缺陷、创新成立或部署收益。**
- **用户需要批准的下一步**：建议按 [Receiver-CF v1](counterfactual_protocol_v1.md) 实现隔离执行器、先通过 no-op/tape/ACK/queue/终止等 gate，再运行最多8个开发 missions、128条配对分支。新 seed/运行预算尚未批准；本轮停在此评审节点，不自动开始。

## 已确认的机制与证据限度

| 问题 | 本轮证据 | 科研含义 |
|---|---|---|
| 代理忽略 receiver 的旧目标与 hysteresis | [CODE] Agent.plan 与 TeamModel._expected_utility；[RUN] 合成相同 belief 下旧目标保留、新 agent 换目标，而代理值不变 | 机制差异存在；尚不知道任务分布中频率、影响或可修复性 |
| 本时隙交付之后没有立即重规划 | [CODE] 全体 UL 决策→fusion→downlink→motion；[RUN] 构造测试验证 | 下一次实际决策发生在移动和新感知之后；立即 shadow replan 不能冒充实际 next target |
| 作者已有反事实实验，但边界不同 | [CODE] force 免费送完整buffer、提前融合、sender静默；[RUN] 提前force确实改变其他 UL 输入 | 作者诊断回答一个有意义的局部问题；不能直接当同预算单个可发 packet 的价值标签 |
| `_snapshot()` 不是完整实验状态 | [CODE] 仅四项 broadcast state；[RUN] deepcopy隔离与内部 channel alias 测试 | 执行器必须复制所有动态状态/随机流并增加 no-op continuation gate |
| 共同初始 RNG 不保证逐格噪声对齐 | [CODE] sensing window 变尺寸；[RUN] 3×3和5×5感知后RNG状态不同 | 主协议保留 native 顺序流并披露耦合边界；不是自动证明估计有偏 |

## 原诊断指标的核查

[PAPER] GOSC p9将914个 sampled decisions 的6–12%描述为队友目标改变。[CODE] `plot_revision.py:689` 实际写 `changed = mean(gt_gain != 0)`；`diagnose_value.py:160` 的 `n_teammate_changes` 恒为 None。`gt_utility` 以拷贝 receiver 做立即重规划，再计算真实幸存者距离折扣覆盖；覆盖效用变化与目标变化不等价（不同目标也可有相同覆盖效用）。

[RUN] saved 数据核查如下；比例只叫“覆盖效用变化”，不重新命名为动作改变，也不能由此确定作者是否有未公开的独立目标计数。

| 类型 | saved rows | `gt_gain != 0` | 覆盖效用变化比例 | dT正 / 负 / 零 |
|---|---:|---:|---:|---:|
| E |369|21|5.69%|185 / 147 / 37|
| I |279|19|6.81%|94 / 94 / 91|
| EI |266|32|12.03%|151 / 99 / 16|

914条全无 target-change count；20 missions 才是聚类抽样单位，不能把914当独立任务。

[CODE] 原分析的 `argsort(argsort())` 给相同值不同 ordinal rank；原代码已对常数特征返回 NaN。新审计保留原分析，另外计算 average-tie 点估计：E/ToM 与 dT 的 rho 从0.05349到0.05313，E/AoI从0.07942到0.07388；I/AoI从−0.08039到−0.05932。**未对新 rho 重算 CI 或显著性**，不得由这个小幅变化声称原作者结论失效。新协议使用 average-tie ranks、mission-cluster bootstrap，并报告常数/无效重采样。

## 最重要的研究风险与下一阶段验收

1. **新颖性**：反事实标签、receiver-demand、ToM和廉价估值都已有紧邻先例，尤其 BANDMAS；需要具体新机制及强简单 baseline 的净增益证据，而不是模块组合。
2. **可归因性**：proxy mismatch、target change 和 completion-time effect 是不同量。当前 private/position oracle 涉及免费特权状态，position同时改变policy与utility，不是“真实最优效用上界”。
3. **任务灵敏度/成本**：原搜索任务可能对精细语义价值不敏感；新状态信息与 compute/sync 成本可能抵消收益。不能为了正结果改任务或忽略控制通信。
4. **基线准入**：严格复现问题仍在，本阶段只能在已批准 ToM 路径上继续诊断；LLM cached/live 均未由本阶段验证。

下一步先检查“可行 packet＋正确时序＋正确 ACK/queue”是否能产生可重复的正/负/零任务标签，再判断 ToM 与简单特征是否能排序。如果没有可解释信号，保留负结果并停止发展此机制；若有，也不能直接宣告论文贡献。完整预算、假设、采样、失败处理与门槛见协议，不在本轮运行。
