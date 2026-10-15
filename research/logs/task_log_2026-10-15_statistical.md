# Research Task Report

- **Research Question / Hypothesis**：获批的R4-S1统计复现；为receiver诊断检验原基线。
- **已核验前人工作**：[PAPER] 沿用D01精读；本轮为新运行，不新增文献结论。
- **实际阅读源码**：[CODE] 原版387b493；协议/统计冻结dfd9475；门控25c280b。
- **本轮新增或修改**：独立统计采集/分析/绘图/门控工具及测试、协议、草稿、日志和本轮紧凑证据。
- **实际运行**：[RUN] 5200全新Planner任务，4workers；0–99与3000–3099；原配置不调参。prepare/run/analyze，绘图与导出。
- **测试与结果**：完整99 passed/132.50s；最终统计7 passed/.72s；门控2 passed/.12s。104项100等价、4不确定、0明确不一致；原private600与headline1200保存字段重现。原始76输入无变化。
- **失败/负面证据**：200记录/800字段有精确差异，77completion_time变化；throughput3个低eta任务区间和eta0资源区间未进入±5%。原oracle3个任务收益CI均跨零。导出路径、图裁切/图例问题已纠正并留证。
- **与原 GOSC 的差异**：只加工具，原算法/调度/信道不改；旧strict失败保持。
- **公平性与泄露检查**：无训练/调参/筛seed；已见旧样本披露为修订协议；oracle成本未匹配；calibration/LLM未重跑。
- **成本**：1455.827s仿真，raw8,912,773bytes；4CPUworkers；无GPU/API/模型下载；未测峰值/真实bytes/tokens。
- **可否进入下一阶段**：Pending/No-Go；receiver因子1200次未运行。
- **用户需要批准的下一步**：审阅已形成的ToM路径限定诊断方案；不是放宽原R4或抹去失败。

完整报告：`research/reproduction/2026-10-15-statistical/report.md`。
具体待确认方案：同目录`receiver_scope_proposal.md`。
