# 证据索引

| 断言 | 原始证据 |
|---|---|
| D1由用户决定，不是静默换划分 | 本会话异步明确回复；[D1决策](../../benchmarks/masbench_d1_evaluation_decision_2026-11-16.md) |
| 当前主机/CPU/RAM/服务状态 | [只读核验](readonly_inventory.json) |
| 远端归档只快进引用，901源一致 | [快进回执](archive_reconcile_stdout.json) |
| 官方模块网络不可达、镜像可达 | [公共metadata诊断](module_transport_probe.json) |
| 只收回本次失败占位 | [回收记录](own_reservation_reclaimed.json) |
| Go/签名模块与7参考源码一致、最终缺C++ | [最后build.json](../../sync/runs/hpc-masbench-context-build-v5-20261116/outputs/build.json)、[compile.log](../../sync/runs/hpc-masbench-context-build-v5-20261116/outputs/compile.log)、[status](../../sync/runs/hpc-masbench-context-build-v5-20261116/status.json) |
| 所有失败保留且回传 | 五个run的manifest/status/artifacts；最后[receipt](../../sync/receipts/20261116T074353Z-31a565.json)以及报告列前四receipt |
| helper/部署还没通过 | [当前停止状态](../../protocols/masbench_context_build_status_2026-11-16.json)、[推进报告](../../reports/masbench_context_deployment_progress_2026-11-16.md) |
| 官方来源 | [Go下载JSON](https://go.dev/dl/?mode=json)、[支持政策](https://go.dev/doc/devel/release)、[模块zip规则](https://go.dev/ref/mod#zip-files)；source_reference中固定commit文件 |

source_reference是只读审查快照，不是已构建依赖安装树。记录的[PAPER]效果范围没有新增。stdout/stderr/产物与报告分别保留，未重写失败日志使其通过。
