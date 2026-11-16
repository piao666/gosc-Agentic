# MASBench B1 执行安全规格 v1

日期：2026-11-10；研究设计与独立保护原型，**不是获批的真实实验 Driver**。本轮仅允许无模型合同。科学基线014b85d+冻结扩展、当前归档4754bed、第三方MASBench c0301a6、历史run身份分别保留。旧预算提案与开发注册表不修改。

## 1. 可信边界和接口

[CODE] `extensions/masbench_reasoning/client.py` 的 `LivePermit` 仅携带协议/registry SHA，不能授予研究权限；`ContextBinding` 由真实部署证据建立，不能从 fixture 的 verified 值复制。`ControlledClient` 审查请求、精确token预算、usage和晚到响应，但没有外部强制终止权。`JsonlAuditSink` 是单文件上限；`run_controlled` 是单episode顺序器，不是跨episode durable预算驱动器。

[CODE] 新独立 `extensions/masbench_reasoning/execution_safety.py` 提供 Ledger 与 supervise_owned_worker；不改上述接口、任务评分、ContractTransport、原GOSC/Native/GP-ID/BF。它未接入真实客户端。调用者仍须可信，不能把Python API隔离称为进程安全沙箱。

## 2. Durable 预算与恢复

[CODE] Ledger绑定身份对象、完整有序episode计划、Limits和boot ID；身份对象未来必须含源码/同步/模型manifest/模板/tokenizer/context/registry/protocol/config哈希。Linux flock独占、逐事件hash链、fsync后才能派发；请求ID不可重用，episode不可重启。请求预留输入与最大输出tokens，不因成功、失败或缺usage退款；metadata GET独立计数。最大98生成/106metadata，两者合计204；SDK retry=0，进程内外最多一个inflight。现有原型不区分96任务+2合成子配额，真实driver还须实现该分区。

[CODE] JSONL、wire bytes、其他受控产物及ledger本身共用byte预算；先预留长度再exclusive写文件，写失败不退。拒绝路径越界与覆盖。该保证仅覆盖 `put_artifact`，不覆盖现有JsonlAuditSink直接写盘、任意worker、临时文件、wrapper stdout或source snapshot；真实整轮256MiB目录cap仍需只读worker+单写者/OS quota等经过验收的边界。hash链只能检错，不能抵御同账户人工删除/回滚整个目录；恢复须校验HPC manifest、最新不可变检查点并禁止换run ID重做不利题。

[CODE] 全局monotonic截止从初次journal开始，resume停机时间计入；跨boot拒绝，不允许换clock重新预算。恢复遇到inflight永久fence，不重发、不清零；已启动episode标为interrupted_pending，后续可落为interrupted而不能重跑。未启动另列；分母保留所有started（失败计0），不能只报completed。若空间耗尽或journal损坏无法写terminal，既有started记录仍是分母，整轮Blocked，不能当作无任务运行。

## 3. 超时和强制停止

[CODE] 自有worker通过新session启动；父监督器用真实monotonic时间、selectors有界读取，截止为min(60s操作剩余,6000s整轮剩余)，TERM后KILL整个自有进程组并reap直接子进程。正常直接子进程退出后仍处理继承pipe的后代。日志内存≤1MiB；共享产物预算不足即停止。合同只使用自造sleep/TERM-ignore/输出worker。

[HYPOTHESIS / Pending] HTTP断开不等于Ollama取消。外部Ollama不在worker进程组，**禁止向服务PID发信号**；超时/中断/状态不明后整轮fence，不能派发下一个生成。真正server-idle/cancel确认、无孤儿生成、外部全局监督器在driver崩溃时仍生效尚未验收。因此即使假worker watchdog通过，真实B1仍Blocked。原型supervisor和Ledger需由未来driver组合；当前没有自动将worker超时写成request terminal的完整接线。

[CODE / 限制] 截止触发TERM，随后有50ms grace、KILL及最多2s reap；不是承诺从deadline后CPU/服务活动立刻为零。若6000s要求包含清理，未来须预留清理窗口、设置更早内部截止并由外层独立supervisor兜底。本轮测试验证“截止触发自有组停止”，不将其写成真实6000s硬上限已验收。worker结果reason=completed仅表示进程退出路径，必须同时检查returncode=0，不能据此把非零退出当任务成功。

| 剩余阻断 | 最小修复候选 [HYPOTHESIS] | 验收/权限 |
|---|---|---|
| 未整合现有客户端/无线日志 | 单可信父进程持有Ledger，子worker仅返回有界结果；每次metadata/generation分别预留，同一操作deadline；分区限额96+2 | 新fake集成合同；不得仅把新模块导入就称已接线 |
| 任意写盘/崩溃后超限 | worker无写权限或受限制工作目录；统一父写者对所有JSONL/wire/临时日志计费；外层独立监督并保留终止审计空间；如需OS quota/cgroup则先审查可用权限 | 无模型写盘/崩溃/断开fixture；目录配额和管理snapshot成本分别明确 |
| 外部Ollama取消 | 审查固定版本断连取消链，再在获批合成请求下核查服务任务结束、无继续生成、后续派发前idle；不能只看client退出或`/api/ps`模型仍驻留 | 需另外明确授权真实合成生成及资源/服务观测，不在本轮运行；有疑点整轮fence |
| 完整资源投影 | 先无模型事件/日志最坏体积投影，批准后的合成请求采模型wall/usage/可归属显存；长context KV内存实测后再核预算 | 未测为null，不能从L40名义容量或短fixture承诺足够；安装/服务变更单独批准 |

## 4. 成本与公平配对合同

[HYPOTHESIS / 准入要求] 固定四题原身份×base主/protocol辅×Full/No-A2A=16计划episode，最多6总发言。题目/Prompt/模型/temperature/上下文/服务/预算同配对，不按结果重排/换模型/补跑。No-A2A仍用自身证据提交答案；Full收益必须追踪payload SHA→送达→receive可见→对方下一请求SHA。记录全部原生EM/F1/None/parse失败与适配失败，主分母含started失败，planned未启动单列；配对不完整则不得通过能力screen。

[HYPOTHESIS / 准入要求] 逐请求记录派发前、HTTP开始、首token/结束/超时、预算预留、返回usage或null、模型实际墙钟；CPU用worker/process或cgroup采样，GPU用可归属服务PID/cgroup的显存采样并注明采样峰值非连续真实峰值。GPU/推理延迟未测不能填0。UTF-8 payload/header/CRC/ACK/重传、UL/DL uses来自wire账本，模拟CPU slot与实际CPU ns、模型wall分别报告。恢复/失败也计资源，不以wire bits换算模型tokens。

## 5. 本轮验收和停止

新合同结果及命令最终写入 `research/reports/masbench_b1_preflight_acceptance.md`；旧147+5仅为历史证据，不计本轮测试数。真正driver集成、精确tokenizer/context、完整目录硬cap、服务端取消/空闲证据、资源投影、用户真实模型授权全部通过前维持Blocked。G1/GP-ID No-Go、正式test/训练禁止；完成B1-pre后停止。
