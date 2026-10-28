# GP-ID/BF结果汇总白名单

用户2026-10-28授权将这几轮结果梳理并提交GitHub。本目录只导出8份小型已完成HPC汇总JSON，逐字节复制，不重算、不改状态。原件、大小与SHA见[provenance.json](provenance.json)，`.gitattributes`对本目录禁用换行转换。

- [GP-ID成本合同](gp_id_cost_probe_summary.json)：52短fixture，效果N0，非收益证明。
- [156任务校准分析](gp_id_calibration_analysis.json)：独立N12、5主要比较均未过联合门槛，科学No-Go。
- [校准诊断审计](gp_id_calibration_diagnostic_audit.json)：全量核验但仍blocked_selection_budget，7条bits/AoI违规保留。
- [BF工程成本/结果](bf_selector_summary.json)、[原始行绑定](bf_selector_input_binding.json)、[独立审计](bf_selector_audit.json)、[验收状态](bf_selector_acceptance.json)：新显式版本工程Go，收益N0。
- [7个派生wire合同](bf_selector_repaired_wire_contracts.json)：control-only合成服务合同，映射时间/发送者，不是原历史mission重跑。

原`research/sync/runs/*/outputs/`仍由Git忽略，原始轨迹、gzip逐行观测、selector目录及完整任务记录保存在HPC和本地镜像。本目录不足以在没有原始数据的情况下独立重算全部统计；不能把汇总副本当作原始任务全量公开包。详细解释见[阶段汇总](../../reports/recent_rounds_summary_2026-10-28.md)。
