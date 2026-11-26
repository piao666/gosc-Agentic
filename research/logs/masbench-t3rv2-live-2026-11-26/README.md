# 公平终答独立真实合成验收

2026-11-26 Asia/Shanghai。两个人工请求完成；事后独立审计与完整回传完成。**受测服务执行/证据闭环通过；长输入格式失败、原2000秒连续完整交付超期保留。** 未运行真实题目能力实验，未提交推送。

- [最终研究报告](../../reports/masbench_t3rv2_live_acceptance_2026-11-26.md)
- [D01–D12实际矩阵](acceptance_matrix.md)、[五个run命令/身份索引](run_index.json)
- [任务brief](task_brief.md)、[任务日志](task_log.md)、[保护哈希](protection_check.json)
- [执行预算](../../protocols/masbench_t3rv2_live_budget_2026-11-26.md)、[AS继承修订](../../protocols/masbench_t3rv2_lifecycle_inheritance_revision_2026-11-26.md)、[事后续办登记](../../protocols/masbench_t3rv2_postdeadline_closeout_2026-11-26.md)
- [实际单次授权](../../protocols/masbench_t3rv2_live_authorization_2026-11-26.json)、[原人工输入](../masbench-t3rv2-deployment-2026-11-26/probe_inputs.json)
- [小型证据逐字节副本](../../artifacts/masbench-t3rv2-live-20261126/README.md)
- [完整回传receipt](../../sync/receipts/20261126-t3rv2-live-d81f79a776.json)：458文件、7763327B，含首轮失败、HDD原件与三套合成fixture常规文件。HPC原件保留，受控本地镜像在`research/sync/runs/hpc-t3rv2i-live-*`。
- [有界T3条件申请（未批准、不可直接执行）](../../protocols/masbench_t3rv2_bounded_diagnosis_request_2026-11-26.md)、[交付SHA](delivery_manifest.json)

HPC实际原件：`/hdd/u202520081000097/gosc-t3rv2-live/hpc-t3rv2i-live-probe-20261126/`。实际运行source为20261126T032819Z；审计source为20261126T064855Z。二者不互相改写。模型恰2次，不补发、不更改格式规则；service/GPU是用户已批准监测停止语义，不称硬隔离。
