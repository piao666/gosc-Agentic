# MASBench T2/T3 归档证据

[运行索引](run_index.json)包含 17 条 HPC 登记，14 次完成、3 次失败。完成的审计也可能核实一次现场失败。登记使用运行当时的 Git 和同步快照。 [产物来源](provenance.json)绑定 16 份逐字节复制的小型证据，记录原路径、大小和 SHA-256。 [回执索引](receipt_index.json)保存 7 份完整回执的原路径、SHA-256、数量和回传范围。

- **T2** 汇总 [窗口计数](t2-window-demand.json)、[首轮零派发](t2-first-attempt-summary.json)、[60 秒截止](t2-timeout-summary.json)、[最终现场](t2-final-summary.json)、[独立审计](t2-final-audit.json)和[服务切换](t2-service-transitions.jsonl)。 [报告](../../reports/masbench_t2_context_acceptance_2026-11-25.md)
- **T3 禁网** 汇总 [16 组彩排](t3-rehearsal.json)、[HDD 存储合同](t3-storage-contract.json)、[集成首轮失败](../../sync/runs/hpc-masbench-t3-integrated-contract-20261125/stderr.log)和[通过的复验](t3-integration-contract.json)。 [准入报告](../../reports/masbench_t3_preflight_2026-11-25.md)
- **T3 现场** 汇总 [51 次实际派发账本](t3-live-summary.json)、[HDD 索引](t3-hdd-manifest.json)和[离线评分](t3-audit.json)。工程验收通过，科学关卡 No-Go。 [报告](../../reports/masbench_t3_execution_2026-11-25.md)

真实题目、私有视图、完整请求与响应、传输原文、完整回执、历史源码包及同步清单由原数据通道保存。T3 的 684 份 HDD 原始文件由现场与独立审计各自读回核对。T1 的既有归档仍可独立核验。 [T1 验收归档](../masbench-t1-20261119/README.md)
