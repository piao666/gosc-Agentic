# T3-R-v2-T 最终诊断与离线归因归档

原四个已曝光开发家族的唯一真实诊断已结束。48 次生成、独立审计和 616 文件按时回传均通过。两种条件合计有效终答 0/16，配对平均 ΔF1=0。离线复核确认 15 个无效终答均因来源声明失败，仅去掉逗号空格只让 1 个原输出通过冻结解析。该输出仍遗漏子问，且结论与可见证据冲突。维持科学 No-Go，暂缓 T4。

- [现场准入报告](../../reports/masbench_t3rv2t_final_admission_2026-11-26.md)、[8 项合同](contract.json)、[初始计数与现场摘要](admission.json)
- [真实诊断报告](../../reports/masbench_t3rv2t_live_final_2026-11-26.md)、[执行摘要](task_summary.json)、[独立审计](live_audit.json)、[完整回传凭证](live_receipt.json)
- [16 个终答和 8 条消息链的失败矩阵](../../reports/masbench_t3rv2t_final_failure_attribution_2026-11-26.md)、[评分摘要](offline_score.json)、[逐条结构与来源哈希](final_attribution.json)
- [运行身份、原件 SHA 与回传索引](archive_index.json)

七个 JSON 为既有小型报告或回执的原字节副本。完整提示、私有视图、原始回复、封存数据、运行包及实际批准文件保存在 HPC 与本地受控镜像。仓库保留 `approved: false` 的原冻结候选，实际运行授权 SHA 由索引绑定。提交日期与运行身份分别记录。
