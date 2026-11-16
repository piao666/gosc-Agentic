# 2026-11-16 / 01：MASBench B1无模型执行保护与交付收尾归档

- 日期与时区：2026-11-16，Asia/Shanghai。
- 用户授权与范围：“整理文件，提交一次github”，一次正常commit/push当前分支；不新增模型调用、任务实验、安装/服务更改或训练。
- 分支：research/progress-audit-2026-10-19。
- 提交前base HEAD：4754bede84bb6e6defd8e646a63e81ccd6a20b4b；远端同分支检查一致。
- 科研基线：014b85dfc472c45d8ea5f15e83e0c1ed8e938daf+冻结扩展；第三方MASBench c0301a650db95958924bb080192c09fef39389a5。
- 历史运行身份：按各run manifest/source_snapshot核验；不回填本次归档身份或自身提交哈希，旧“未提交/未推送”保留当时含义。

## 1. 提交内容

归档B1-pre A/B静态与只读核验、独立执行保护原型、fixture-only Driver/无模型合同、精确计数/context实施方案、全部阶段报告与管理/run元数据；补[阶段入口](../research/reports/masbench_b1_archive_summary_2026-11-16.md)及导航。

新增[6份小型证据白名单](../research/artifacts/masbench-b1-20261116/README.md)，合计10,454bytes，均与原outputs逐字节相同并有provenance。原始outputs仍忽略；12个source patch/tar共358,066,710bytes不新增入Git，继续保留本地/HPC；模型、环境、私人资料和数据正文不上传。针对新证据增加-text规则，既有历史不重新规范化。

7份约8.47MB完整回传清单含大量重复历史条目，本次保留本地/HPC原件并新增忽略规则；公开receipt_index保存原件SHA/大小、mirror状态及B1条目。run manifest/status/日志/source_snapshot仍按原路径归档，不删旧tracked证据。

## 2. 主要尝试

[CODE/RUN] 核对实际模型manifest、GGUF tokenizer/template元数据、当前默认context与环境；对冻结registry只做D1/D2描述性汇总，不改分组、题目或seed。

[CODE/RUN] 从独立Ledger/自有假进程保护扩为复用原ControlledClient、run_controlled、LocalAgent和ContractTransport的fixture Driver。补持久96+2分区、GET/输入输出/字节预算、Prompt/私有观察配对、共同操作截止、seccomp假worker、外层崩溃/超时与恢复不可增预算。没有改变原GOSC/Native/GP-ID/BF策略、原客户端和wire语义。

[CODE/HYPOTHESIS] 精确计数方案固定同源Ollama release commit，区分完整Go模板、实际engine tokenizer与runner生效窗口；仅形成构建/配置方案，未安装或调用模型。工具链官方archive与SHA仍Pending。

[RUN] 为恢复写盘，先只读盘点目录；用户明确批准清除NextWork/d2l-zh并单独批准停止仍运行的Laya服务后，才执行精确清理。旧quota失败及最后同步失败保留，之后标准同步补齐交付；未借清理重跑不利实验。

## 3. 结果

[RUN，历史] hpc-masbench-b1-preflight-20261110只读分析exit0；实际默认1024与架构32768分开，部署精确绑定未验证。D1余52行=36家族34文章分量；D2假设剩294行196家族，非同等严格隔离，registry不变。

[RUN，历史] hpc-masbench-b1-safety-20261110为17合同；最终hpc-masbench-b1-integration-v4-20261110为24合同全过，unittest2.691s、登记2.817053s。前序20/22/23保留，不累加；旧147+5与本次归档都未重跑。均非效果样本，不适用任务CI/显著性结论。

[RUN，失败保留] v4测试完成后quota导致dashboard/receipt管理失败，后续同步与重试也失败；不称全流程无失败。清理授权目标删除前合计5,861,621,760bytes（约5.46GiB），不保证等于独享配额释放；Laya仅SIGTERM，GOSC/Jupyter/Ollama及研究原件保留。最终源同步20261116T024042Z核901文件、SHA差异0，回执已镜像。

[RUN，本次管理] 暂存前/后轻量文件、证据SHA、冻结源、stage raw bytes、敏感/大文件、Markdown入口与固定说明格式检查，结果在 `research/logs/git-publish-2026-11-16/`；没有新的HPC计算或真实API调用。本次Git成功身份以包含本说明的提交及远端引用核验，不自填自身哈希。

## 4. 当前进展

**无模型工程受测支持域Go，真实B1 Blocked；科学G1/GP-ID No-Go保持。** 真实Reasoning episode/生成仍0，没有Full相对No-A2A收益、内容价值排序或可发表性结论。fixture的固定计数与verified不属于真实Qwen部署证据。

实际tokenizer/完整模板/生效num_ctx、真实服务取消/idle、模型CPU/GPU/wall与完整产物投影、正式D1/D2评价划分/统计功效均Pending。此次只归档，不放行正式test、训练、改服务、扩样本或新Benchmark。

## 5. 下一步安排

1. 核现有配额，固定受维护Go工具链官方archive/SHA与依赖清单，审阅同源离线计数helper的资源预算；安装/构建另获批准。
2. 先做CPU离线完整模板/token IDs合同，再单独审阅服务context、runtime等价与取消预检；不得自动置真实ContextBinding为verified。
3. 所有准入条件与明确模型调用授权满足后才申请四题能力screen；结果仍只是开发线索，失败不加复杂估计器挽救。
4. 下一次HPC工作先核Git HEAD和源码manifest对齐本次归档；不改写历史执行身份。本次不为归档而新增HPC运行或更新远端HPC Git引用。

## 本次提交验证

- 实际管理：git status/rev-parse/branch/remote/ls-remote/diff、轻量文件/哈希、六份provenance与73冻结源、暂存字节/敏感路径/大文件/链接/说明格式核验；不运行新pytest或研究分析。
- 通过/失败细节：见[Git管理日志](../research/logs/git-publish-2026-11-16/task_log.md)、precommit_file_audit.json、staged_audit.json。检查结果不自哈希；最后暂存统计以Git树为准。
- 原始记录空白例外：failed final_upload_stderr.txt一行尾空格、preflight_observed.json末空行原样保留；全量staged空白检查因此有提示，自有源/文档另排除这两个精确原件核验，不以修改证据消除提示。
- Git提交/推送：正常推送既有研究分支，不force；最终身份由Git历史与origin分支引用交叉核验。
- 未运行：真实模型/任务/训练、依赖安装、服务修改、新HPC合同及正式测试；本次均不需要且未获科学运行放行。
