# MASBench B1：无模型Driver整合与精确计数方案验收

2026-11-10 Asia/Shanghai。**本轮授权范围完成：无模型Driver受测支持域Go，精确计数/context实施方案已交付；真实B1仍Blocked。** 新增最终24项HPC合同通过。它们不是真实Reasoning episode、模型能力或通信收益证据。G1/GP-ID科学No-Go、正式test/训练禁令保持。

交付：[计数/context方案](../benchmarks/masbench_exact_context_implementation_plan_v1.md)、[机器可读提案](../protocols/masbench_exact_context_implementation_plan_v1.json)、[整合保护合同](../protocols/masbench_b1_fixture_driver_contract_v1.md)。旧B1-pre四份报告、原始失败、registry与历史run不改写。

## 1. 真实版本、授权及证据

[RUN] 启动时本地已有上轮未提交成果，与会话证据一致，完整保留。本地/HPC Git HEAD为4754bede84bb6e6defd8e646a63e81ccd6a20b4b，研究分支和origin未变；本轮代码以dirty source_snapshot绑定。科研基线014b85d+冻结扩展、第三方MASBench c0301a650db95958924bb080192c09fef39389a5、旧模型manifest/历史执行身份分别保留。远端旧index状态仍如实保存在manifest，不用D/MM标记推断源文件被删；同步逐文件SHA才是运行文件证据。

[RUN] SSH只读核UID8301880/n1、2CPU/24GiB、kernel5.4.0-100-generic、无running任务；gcc/cmake/timeout/unshare可定位，go不在PATH。进程8964白名单仍1024 context，新engine/experiment环境未设置；未读其他敏感环境。此为配置事实，不是当前模型实际加载/推理证明。

[CODE] 本轮新增 `extensions/masbench_reasoning/fixture_driver.py`，复用且不修改原client/application/wire/registry及先前execution_safety。新增HPC入口 `experiments_ext/masbench_b1_integration_contract.py` 与 `tests_ext/test_masbench_fixture_driver.py`。没有改GOSC/Native/GP-ID/BF策略、原候选、数据/gold/评分或批准真实调用。

## 2. 实现的实际行为

| 机制 [CODE] | 本轮实现 | 主要验收 |
|---|---|---|
| 原接口整合 | FixtureCampaign→原run_controlled→原ControlledClient→受限假RPC；原LocalAgent/ContractTransport语义保留 | base/protocol × Full/No-A2A原路径、交付进入下一请求、No-A2A仍可最终作答 |
| 公平配对 | family/style对应的PrivateView及**实际初始请求**SHA绑定；fresh Agent检查 | 私有证据和Prompt分别漂移均在第二episode启动前拒绝 |
| 统一账本 | CampaignLedger持久身份/plan、GET额度、96任务+2合成分区、输入/最大输出预留；失败不退款 | 分区不可互借、跨episode/resume不能清零、不利任务不能重跑 |
| 审计与wire成本 | 原client audit_sink换为统一emit；仅旁观flush原wire事件/CPU/offers，所有产物+ledger统一cap | Full实际合成帧非零，No-A2A帧0；JSONL/wire经同一主账本，usage缺失保留null |
| 字节停止 | 总cap中预留4096B控制日志，其余给主Ledger；未知文件/符号链接/已存artifact变化拒绝 | 额度耗尽不超受控cap，原started仍在分母；resume篡改拒绝 |
| 假worker限制 | Linux x86_64 seccomp默认拒绝，关继承FD，仅IPC写；不许open/socket/fork/exec/stdout；有界CPU/地址空间/IPC | 实际权限拒绝fixture通过；无保护回退路径 |
| 操作共同截止 | generate开始固定绝对截止，metadata、audit fsync、generation共用 | 审计故意延迟后不能再得到完整generation时间；metadata超时也持久fence |
| 响应失败与结算 | 旧客户端完整验证后再settle；截断、usage偏差、worker错误/超大返回均failed | 失败不写completed，已预留额度不退款 |
| 外层监督 | 独立进程监督controller session；退出/崩溃/超时均KILL owned group，guard-init在派发前持久绑定boot/起点/wall/argv | 实际Campaign生成挂起时从外层中断，resume保留inflight与started；不能增大wall或换命令 |

[RUN] 新测试中的“Full和No-A2A都输出fixture-final”由固定响应决定，只证明原生最终答案能力与消息路径，不能用于通信必要性、准确率或F1结论。固定四token和全零fixture manifest不是实际Qwen tokens；没有把synthetic ContextBinding写成真实verified。

## 3. HPC结果、失败和回传

| run（均位于research/sync/runs） | 本次合同数 | 登记elapsed | 执行 / 管理状态 |
|---|---:|---:|---|
| hpc-masbench-b1-integration-20261110 | 20 | 1.663927s | tests completed，exit0，完整回传 |
| hpc-masbench-b1-integration-v2-20261110 | 22 | 1.849613s | 增补Prompt配对与audit共同截止后全套通过 |
| hpc-masbench-b1-integration-v3-20261110 | 23 | 2.754212s | 增补外层→实际Campaign整链中断后全套通过 |
| **hpc-masbench-b1-integration-v4-20261110** | **24** | **2.817053s** | **最终24/24通过，0failure/0error；随后管理写盘遇quota** |

[RUN] 最终unittest2.691s、Python3.11.15，单CPU合同顺序执行；wrapper timeout125s、alarm120s、CPU60s、单文件16MiB保护。原147+5与上轮17没有重跑；20/22/23为前序版本，不能相加成独立样本或单次总测试数。新增的修订均对应复查发现的具体公平性/预算缺口，不是改变任务目标。没有真实模型/HTTP、数据集任务或GPU加载。

[RUN / 管理失败] v4的status已写completed/exit0，24项结果与日志完整，但随后refresh_dashboard临时文件写入报 `OSError: [Errno 122] Disk quota exceeded`；launch外层exit1，首次pull回执上行也失败。**不把测试通过等同这次launch全流程通过，不删除失败记录，不重跑合同来消除管理失败。** 本地已有receipt `20261110T034339Z-eaef8e.json`，当时尚未成功写回HPC。

[RUN] 仅清理此前由本助手创建、已完成使用的临时Git传输包 `/tmp/gosc-b1-pre-4754bed.bundle`：路径/regular-file/非symlink核验后SHA匹配23e1c490…aba30，释放43,202,517bytes。没有删除实验数据、失败日志、模型或源码快照。随后常规 `hpc_runs.py pull` 成功刷新dashboard、回传差异并将新receipt `20261110T034520Z-f62d10`写回HPC，all_outputs_mirrored=true；原失败保留。quota命令不可用，没有虚报账户剩余空间或声称可满足后续4GiB构建提案。

[RUN] 四个run的源同步分别20261110T033157Z/033550Z/033925Z/034250Z，857/858/860/860文件，mismatch0。前序receipt分别033305Z-7b64a5、033649Z-485991、034016Z-ef567d；最终以034520Z-f62d10的完整回传与上行完成为准。实际回传bytes/source snapshot哈希/argv/资源和产物SHA汇总在本轮experiment_manifest.json，原件在各run manifest/status/artifacts/stdout/stderr。

## 4. 精确计数/context方案的新增结论

[CODE] 已从官方release核定Ollama v0.11.11 source commit92b96d54efd6b49322b7cf046f9a0dc16b00cd0a；源码有VocabOnly与legacy Tokenize(false,true)路径，Go模块最低声明1.24.0。首选方案是固定同源template/full-message renderer与实际engine词表计数helper，只做CPU离线计数、不载tensor/推理。所有来源链接、接口、边界fixture、身份链与反证条件见方案，不编造helper已存在或测试通过。

[RUN / Pending] HPC无Go工具链；官方Go下载metadata访问失败，受维护兼容archive版本/官方SHA尚未冻结。因此方案是可审阅候选，**还不是可执行安装清单**。提议构建硬cap1800s/2CPU/4GiB RAM/下载≤1GiB/新增峰值磁盘≤4GiB、离线合同120s/2GiB/16MiB；均非测得投影或当前授权，须先核配额/官方hash/依赖清单。当前储存吃紧本身就是实际阻断，不能为推进而默装依赖。

[HYPOTHESIS] 服务32768只是后续独立配置候选，现行1024未改；model metadata、helper计数与实际runner num_ctx必须一致并有逐请求无截断证据，之后才能建立真实ContextBinding。真实取消/idle核验与GPU加载需要另批合成请求预算；不能顺手启动四题诊断。

## 5. 限制与Go/No-Go

[CODE / 限制] seccomp只在本HPC/Linux x86_64假worker支持域验证，不是实测跨平台工具，也不适合需要文件/网络的真实tokenizer或Ollama client。fork继承地址空间不是私有信息安全隔离。控制器和外层监督器仍属可信程序；整个账户/任意外部写入不受该受控目录cap保护，外层监督器本身被强杀不在通过合同内。KILL/reap有有限清理时间，不承诺内核不可中断任务在deadline瞬间退出。

[HYPOTHESIS / 未验收] 真正模型客户端的隔离与取消、实际runner context/tokenizer等价、真实推理CPU/GPU/wall/usage、完整最坏产物投影、正式D1/D2划分/统计功效均Pending。不得把本次合成wire的字节或CPU slot换算成实际模型tokens/推理时延，也不把24合同写成算法贡献。

| 决策 | 结论 |
|---|---|
| 本轮“方案＋无模型Driver整合保护” | **Go，限已验收支持域** |
| 精确部署计数/context绑定 | **Pending**；未安装/构建/改服务 |
| 同源离线helper准备 | **Conditional Go建议**；先冻结工具链hash/依赖与可用配额，再另获安装/构建授权 |
| 真实B1能力screen | **Blocked**；未获本轮真实生成授权，且关键证据缺失 |
| 正式test/复杂估值器训练 | **No-Go** |
| G1、GP-ID科学负结果 | **No-Go保持** |

建议下一步先解决工具链官方archive与存储预算，批准隔离同源helper构建/无模型计数合同；之后再审服务context/取消预检。四题身份、Prompt主辅、98请求/6000s/256MiB及科学停止规则均不在本轮改动范围。完成本轮后停止，不自动下载或进入B1。

# Research Task Report

- **Research Question / Hypothesis**: 原客户端/消息闭环能否被持久、不可重置预算与自有进程停止链实际约束；精确计数/context如何合法获得。
- **已核验前人工作**: [CODE]Ollama固定release/source、template、Tokenize与go.mod；本轮未新增论文效果结论，[PAPER]沿用既有范围，不声称重读全部文献。
- **实际阅读源码**: client.py LivePermit/ContextBinding/ControlledClient/JsonlAuditSink/run_controlled；application.py LocalAgent/PrivateView；wire.py ContractTransport；execution_safety.py Ledger；registry.py、hpc_runs/sync_hpc/hpc_ollama及上一轮审查；实际新入口见上。
- **本轮新增或修改**: fixture_driver.py、集成合同/入口、计数方案md/json、新整合合同与本验收，日志/证据/manifest和当前导航。原核心、旧客户端、前轮四报告及73冻结源码未改。
- **实际运行**: 四个HPC登记合同，模型/seed均不适用；无真实任务和生成。每次实际argv与同步hash见本轮experiment_manifest，下面给共同入口。
- **测试与结果**: [RUN]最终24通过；前序20/22/23保留，不累加。没有新真实任务分数、CI、N或统计检验。
- **失败/负面证据**: Go metadata与GitHub tag API访问失败（source SHA后由官方release核定）；v4测试后quota导致登记收尾与receipt上行失败，恢复记录如上；真实计数/context/取消仍未验收，不抹掉旧失败。
- **与原 GOSC 的差异**: 仅独立研究执行保护；估值/候选/调度/无线策略与G1/GP-ID/BF不变。
- **公平性与泄露检查**: 两条件绑定初始Prompt与自有观察，No-A2A自主答案保留；全started分母、失败不重跑；无gold在线输入，无真实题目/模型曝光或registry修订。
- **成本**: 四run elapsed合计9.084805s，runner RSS约83MiB且含Git管理子进程，不是模型峰值。GPU/实际模型token/推理wall未测；合成无线账本只作合同。自动source快照使每次管理回传约60MB，四轮管理成本约241MB，须计入存储规划；不伪称是256MiB科学产物预算内的推理费用。
- **可否进入下一阶段**: 本轮受测工程Go；计数helper构建Conditional Go建议，真实B1 Blocked，正式test/训练No-Go。
- **用户需要批准的下一步**: 工具链archive/hash/依赖和配额具体化后批准同源离线helper准备；服务更改、真实生成/取消预检、真实四题仍独立批准。本轮无Git commit/push。

```text
python scripts/hpc_runs.py launch --run-id <表内唯一run-id> --kind test --stage MASBench-B1-fixture-integration --purpose <manifest中实际说明> -- /usr/bin/timeout 125s {python} experiments_ext/masbench_b1_integration_contract.py
python scripts/hpc_runs.py pull
```

[RUN] 最终本地轻量文件/产物SHA/73冻结源/新代码对v4 source_snapshot核验见 `research/logs/masbench-b1-integration-2026-11-10/management_verification.json`。最后文档同步结果单列final_upload_status.json；如quota阻断，不把本地交付称为HPC上行完成，也不重复运行科学合同。
