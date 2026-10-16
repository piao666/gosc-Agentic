# Research Task Brief — Receiver-D1 continuation

- **授权与范围**：用户2026-10-16“继续任务”，完成此前已确认的ToM路径限定诊断。启动commit491b1878dfc50a439c055703f598212862079bfc，工作区clean；不扩大为算法开发或新实验。
- **科学问题**：[HYPOTHESIS] 独立receiver私有证据/真实位置是否在原Planner三设置中稳定改善completion_time至少5%？联合模式和交互为次要。
- **已知证据**：[RUN] 2026-10-15执行manifest保留1200条，耗时730.807秒，76项保护输入无变化；105 tests passed的原日志存在。此刻尚未分析效果，不将执行passed等同于假设成立。strict R4仍failed、R4-S1仍inconclusive。
- **拟修改**：新增本轮统计/图表/完整报告、manifest与证据索引；不改冻结协议、分析器、adapter、核心算法或旧结果。
- **实验/分析**：不重跑mission。先复核1200唯一(setting,mode,seed)、3×4组各N100、配置/源码/raw哈希、原准入与保护输入；再执行冻结summarize.diagnostic（paired bootstrap4000、seed0、6个主要比较Bonferroni、5%阈值），保留全部结果。
- **成本**：仅文件校验/CPU统计与制图，预计数分钟；无LLM、模型下载、依赖安装、GPU或收费API。
- **反例/验收**：若三设置不能同时达到单因子family CI下界>5%，不宣称稳定实用缺陷；跨零不是无作用证明。检查实际资源成本与privileged state边界。报告完成后停止，下一步需另定。
