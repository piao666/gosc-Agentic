# 2026-10-16 — Receiver 代理机制与反事实协议审查完成

起点 d1eddaebc63313f222da7b5bb759a3e86a4da4d3；用户批准“进行此阶段”。启动clean；只新增本任务文件，无核心修改、无新性能批次、无推送/外部调用。

完成 Research Task Brief、实际 Planner/TeamModel/融合/队列/随机流/两条调度路径映射；本机定向精读 D01/D08/D06/A02 四篇 PDF 相关章节与4页公式图像。BANDMAS 已覆盖离线 replay→廉价 online predictor 路线，新颖性必须重新严格界定。

[RUN] 新合成契约8通过1.41s；完整113通过99.18s（包含8，不相加）。另对 average-tie ranks 做4个数学探针通过，不混入 pytest 计数。作者 saved 914条/20 missions只读重分析，全部缺失直接目标变化计数，gt_gain非零比例E5.69%、I6.81%、EI12.03%。tie处理敏感性只报告点估计，不报告未算CI/显著性。76个protected inputs匹配。

发现：softmax忽略receiver旧target/hysteresis；native先规划再通信再移动；作者force提前免费融合完整buffer，改变他人当时UL输入；broadcast snapshot不是完整状态；sensor裁剪使CRN非逐格对齐。这些机制不证明分布中存在稳定可修复损失。原作者已有反事实诊断，不是我们的新贡献。

产物：[完整报告](../reproduction/2026-10-16-mechanism/report.md)、[反事实与成本协议](../reproduction/2026-10-16-mechanism/counterfactual_protocol_v1.md)、[证据卡](../reproduction/2026-10-16-mechanism/prior_art.md)、[源码表](../reproduction/2026-10-16-mechanism/code_map.csv)。机器可读manifest/命令/证据索引同目录；原始本机PDF提取和测试日志在`.local/reproduction/2026-10-16-mechanism-v1/`。

状态：本阶段 complete；strictR4 failed保留、R4-S1 statistically_inconclusive保留；Receiver-D1 6项主要校正区间跨零。No-Go：新方法/稳定缺陷/部署收益宣称。Pending：用户审定协议后，才实现执行器、通过完整gate，并运行提议5000–5007、最多128 branches、2workers/15min CPU pilot；当前未实现/未运行，不自动扩大或改任务，不安装Ollama。

任务结束停在报告节点。下次先读本文件、完整报告和具体协议；不要把本轮合成测试通过误当新反事实runner通过，不要覆盖旧结果或把开发seed当unseen test。
