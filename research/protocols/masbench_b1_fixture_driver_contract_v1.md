# MASBench B1 无模型Driver整合合同 v1

2026-11-10。状态：本轮新独立fixture实现；实际HPC结果见[验收](../reports/masbench_b1_driver_integration_acceptance_2026-11-10.md)。旧[执行安全规格](masbench_b1_execution_safety_spec_v1.md)与历史17合同原件不改。真实B1依旧Blocked，G1/GP-ID No-Go保持。

## 授权与信息边界

[CODE] `extensions/masbench_reasoning/fixture_driver.py::FixtureCampaign`只接受固定字段的合成计划，内部model固定为`fixture-only-not-qwen`，manifest全零；没有live backend参数、真实任务加载器或真实执行CLI。其固定四token计数及verified fixture绑定仅用于验证旧接口，不生成任何真实Qwen verified证据。真实episode、chat/generate、模型/依赖下载、服务更改、训练与提交均不在本轮实现范围。

[CODE] 原 `ControlledClient`、`run_controlled`、LocalAgent和ContractTransport保持不变。新adapter调用这些原接口，以实际初始requests SHA及PrivateView SHA绑定同家族/Prompt的Full与No-A2A；拒绝复用已有memory/facts/received的Agent。No-A2A仅拒绝A2A传输，保留本地生成、自己的历史与提交答案。审计transcript、peer私有证据不进入下一请求。fork worker会继承父进程地址空间，**并非隐私安全沙箱**；本轮仅执行受审的内置替身函数，未来不可信worker需另行设计spawn/输入隔离。

## 主账本与全写路径

[CODE] `CampaignLedger`在原Ledger上新增独立schema身份，完整有序plan、Limits、分区上限及控制预留共同绑定；不接管旧v1 journal。task最多96、synthetic最多2、生成总数98、metadata最多106，不能借用另一区额度。逐GET先收费，逐generation在worker派发前预留输入/最大输出；验证失败、超时、usage缺失不退额度。完成状态在原客户端的完整响应验证之后才写，length截断或usage不符不能写为completed。

[CODE] 原client的audit_sink注入新 `emit`，每个阶段落入exclusive JSONL产物；Transport子类仅旁观flush原事件/CPU/offer，不修改内容、帧、slot或成功规则。原生结果通过独立serialization输出bytes hex，不能将它回注model输入。所有这些文件及journal共享额度；控制日志另从**同一总额度预留4096bytes**，因此主Ledger上限为总cap−4096。控制区不是额外免费空间。

[CODE] resume核artifact SHA、目录未知文件/符号链接、identity/plan/limits；已有started即fence，即使崩溃发生在两个请求之间也不能从头重跑。inflight预算保持，所有started保留在分母；空间不足写不了terminal时仍可从既有started审计，整轮Blocked。completed表示episode执行完，不等于答对；本模块不加载gold、不计算任务质量。

[CODE / 边界] 这是受审可信单写者+被限制假worker的文件上限，不是给整个账户或未来真实服务建立OS目录quota。不得将新日志迁移到原JsonlAuditSink直接写盘绕开Ledger。管理source snapshot、hpc_runs stdout/stderr属于独立管理通道，不伪称包含在256MiB科学产物内；最终总磁盘仍须投影。

## 自有worker与外层停止

[CODE] 每次metadata/generation由fork创建一个内置替身worker，关掉继承的所有文件描述符，只保留IPC pipe；Linux x86_64 default-deny seccomp白名单仅允许必要内存/信号/时间/退出和向该pipe写数据，不允许open/socket/fork/exec/stdout写入。安装失败就返回失败，不回退无保护模式。每worker设置256MiB地址空间/有限CPU，IPC body≤1MiB，parent有真实monotonic deadline并KILL/reap owned child。资源记录只表示假worker CPU/RSS/wall，模型推理与GPU值保持null。

[CODE] `ControlledClient`与adapter共用从generate开始的绝对operation deadline；metadata、审计fsync及generation消耗同一60s提案时间，不能在create时重新给满60s。所有调用还受主账本原始整轮截止约束；普通HTTP与真实LLM不能使用这个禁止socket/open的fixture sandbox。

[CODE] `guard_fixture_process`是独立外层监督器，创建session包住控制器及继承进程；即使控制器崩溃或退出，也KILL自有group。其guard-init在派发前fsync绑定boot、原始monotonic起点、wall上限与argv SHA；resume不能换更大预算或命令，控制区不会清零。剩余全局时间取原guard与原Ledger截止的较早者。预留100ms清理窗口，KILL后有最多2s reap边界；不能宣称内核不可中断任务也必在deadline瞬间消失。

[HYPOTHESIS / 尚未解决] 外层监督器本身被强杀、真实服务端取消/idle、真正模型客户端的受限网络沙箱、真实计数器、全进程树资源上限与完整部署投影仍非通过项。没有给Ollama PID发信号；`server_cancel_verified=false`。RPC/控制器停止不撤销真实B1的Blocked。

## 验收与停止条件

[HYPOTHESIS / 验收合同] 覆盖两Prompt的Full/No-A2A实际原接口路径、下一请求可见性、wire账本、配对Prompt/私有观察漂移、分区/全局预算恢复、错误/截断/usage、存储耗尽、目录篡改/符号链接、seccomp权限拒绝、请求超时、控制器崩溃、外层截止穿透实际Campaign且保留inflight、guard恢复拒绝增加预算。全部合成fixture，不是16真实episodes或新独立样本。

本轮结果只允许判定受测支持域工程Go。真实部署计数/ContextBinding、服务配置/取消、资源投影、数据主张与新真实调用授权完成前，不进入任务效果实验；正式test/训练保持No-Go。
