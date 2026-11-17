# 2026-11-17 / 01：D1决定、同源计数与真实部署有限域验收完整归档

- 日期与时区：2026-11-17，Asia/Shanghai。
- 用户授权：“写一份详细的提交报告（包含从上次提交前到本轮的所有验证），整合本地改动，提交一次github”；一次正常commit/push当前分支。
- 分支：`research/progress-audit-2026-10-19`；提交前base HEAD与远端均为 `916289ba20fd9808a3673af0aebf175bfc830ccc`。
- 上次提交说明：[2026-11-16-01](2026-11-16-01-masbench-b1-safety-and-delivery.md)，其base为4754bed；此次覆盖其归档前验证的回顾，以及916289b之后直到本轮的全部新增验证。旧验证不重跑、不重复累计成新样本。
- 第三方版本：MASBench `c0301a650db95958924bb080192c09fef39389a5`；Ollama v0.11.11/`92b96d54efd6b49322b7cf046f9a0dc16b00cd0a`；Go1.26.11与Zig0.17.1固定官方archive/SHA。归档不等于重新安装或重新验证这些版本的全域性质。
- 历史运行身份：以各run manifest/source_snapshot为准；不把本次归档SHA写回旧run，不在本文自填本次提交哈希。

## 1. 提交内容

1. [通俗阶段成果](../复现实验阶段成果.md)及[项目进度梳理](../research/reports/project_progress_and_plan_2026-11-16.md)：区分原作者贡献、复现证据与缺口、既有负结果、创新待验证、当前准入瓶颈。
2. [D1决定](../research/benchmarks/masbench_d1_evaluation_decision_2026-11-16.md)：用户保留文章关联分量隔离，registry和4题开发预留不改；正式划分/功效未冻结。
3. 同源计数源码与隔离入口：`experiments_ext/masbench_context_counter/main.go`、`masbench_context_build.py`、`masbench_cpp_vendor_prepare.py`、`masbench_cpp_vendor_build.py`、`masbench_context_offline_contract.py`。保留原Go停止门、新增C++独立授权与所有失败。默认system、完整渲染、词表flags及实际客户端准入支持域显式化。
4. [离线验收](../research/reports/masbench_cpp_offline_acceptance_2026-11-17.md)、[真实部署验收](../research/reports/masbench_real_deployment_acceptance_2026-11-17.md)及独立 `masbench_deployment_acceptance.py`：临时32768、合成长输入、V1 usage、主动断连/卸载栅栏和原配置恢复；未自动接线生产Driver。
5. 15个新run的manifest/status/日志/source_snapshot与归档恢复侧车；[小型证据包](../research/artifacts/context-deployment-20261117/README.md)含20份逐字节原始JSON，80,630bytes。`provenance.json`逐份绑定原artifacts大小/SHA，失败输出也保留。
6. 16份约19.94MB重复全历史receipt原件保留本地/HPC，公开SHA绑定[精简索引](../research/artifacts/context-deployment-20261117/receipt_index.json)。原outputs、patch/tar/gzip、模型、环境、临时下载及私人PDF不新增入Git；旧tracked历史不删除。本次新增-text仅覆盖新证据路径，保护原件字节。
7. `research/README.md`、project_status、next_steps、dashboard/STATUS等入口更新；科学No-Go与有限域/Pending边界保持。

## 2. 主要尝试

### 上次提交前已做的验证（历史回顾）

| 阶段 | 已有证据与结果 | 本次解释边界 |
|---|---|---|
| 10月末G1/任务适配 | 既有519工程测试与机制诊断：有限价格控制可复现本版G1选包，内容路线No-Go | 不因新部署成功撤销，不作为本轮重跑 |
| 11月2日环境/模型恢复 | 固定模型manifest/blob、独立Reasoning环境/依赖、许可证与GET元数据核验；早期下载、配额和恢复失败保留 | 环境就绪不代表任务能力 |
| 11月3日数据/适配 | 数据300行、200唯一问题、重复/支持异常；最终67适配合同 | 不是67效果样本；不改保守分组来增加N |
| 11月3日客户端与准备 | 最终147准备合同+独立httpx MockTransport5项；4题/4分量预留248行、剩52 | 无真实生成/题目曝光，前序失败保留 |
| 11月10日B1前置 | 只读服务1024/模型架构32768区别；D1剩52行=36问题家族/34文章关联分量；17执行保护合同 | D2仅弱隔离备选，不能静默替换D1 |
| 11月10日Driver集成 | 最终24合同；前序20/22/23为过程快照，不累计。持久预算/分区、真实Prompt配对、假worker seccomp、外层中断/不可重置deadline等 | 仅fixture-only工程域，原client/application/wire不改；固定“四token”不是Qwen计数 |
| 11月16日上次归档收尾 | 用户指定目录清理前约5.46GiB，停止Laya服务后完成清理/配额与源同步；901文件0差异，6份10,454bytes白名单 | quota/dashboard/receipt/同步失败均保留；无模型调用 |

上述历史依据为上次[提交说明](2026-11-16-01-masbench-b1-safety-and-delivery.md)、[B1集成报告](../research/reports/masbench_b1_driver_integration_acceptance_2026-11-10.md)、[前置报告](../research/reports/masbench_b1_preflight_acceptance.md)和旧[小型白名单](../research/artifacts/masbench-b1-20261116/README.md)。本次只核档案与冻结源，不把历史报告改写为新增运行。

### 916289b之后的新工作

[CODE/RUN] 先读远端提交、本地说明书和权威研究索引，写进度/通俗总结。Git直连读取曾失败，后连接器核验远端；不是pull/合并或新研究实验。用户明确保留D1，保持原预留/异常记录及首次真实题目曝光边界。

[RUN] 用户先批准Go1.26.11+Ollama固定模块的离线构建，1800s/2CPU/4GiB等边界。home配额与占位方式失败后仅修自有占位；改/tmp时把tmpfs同时计入内存，未回退Windows测试。goproxy.cn只作为模块传输，保留sum.golang.org签名校验；最终Go通过、C++7.5缺filesystem和module zip缺vendor导致失败。

[RUN] 固定完整vendor4文件/3子树与Zig官方归档，HTTP大响应截断后转已核官网镜像Range，最多2连接，最终官方SHA相同。用户另行批准新增Zig/Clang/libc++与glibc2.27目标；C++17/CGO先验收，再构建helper。隔离wrapper映射-lstdc++至-lc++只作用此构建，系统GCC/Python/Ollama不升级。

[RUN/CODE] 离线检查发现Qwen有68字节默认system，按固定ChatHandler规则处理。首轮把manifest的sha256:误写为文件名sha256-，启动helper前失败；第二轮发现renderer多system支持域与受控客户端不同，fixture期望错误。修期望而不改客户端/删用例：14render、36合法窗口、6schema拒绝、4special-token。

[RUN] 用户批准7份管理patch无损压缩，逐份本地/远端/解压SHA一致，释放366,419,761bytes；本地未压缩原件和HPC侧车保留。此前仅对齐HPC HEAD未处理旧索引导致虚假大量删除，原patch不重写；改独立/tmp索引，真实索引保持。一次prepare收尾因EDQUOT残留running，核进程消失后授权补记failed，精确结束/退出仍unknown。

[RUN] 用户要求真实部署后，临时把原服务默认1024设32768，2 debug、2合成生成、1卸载，在39.73s内验收并finally恢复1024。不是永久配置32768，不是四题能力screen。

## 3. 结果

### 全部新增登记运行（HPC n1；每条独立manifest）

目录前缀均为 `research/sync/runs/`；完整命令、Git/sync身份与原始state在[15-run索引](../research/artifacts/context-deployment-20261117/run_index.json)。空值不补造，SIGINT主动停止不冒充编译/科学失败。

| run ID | 秒 | 状态/退出码 | 主要结果或失败 |
|---|---:|---|---|
| hpc-masbench-context-build-20261116 | 0.423447 | failed/1 | 自有配额占位打开方式EBADF |
| hpc-masbench-context-build-v2-20261116 | 0.726638 | failed/120 | home真实EDQUOT |
| hpc-masbench-context-build-v3-20261116 | 32.448509 | failed/1 | Go官方archive通过；模块网络不可达 |
| hpc-masbench-context-build-v4-20261116 | 5.425162 | failed/1 | 签名模块/7参考匹配；临时cmd目录权限 |
| hpc-masbench-context-build-v5-20261116 | 51.130733 | failed/1 | GCC7.5缺filesystem、模块zip缺vendor |
| hpc-masbench-cpp-vendor-prepare-20261116 | 142.637626 | failed/1 | 大blob HTTP截断 |
| hpc-masbench-cpp-vendor-prepare-v2-20261116 | 未知 | failed/未知 | raw传输仍截断，收尾另遭EDQUOT；原running状态保留副本 |
| hpc-masbench-cpp-vendor-prepare-v3-20261116 | 380.164011 | failed/-2 | 官方通道过慢，主动SIGINT，保留片段 |
| hpc-masbench-cpp-vendor-prepare-v4-20261116 | 512.203913 | failed/-2 | 镜像通道过慢，主动SIGINT，保留片段 |
| hpc-masbench-cpp-vendor-prepare-v5-20261116 | 216.098090 | completed/0 | 4 blob/3 tree、官方工具链SHA/内容/许可检查通过，未执行编译器 |
| hpc-masbench-cpp17-helper-build-20261116 | 200.900348 | completed/0 | C++17 filesystem/string+CGO及helper通过 |
| hpc-masbench-context-offline-contract-20261116 | 0.190880 | failed/1 | 默认system摘要前缀检查失败，helper未启动 |
| hpc-masbench-context-offline-contract-v2-20261116 | 0.778828 | failed/1 | 词表only实际执行，客户端fixture支持域期望失败 |
| hpc-masbench-context-offline-contract-v3-20261117 | 1.005240 | completed/0 | 14render/36窗口/6schema/4锚点全部通过 |
| hpc-masbench-real-deployment-20261117 | 39.725243 | completed/0 | 临时32768、2443-token对账、断连卸载和恢复通过；原生idle未独立观测 |

合计15条：4 completed、11 failed（含2次主动中断传输）；不按“最终绿”抹掉此前失败。三次离线登记执行合计1.974948s；有人工诊断间隔，不称连续120s自然时间窗。工程fixture无任务样本N/显著性或任务CI，不套用科研效应推断。

### 正面证据与严格限制

- [RUN] 官方Go archive、签名Ollama模块和参考源码匹配；module Origin缺失，7参考匹配不冒称全git-tree证明。Zig archive57,411,036bytes、展开374,407,381bytes、0 symlink/hardlink；MIT及LLVM/第三方声明保留，9份显式license不代表整包纯MIT。完整版本/SHA见协议与原始小型输出。
- [RUN] helper SHA `e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5`；固定模板/system/manifest，词表only日志明确skipping tensors，无tensor context。独立renderer及special-token锚点不是独立tokenizer；不把同helper自比较冒充部署逐token独立证明。
- [RUN] 新C++构建采样临时文件峰值1,468,595,060bytes、进程组RSS670,670,848bytes、合计2,011,885,643bytes，低于授权上限；一个弃用警告保留。最终离线采样RSS77,983,744bytes，14/36/6/4分别报告，未改生产客户端。
- [RUN] 真实驻留API报告32768；两组完整render一致，2443 prompt tokens大于原1024，服务usage一致；正常返回OK/stop、输出2 tokens。取消预留max512不退款，实际最终tokens未知。POST5；run内GET10，加前后管理GET共12≤40。采样RAM5,216,960,512bytes、GPU8,680,112,128bytes；均是采样而非瞬时硬隔离证明。
- [RUN] 主动断连后卸载返回done/unload，ps空、旧runner37396消失；恢复PID37483/default1024/parallel1并独立核实。不能推断仅断连即原生即时idle；未保存原始SSE chunk/最终取消usage，runner命令行未暴露ctx-size，因此不编造这些证据。
- [RUN] 最后回传20261117T032230Z-620403已镜像所有登记产物；最后源同步20261117T032915Z核1027文件、0差异。本次Git归档不再做HPC运行/模型调用，不把管理读取当新实验。
- [RUN，管理失败] 多次网络超时、直接源/镜像传输失败、本地60s备用下载超时、恢复时VPN不可达以及一次管理脚本路径错误均按既有日志/报告保留。用户恢复VPN后才复核n1/UID/二进制/配额并继续，没有本地计算替代。

## 4. 当前进展

| 关卡 | 当前结论 |
|---|---|
| D1文章隔离选择 | 已明确；正式评价划分/功效Pending，预留248/300后余52行=36家族34文章分量 |
| 同源离线候选 | 已构建且合成支持域Go；不是通用独立tokenizer或部署认证 |
| 真实context/完整输入/正常usage | 临时32768的有限输入通过；当前默认已恢复1024 |
| 取消 | 取消后卸载栅栏通过；原生即时idle未独立证实 |
| 生产Driver/真实ContextBinding | 未接线/未放行；禁止复制fixture verified |
| MASBench真实任务与效果 | 0题/0episode；新增真实生成仅2次合成部署检查 |
| 科学收益/正式test/训练 | 原G1/GP-ID No-Go保持；没有成本匹配净收益、能力通过或可投稿结论 |

原GOSC复现已积累真实LLM/缓存/多seed证据，但历史一致性、作者cache生成链/校准缺口仍单列。此次部署成功不填补那些缺口，不把Genie改称任务最优上界，也不将Planner/cache回放当新LLM调用。

## 5. 下一步安排

1. 先实现真实Driver的完整计数、运行时服务身份和取消后卸载栅栏接线合同；审查是否接受这种停止策略。修SSE原始chunk/最终usage不可得时的持久fence与未知字段，不补造既有记录。
2. 明确是否持久采用32768，并重新核实服务参数、空闲/模型资源和回滚；本次临时32768不能直接作为当前长任务准入条件。tmpfs helper在重启后可能消失，复用前重核SHA，不擅自重新下载/重建。
3. 明确四题能力screen和真实调用预算后才运行；D1严格文章隔离保持。正式独立划分/统计功效不足时收窄主张或停，不静默切D2、不用测试数据调参。
4. 科学机制只在强简单baseline和实际预算匹配后讨论；不扩N/训练挽救既有No-Go。Git归档本身不授权后续科研或服务修改。
5. 后续HPC工作先核新的Git/source manifest身份；本次不自动更新HPC HEAD、回写历史run或为归档启动计算。

## 本次提交验证

- [RUN，本次仅管理] `git status/log/rev-parse/remote/ls-remote/diff`、文件/JSON/SHA/敏感路径/大文件、冻结源与stage字节审查、Markdown入口和固定五部分格式；实际结果保存 `research/logs/git-publish-2026-11-17/`。没有新pytest、推理、仿真或统计。
- 暂存新代码/文档/15run元数据/20小型原始JSON/compact receipt索引；原outputs、二进制、patch/tar/gzip、完整receipt、环境、私有论文不新入Git。源码与证据检查分开，原始日志空白提示保留，不改证据来变绿。
- 普通一次commit/push当前授权分支，不force；身份以包含本说明的Git历史与远端引用交叉核验，不在本文回填自身哈希。最后工作区状态由管理核验确认。

- 已完成的归档审查：73冻结源码未改、20原始小型输出与16原receipt SHA一致、受保护上游/原客户端未改、敏感/模型/环境/私人PDF/大文件blockers为0；新证据stage blob与本地原件字节一致。初始审查237份非自哈希文件约6.95MB，最终统计以Git树为准。
- 默认沙箱暂存曾因.git/index.lock写权限失败，提升Git写权限后成功，失败单列而不称首次暂存成功。默认空白检查对保留的CRLF原件有提示；使用cr-at-eol明确策略后exit0、无真正空白例外，不改变原始证据。详见[管理记录](../research/logs/git-publish-2026-11-17/task_log.md)、审查JSON及whitespace_check.json。
