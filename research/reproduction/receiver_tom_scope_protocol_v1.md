# Receiver-D1：已批准的ToM路径限定机制诊断

批准依据：用户在本轮对“是否批准按ToM路径限定方案继续”回复“确认”；对应已提交95ce323的`2026-10-15-statistical/receiver_scope_proposal.md`。本文件记录新准入，不修改此前statistical_protocol_v1或其结果。

## 准入与证据

strict R4保持failed；R4-S1保持inconclusive(100 equivalent/4 inconclusive)。本次新准入名为`tom_path_diagnostic_only`，仅允许原gosc/ToM的探索性因果机制诊断，不能标作总体R4通过、方法开发或强baseline/SOTA比较。

执行前校验原5200条raw哈希、plan/source/config、统计gate；其中gosc的frontier700、private600、headline600共1900条已有保存字段须无差异。headline只提供task与symbols，不声称未保存字段一致。新runner须显式选择此准入并加载绑定方案/本协议哈希的用户批准记录；旧default门控仍拒绝inconclusive。

## 不改变的实验与统计

沿用原`diagnostic_preregistration.json`（2026-10-15T02:22:25Z前已冻结）：default/W50/snr-5三search设置，原eta、Planner、scheduler/channel、候选消息格式；shared/private/position/joint四模式；seeds4000–4099每设置每模式N=100，共1200条。没有训练/调参、eval或calibration seed复用、新任务或LLM。

主要终点completion_time；收益=shared−intervention，正值更快。private/position对shared跨3设置构成6个主要比较；按整个mission seed配对bootstrap4000次、统计seed0，报告95%及Bonferroni6 percentile区间，实用阈值为shared均值5%。沿用`summarize.diagnostic`，joint和交互为次要、不混进6项主要family。

同时报告点估计≥5%、family区间下界>0、family区间下界>5%三个层次；原工具已给出最后一项。若称某单因素在本诊断三设置“稳定实用”，要求三设置的family区间下界均超过各自5%阈值。单设置信号只能作条件性结果；跨零不证明无作用，区间上界低于5%才支持排除对应大小的收益（限本设置/模型）。Bonferroni尾部在4000重采样中样本少，区间为近似、存在Monte Carlo误差，不能宣称精确覆盖。

## 源码事实与公平边界

[CODE] `extensions/receiver_oracle.py`只改变`TeamModel`视图；shared/joint对应原tom_oracle False/True，两个单因子由原独立mask构造。base与realistic两路径contract均测试，原实际Agent、scheduler、channel不替换。

[CODE] `gosc/voi.py:TeamModel.__init__/_expected_utility`中的dist同时用于receiver预测分数及u_true的距离折扣；position的效果不是纯policy预测误差修正。private包括pending_llr和confirmed_pending；joint仍沿用原softmax、shared deconfliction信息等代理，不是实际最优价值或任务收益上界。此轮不新增第五模式拆分这些机制。

同步/查询状态免费且oracle不可部署；固定eta不意味着实际UL/DL等成本。任务和通信效果必须一起读；不能从本结果宣称净收益、LLM效果、性能缺陷的普遍性或创新成立。源作者joint对照已存在，新内容仅是透明的因子拆分及独立seed诊断。

## 执行与停止

主Windows .venv/lock不变；先运行完整测试与门控/adapter契约。独立`2026-10-15-receiver-v1`目录，approval/准入证据/plan/config/source/raw和完成manifest均exclusive-create。≤4workers，每worker1数值线程，25分钟上限；不覆盖statistical-v1、原results/cache/PDF。

完成全部1200再分析；缺seed、异常、非有限数或保护哈希变化失败保留输出。不因中期收益/不利结果筛选或早停。完成报告后停止；若无稳定实用收益，不继续堆模块。下一轮是否做等成本或新任务要单独确定。
