# T3-R-v2 真实部署准入核查入口

2026-11-26 Asia/Shanghai。**真实部署Blocked，未完成；没有真实生成/服务切换/新增测试，尚未释放T3能力诊断申请。** 本目录行政只读记录不是hpc_runs完成记录。

- [最终研究任务报告](../../reports/masbench_t3rv2_deployment_admission_2026-11-26.md)
- [现场准入矩阵](admission_matrix.md)
- [部署补齐合同](../../protocols/masbench_t3rv2_deployment_admission_v1_2026-11-26.md)
- [具体缓存迁移及资源合同选择申请](../../protocols/masbench_t3rv2_deployment_remediation_request_2026-11-26.md)
- [未批准的纯合成部署预检计划](../../protocols/masbench_t3rv2_deployment_probe_candidate_2026-11-26.json)、[完整字面人工输入](probe_inputs.json)
- [HPC原始只读快照](hpc_readonly_inventory.json)、[只读采集脚本](readonly_inventory.py)；脚本仅通过SSH stdin在HPC执行，stdout保存本地，无HPC文件写入。
- [前序48份交付保护SHA](protection_check.json)、[任务brief](task_brief.md)、[任务日志](task_log.md)、[管理行为manifest](experiment_manifest.json)
- [交付SHA清单](delivery_manifest.json)，不自哈希；本轮数据来源不含真实题文/gold。

当前2CPU/24GiB总容器、服务0.11.11、固定qwen清单等身份核过；服务仍1024，SSD个人余6594560B，子树/GPU硬上限无证据。三个依赖下载缓存共35074439B的原样HDD迁移待批。32MiB无模型准入余量尚未满足，不同期望后续64MiB真实预检余量已满足。

待用户决定是否允许上述具体迁移及接受监测停止合同；之后才能继续独立live接入及D01–D12。真实部署通过前，不申请实际T3能力调用、不进入T4；Git提交推送另行指示。
