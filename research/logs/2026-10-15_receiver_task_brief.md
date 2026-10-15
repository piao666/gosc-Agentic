# Research Task Brief — approved ToM-path receiver diagnostic

- **授权**：用户本轮“确认”明确批准`2026-10-15-statistical/receiver_scope_proposal.md`。工作起点95ce323，启动工作区clean。只改变诊断准入范围；strict R4仍failed、R4-S1仍inconclusive。
- **科学问题**：[HYPOTHESIS] 在固定原ToM估值器、Planner、scheduler、channel与eta下，给TeamModel分别开放receiver私有证据与真实位置，能否得到稳定且有实际意义的任务收益？
- **前人成果**：[PAPER] 沿用D01私有信息对照精读；[RUN] 原ToM1900条已有参考字段匹配，原joint-oracle三个设置未确证稳定收益；新4000–4099尚未采集。
- **修改**：独立准入记录/验证与runner门控、必要门控测试、协议与报告。`gosc/`、原始数据/缓存、adapter、原统计方案不改。
- **设计**：3设置(default/W50/snr-5)×4模式(shared/private/position/joint)×100独立seeds4000–4099=1200新运行。沿用已冻结4000 paired bootstrap、统计seed0、6个主要单因素对照、Bonferroni6、shared均值5%实用阈值；joint和交互次要。
- **解释边界**：[CODE] `voi.TeamModel.dist`同时用于预测策略与u_true，所以position不是纯预测误差干预；joint仍沿用softmax等代理和旧的队友排斥信息，不是任务最优oracle。无LLM实验或可部署state查询，访问状态未计价，固定eta非等成本。
- **成本**：最多4CPUworkers/每worker1数值线程，预计5–15分钟，上限25分钟；完整测试另计数分钟。零依赖/模型下载、GPU/付费API/LLM调用。
- **反证/停止**：无稳定实用收益则报告负面或边界结果，不加模块/挑seed/改变任务。异常/缺seed/哈希变化失败保留证据。完成后停止，下一步成本匹配或新任务另议。
- **验收**：完整102+新增门控测试、adapter endpoint contract；不可变approval/plan/config/source/raw/log，原ToM1900条门控证据；1200完整后一次性统计，输出N/CI/资源/正负seed/失败/交互，明确区间不能证明的事。
- **输出**：`.local/reproduction/2026-10-15-receiver-v1/`、`research/reproduction/2026-10-15-receiver/`及任务日志；原statistical-v1只读。
