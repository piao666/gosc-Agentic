# Evidence Index

- [审阅结论与执行建议](../../reports/masbench_reasoning_data_decision_review_2026-11-03.md)
- [旧验收报告](../../reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)：300行/200问题/67合同及支持域。
- [分组源码](../../../scripts/masbench_reasoning_data_audit.py)：68行title边、81行支持句文本边、120–123行hash分桶。
- [既有HPC followup](../../sync/runs/hpc-masbench-data-followup-20261103/outputs/data_followup.json)：前3组easy/hard差异、indices244/245同一问题、空句与索引诊断。
- [无模型应用入口](../../../extensions/masbench_reasoning/application.py)：generate_fixed/run_fixed，当前没有真实模型循环。
- [模型环境边界](../../benchmarks/masbench_reasoning_environment_v1.md)：历史metadata/依赖通过，实际chat/context未验。
- [上行状态原件](../masbench-adapter-contract-2026-11-03/final_upload_status.json)：旧SSH失败，不是本轮实测。
