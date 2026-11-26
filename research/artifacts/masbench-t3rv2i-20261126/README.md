# T3-R-v2-I 小型非私有验收证据

2026-11-26。所有七份复制JSON与源文件逐字节SHA一致，见[copy_provenance.json](copy_provenance.json)。没有真实MASBench正文/gold/LLM请求响应或模型权重。

- [contract_results.json](contract_results.json)：新版专用54 pytest，其中C01–C32参数化53 call+1桥接；不是问题N。
- [legacy_results.json](legacy_results.json)：新跑旧synthetic adapter67通过，单列支持域。
- [independent_audit.json](independent_audit.json)：stdlib独立审计通过，46 journal、5向量、39冻结文件、memory/帧/计数绑定。
- [pressure_summary.json](pressure_summary.json)：只读重建35个合成请求字节压力；该summary如实保留首次精确计数OOM，后续获批补验见下一项，不改旧状态。
- [counter_recheck.json](counter_recheck.json)、[counter_process.json](counter_process.json)：获批额外1次/2GiB AS后的实际精确计数，35条最大15046tokens，未创建tensor context。
- [scoped_receipt.json](scoped_receipt.json)：9 run119当前文件21131910B全量回传，恢复218归档原文件，259原artifact SHA通过；全部失败亦保留。
- [run_index.json](run_index.json)：完整实际命令、Git/sync身份、9run状态和资源，5completed/4failed；执行完成不冒充研究成功。

完整stdout/stderr/JUnit、原始合成prefix/journal归档、counter原stdout压缩件、源码snapshot/patch/untracked包在`research/sync/runs/hpc-t3rv2i-*`及HPC原run，已定向回传；不自动纳入Git。pytest convenience目录按官方策略不镜像，其regular原字节已入归档。

源码与报告入口：[最终报告](../../reports/masbench_t3rv2i_implementation_acceptance_2026-11-26.md)、[逐项矩阵](../../logs/masbench-t3rv2i-2026-11-25/acceptance_matrix.md)。工程Go仅限无模型支持域；真实部署/真实能力/内容价值/无线净收益未建立。提交推送另批。
