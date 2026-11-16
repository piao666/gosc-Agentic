# Research Task Report — B1整合交付收尾与精确目录清理

日期2026-11-16 Asia/Shanghai。用户先要求继续完成原交付，随后明确允许清除NextWork、d2l-zh和其中的laya-env；发现Laya服务活动后，用户另行明确批准停止该服务再删除NextWork。此次不扩大科研运行权限。

- **Research Question / Hypothesis**: 本轮仅关闭文件同步/配额阻断，不检验任务价值或模型能力。
- **已核验前人工作**: [PAPER]未新增论文阅读/结论；沿用11月10日静态规格与报告。
- **实际阅读源码**: [CODE]sync_hpc.py的备份/HEAD/源文件SHA及running保护；前轮报告、manifest与24项合同证据。原算法及client/application/wire/registry不改。
- **本轮新增或修改**: 本目录brief、磁盘管理盘点、精确删除授权、进程核验、cleanup_result及收尾记录；更新研究入口和当前状态。保留所有前轮未提交成果与失败记录。
- **实际运行**: [RUN]SSH只读Git/UID/进程核验；有时限的du管理盘点；仅停止已批准的PID57695 Laya服务；Python shutil.rmtree删除两个已核实的绝对目录；项目目录1MiB写盘检查；标准python scripts/sync_hpc.py源/文档同步。没有项目测试、仿真、LLM、训练、依赖安装或Git commit/push。
- **测试与结果**: [RUN，历史]hpc-masbench-b1-integration-v4-20261110最终24合同通过，本轮不重跑；其原件、产物SHA与新源码身份轻量核验见final_verification.json。新的清理不是科研测试，空间检查不是模型能力验收。
- **失败/负面证据**: 11月10日quota造成登记收尾/回执上行失败、最后同步及重试失败均保留；11月16日清理前的原manifest补齐也因quota失败。全账户du60s、部分环境目录25s到时未完成，不将局部占比冒称账户全量。临时包位于/tmp，删除它不代表项目配额恢复。
- **与原 GOSC 的差异**: 无核心算法、数据、候选、调度或wire变动。
- **公平性与泄露检查**: 没有真实题目/gold/模型曝光，没有更换registry或主Prompt；保持原No-A2A答案能力和全started分母合同。
- **成本**: 删除前du为NextWork 5,619,167,232bytes、d2l-zh 242,454,528bytes，共5,861,621,760bytes（约5.46GiB），laya-env包含其中、不重复计数。此为目录占用口径，不保证等于独享可释放配额。仅原Laya服务SIGTERM，未用SIGKILL、未停止JupyterLab/Ollama；GOSC数据/模型/失败/源码快照保留。写入检查成功，随后标准同步的状态/文件数/完整SHA验证由source_sync_receipt.json独立记录，不伪造账户剩余配额。
- **可否进入下一阶段**: 原24项无模型集成支持域Go；科学G1/GP-ID No-Go保持。精确部署计数/context、服务取消与真实B1准入仍Pending/Blocked，正式test/训练不放行。
- **用户需要批准的下一步**: 如推进同源离线计数helper，仍须固定工具链官方archive/hash、依赖与资源清单并另获安装/构建授权；实际服务变更/模型生成独立批准。本轮收尾完成后停止。

## 目录与进程边界

[RUN] 目标为 `/home/u202520081000097/NextWork`、`/home/u202520081000097/d2l-zh`。删除前确认UID8301880、解析路径等于原始绝对路径、非symlink、无嵌套mount、不包含GOSC；GOSC现用venv/Reasoning环境/Ollama服务入口无目标依赖。检测出Laya服务PID57695的脚本属于NextWork而cwd为RAG，获得专项停止授权后才继续。三个仅cwd位于NextWork的空闲Jupyter bash未终止；JupyterLab及RAG目录均未删除。

[RUN] cleanup_result.json逐目标记录删除完成；项目1MiB创建/fsync/删除管理检查通过。此前failed repair临时文件与原备份不删除、不改写历史run。配额解除后改回标准同步，无须继续执行finish_manifest_delta.py或重跑原合同。

## 当前交付入口

- [原无模型Driver验收](../../reports/masbench_b1_driver_integration_acceptance_2026-11-10.md)
- [精确计数/context实施方案](../../benchmarks/masbench_exact_context_implementation_plan_v1.md)
- [Driver整合合同](../../protocols/masbench_b1_fixture_driver_contract_v1.md)

当前Git归档仍4754bede84bb6e6defd8e646a63e81ccd6a20b4b，科研基线014b85d+冻结扩展、第三方MASBench c0301a6、模型manifest及历史run版本均保留。新同步不是新的实验身份。
