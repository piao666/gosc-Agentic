# MASBench B1准备与交付归档摘要

2026-11-16。当前归档base为4754bede84bb6e6defd8e646a63e81ccd6a20b4b；科研基线014b85d+冻结扩展、第三方MASBench c0301a650db95958924bb080192c09fef39389a5、模型manifest与历史run身份分别保留。本次只整理并提交已完成工作，不新增科研运行。

## 已完成与证据

- [RUN] B1-pre只读核验：现行服务默认1024，模型声明32768不等于有效context；词表/merges存在，但GGUF与Ollama模板身份不同，部署精确计数仍Pending。D1余52记录实际36问题家族34文章关联分量；D2仅为较弱隔离候选，未改registry。见[前置验收](masbench_b1_preflight_acceptance.md)。
- [RUN] 独立保护原型17合同通过；后续fixture-only Driver复用原client/application/wire，最终24项集成合同通过。20/22/23是前序版本，不能累加。内容涵盖持久分区预算、Prompt/私有观察配对、共同截止、受限假worker与外层中断恢复。见[集成验收](masbench_b1_driver_integration_acceptance_2026-11-10.md)及[整合合同](../protocols/masbench_b1_fixture_driver_contract_v1.md)。
- [CODE/HYPOTHESIS] [精确计数/context方案](../benchmarks/masbench_exact_context_implementation_plan_v1.md)固定同源Ollama commit并给出CPU词表计数/完整模板渲染路径与预算候选；没有安装Go、构建helper、改服务或把fixture绑定变成真实verified。
- [RUN] v4计算完成后发生quota管理写盘/receipt失败；最后文档同步及低空间重试失败也保留。用户明确授权后停止Laya服务，清除NextWork（含laya-env）与d2l-zh；删除前目录合计约5.46GiB，GOSC模型/实验原件不动。最终标准源同步20261116T024042Z核901文件、SHA差异0，回执两端一致。见[收尾记录](../logs/masbench-b1-integration-closeout-2026-11-16/closeout_report.md)。

## 归档边界

[RUN/管理] [6份小型输出](../artifacts/masbench-b1-20261116/README.md)逐字节复制原HPC JSON，合计10,454bytes，provenance列原路径/大小/SHA；无统计重算。run manifest/status/日志/source_snapshot及回传receipt按原始身份归档。12个重复source patch/tar共358,066,710bytes仍在本地/HPC且保持忽略；不删除旧tracked历史、原始outputs、模型或失败记录。

回传receipt采用原件SHA绑定的摘要索引，7份反复列出全历史的完整清单约8.47MB保留本地/HPC；Git只纳入mirror状态与本轮B1条目等紧凑索引，不将管理副本重复体积当新科研产物。

[RUN/管理] 本次只做Git、文件/哈希/链接、凭据与大文件核验；不重跑17/24或历史147+5，不把本次提交写成新HPC测试。73冻结源码及集成源对最终执行快照核验结果见本次Git管理日志。

## 当前关卡与下一步

**受测无模型工程支持域Go，真实B1 Blocked；G1/GP-ID科学No-Go保持。** 没有真实Reasoning任务或模型生成，Full相对No-A2A收益、内容排序贡献、实际精确tokenizer/context、服务取消、正式划分/功效均未成立。工程通过和Git归档不证明可发表。

下一步先固定受维护工具链archive/官方SHA、依赖清单与现有配额，再单独批准同源离线helper构建/计数合同；服务context改动、取消预检、真实四题诊断仍分别需批准，正式test/训练继续禁止。后续HPC工作先对齐本次新Git归档与源码manifest，不回写旧run。本次提交说明见[五部分记录](../../commit/2026-11-16-01-masbench-b1-safety-and-delivery.md)。
