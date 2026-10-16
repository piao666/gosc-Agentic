# Research Task Brief — approved Receiver-CF v1 pilot

- 授权：用户2026-10-16“批准”前一报告具体协议/执行器/8missions/128branches/2workers/15min提案。base37cf326f163a25faafc6c3d439b7068e6528f990；启动clean；沿用限定ToM诊断准入，原strict R4 failed、R4-S1 inconclusive不改判。
- RQ：[HYPOTHESIS] 原生已选E/I尝试的解码成功/失败是否改变下次真实Planner目标及未来任务结果，unclipped ToM能否排序这种条件效果？不开发新估值器，不把合成反例/8missions当稳定论文收益。
- 前人成果：[PAPER/CODE] GOSC已有免费完整buffer瞬时交付反事实；BANDMAS已有离线replay→廉价在线估值。这里是固定原生可行尝试/时序/ACK下的诊断，不声称新颖性。
- 修改：仅新增extensions/counterfactual.py、experiments_ext/run_receiver_cf.py及分析脚本、tests_ext/test_receiver_cf.py、research新报告/日志；不改gosc、原实验/测试/results/缓存、旧协议或PDF。
- 设计：冻结Config()、seeds5000–5007开发集、t=8/24、outcome-blind SHA选择每点一个原生已选E/I、4个stream-coupled repetitions、success/failure；最多128branches、8native前缀。先通过native/no-op回放与ACK/queue/RNG/多包/终止契约，再执行。
- 成本：2workers各1数值线程，pilot wall900s硬上限，超时保留partial；开发/短契约/全套测试单独计时。无下载/新依赖/GPU/Ollama/API；既有Python3.12.10环境。
- 反例：无可用尝试、零/负dT、无目标改变、简单特征同样好、少clusters导致CI未定义/不稳定均保留；不更换seed/任务追正结果。
- 验收：不可变source/config/seed/protocol/approval manifest、逐branch原始结果/状态hash/tape/目标/成本/异常、无隐私状态入online特征、mission级统计和cluster CI、上游保护hash；本轮按授权运行后报告并停止，不自动扩大实验或训练模型。
