# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 接收端私有证据/位置在原Planner上是否能稳定带来≥5%时间收益？继续此前已批准的1200次诊断，不扩大研究范围。
- **已核验前人工作**：[PAPER] 沿用此前D01 p.8 TableVI、p.11私有信息实验记录，本轮不新增论文事实。[CODE] 原shared/joint对照已存在。
- **实际阅读源码**：[CODE] baseline387b493；执行491b187。TeamModel、Config、Simulation任务/资源计数、receiver_oracle、campaign/runner/admission/summarize与门控测试；原源码不改。
- **本轮新增或修改**：2026-10-16 continuation brief；receiver_report.py导出器；research/reproduction/2026-10-15-receiver/完整报告/统计/逐seed/图/manifest/next_stage_plan；全局证据索引与旧报告新增后续链接。10月15日已提交的准入/runner/测试改动保留。
- **实际运行**：[RUN] 10月15日1200 fresh由4workers完成730.807s；本轮只核验并执行summarize diagnostic及receiver_report，无重跑mission。12组各100，seeds4000–4099，无训练调参/LLM。
- **测试与结果**：[RUN] 运行前targeted11 passed/6.04s、full105 passed/47.77s，日志复核；本轮未重跑完整测试。preanalysis与export核验1200唯一身份/配置、curve/有限值、raw/source哈希和76项受保护文件。六个主要family CI均跨零；default/private均值6.16 slots(8.48%)，95%[0.45,11.82]，family[-1.41,13.92]。不将导出器写成已被先前105项覆盖。
- **失败/负面证据**：[RUN] W50/position点估计-3.23slots；joint/交互均未校正CI跨零；全部6项上界仍允许5%收益。无异常退出/缺seed/超时，任务1200均完成，但45次false declarations保留。strictR4失败和R4-S1四项不确定不改。查找旧paper-code-map路径未找到，未将该路径用作新证据。
- **与原 GOSC 的差异**：仅TeamModel诊断view开放不同当前状态，不是新估值器；本轮续作只读分析与归档。
- **公平性与泄露检查**：相同seed/外生流初始化不等于所有分支全程相同候选消息；oracle免费/固定eta/实际开销不匹配，不能写等成本收益。共享上行未启用，不能推广LLM/新任务。全部seed保留；下一轮如用这些数据设计模型，须标为开发而非未见测试集。
- **成本**：[RUN] 12.18min仿真（前一日完成）、4CPUworkers、0GPU/LLM/付费API/下载；raw2,086,897bytes。worker mission wall求和2916.455s不是CPU时间；峰值资源和真实序列化bytes/packet-success未测。资源见完整报告。
- **可否进入下一阶段**：No-Go for方法开发/稳定缺陷宣称，Pending for科学假设；已批准诊断执行与归档完成。
- **用户需要批准的下一步**：next_stage_plan.md建议先机制/相关先例审查，再审定同状态离线反事实与成本协议；未执行新实验、改任务或发信。任务结束停止，等待用户决定。

报告审阅：原导出标题“1200次独立”容易混淆fresh execution和独立统计单位，已另存report_v2.md明确为100个配对seed×3设置×4模式；原report/hash保留，数字/区间/决策不变。report_review.json保存准确文本变换。首次追加索引patch因旧报告标题不匹配失败、未产生部分修改，核验实际标题后重新应用；不影响实验或统计。
