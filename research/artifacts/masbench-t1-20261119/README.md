# MASBench T1 验收证据索引

[T1 验证总报告](../../reports/masbench_t1_validation_archive_2026-11-19.md)串起 11 月 17 日前置条件与 11 月 18–19 日的真实接线、失败和复验。T1 本身的 HPC 登记共 **32 条**，22 条 completed、10 条 failed。所有登记状态和实际命令见 [运行索引](run_index.json)，包括结束时间和退出码为未知的两条失败。完成的独立审计可能核实的是一次现场失败。

- [产物来源](provenance.json)逐件绑定 **30 份**、共 **904,353 bytes** 的摘要、审计、控制链和预算账本。文件按原登记 SHA-256 校验并逐字节复制。控制链可能包含登记器预分配产生的零字节填充。
- [回执索引](receipt_index.json)记录 **10 份**完整原回执、合计 **9,946,297 bytes** 的路径、SHA-256 以及其中的 T1 条目。原始全文保留在本地与 HPC 的原路径。曾遇 EDQUOT 的 `20261118T080840Z-e03b60` 在 HPC 有可复原且已验原始 SHA 的 gzip，详见[当时的恢复记录](../../reports/masbench_t1_runner_recheck_2026-11-18.md)。
- [最终复验摘要](hpc-masbench-t1b-formal-runner-retest-20261119__summary.json)与[独立审计](hpc-masbench-t1b-formal-runner-retest-audit-20261119__audit.json)记录现有 1024 窗口工程验收通过。首轮失败的 [四例证据](hpc-masbench-t1b-formal-audit-detail-20261119__audit.json)仍保留失败判定。真实题目曝光为零。
- [HDD 清理及读回](../../reports/hpc_storage_and_t1_recovery_2026-11-19.md)、[noise 定位](../../sync/runs/resume-radio-noise-20261020/ssd_archive_location.json)、[overhead 定位](../../sync/runs/resume-radio-overhead-20261020/ssd_archive_location.json)和[最终旧锁归档凭证](../../logs/masbench-t1-driver-2026-11-17/t1_formal_marker_recovery_applied_20261119.json)保留两次 HDD 归档的出处及核验结果。

全量 `outputs/`、源码补丁、源码 tar 包和失效写入的空临时文件保留于原数据通道。运行索引所列提交及源码快照均为执行时身份。
