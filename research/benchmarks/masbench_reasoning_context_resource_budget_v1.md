# MASBench最小能力诊断：上下文与资源预算提案

日期2026-11-03。状态：**已给出资源上界，运行仍Blocked/Pending，未获模型调用授权**。本轮只做已有数据/模板的无模型盘点；不是时间吞吐校准或真实任务能力试验。

机器可读配置：[proposal_v1.json](../protocols/masbench_reasoning_minimal_capability_proposal_v1.json)。开发清单绑定HPC `hpc-masbench-registry-v2-20261103`，registry内容SHA `94b20ff4e199f8e6dc9eeeae8b0a8f91767c00576906f5589387a1266f4a4f1a`；不是旧9/17/274三分提案。

## 上下文：已核与未核

[RUN] `hpc-masbench-context-budget-20261103`按原模板、四个选定记录、两个提示族、两个agent生成16个初始请求的字节数和内容哈希，不调用模型或推断token数。逐项见该run的`outputs/context_budget_preflight.json`。后续历史与累计板尚未生成，不能由初始请求大小证明六turn都可装入。

[RUN] 独立Reasoning环境有openai/httpx，未发现transformers/tokenizers/sentencepiece/tiktoken/llama_cpp/gguf模块。未安装新包、下载tokenizer或权重。精确模型tokens仍为null，不以words或UTF-8字节换算冒充实测。

[CODE] 现有`hpc_ollama.py:38`启动配置为1024 context；本轮没有改服务，也没有重新核验当前进程的有效context。旧模型metadata声明Qwen32768不是部署num_ctx已为32768的证据。单一候选暂定现有qwen2.5:7b Q4_K_M，manifest与旧归档一致；其归档许可层标题为Apache License2.0，可追溯文件不等于所有用途的法律批准或模型能力验收。本次不在三模型间试题挑胜者。

每个未来请求必须核验：

`exact_tokens(deployed_chat_template(system + own_full_history + delivered_peer_visible_and_local_board_history)) + 512 <= effective_num_ctx`

需要同时绑定实际部署模板/tokenizer、模型manifest和服务context配置的证据SHA。自身full输出、peer MESSAGE/fallback、每次板后缀均纳入，不只计算当前问题或消息body。每turn重新计数；溢出直接失败且计入已启动分母，不自动删历史/截断。客户端默认拒绝未核验ContextBinding，不能为通过合同把真实绑定手工标成fixture的verified。

因此当前**不能宣称已完成可执行的上下文容量验证**。资源预算的算术部分已完成；精确tokenizer与服务配置核验是模型调用前的明确关卡。若需要新增轻量依赖或修改服务配置，应先具体列包/配置、成本及影响并取得相应授权；不升级驱动、不新下模型。

## 资源提案：硬上界，不是实测投影

| 项目 | 候选上限/边界 |
|---|---|
| 任务/提示族 | 4问题家族；base为主、protocol辅助；Full可靠传输/No-A2A，共16episodes |
| 发言机会 | 每episode6总turn，非6对Alice/Bob |
| 模型调用 | 任务最多96；另2次合成API预检；总98，失败请求也占次数；SDK重试0 |
| HTTP | 每次生成前最多1次身份GET；另≤8次启动metadata检查；总GET≤106，连同生成POST≤204 |
| 输出 | 每次512tokens，总≤50,176；不是实际生成量或足够完成推理的证明 |
| 输入 | 候选C=32768时总理论上界98×(32768−512)=3,161,088tokens；每请求还需精确核验 |
| 并行/硬件 | 一次1调用/1加载模型，CPU≤2；沿用已有HPC资源，不申请新硬件 |
| 单操作超时 | 60s共同覆盖token准备、metadata与生成，不是各自60s后相加；模型冷加载也计入 |
| 总墙钟 | 6000s硬上限；98×60=5880s是按接收期限计算的名义操作预算，余量并非吞吐测量；提前触顶则未完成配对blocked |
| 真实运行时间/显存/KV | 未测；runtime_projection=null，不以旧短JSON速度估长context性能 |
| 产物 | 256MiB硬上限；每请求JSON与响应JSON各≤1MiB，98对≤196MiB，加metadata/结果/错误/日志余量；runner源码快照另列管理通道 |
| 结束 | 不无限drain、不补做失败题、不自动重采样、换模型、改prompt或延长输出救结果 |

未用完预算不能自动转成额外题目/重复种子。恢复运行须按相同registry及不可变事件记录，不以resume静默重开98次额度。真实运行driver还需共同执行请求、墙钟、存储总cap；本轮没有提交可自动运行的campaign入口。

## 统计与科研门槛提案

所有已启动任务进入主F1分母；解析失败、截断、超时、模型/API/上下文失败计0，并保留互斥end_reason及具体flags。未启动单列，完整配对未完成不得通过。原非None F1/words口径并列，不能替代主分母。

在调用前固定base为主诊断族：建议至少2个不同问题在Full下规范化EM正确，并至少1个同题Full−No-A2A F1>0且peer payload确实进入下一次请求，才作为“值得继续设计”的线索。protocol只作独立辅助结果，不在base失败后改为预定主方法。该门槛是本轮提案，不是已经检验/批准的科学成功标准。

四个开发问题覆盖四个保守分量，但曝光预留248条，只余52条未预留。剩余池是否满足未来独立校准/评价、统计功效与硕士论文主张仍Pending；不能称52行都是独立问题，也不把这四题的小诊断当正式可发表证据。对预留影响及后续可行性应在真实调用前作研究决策。

Full能力不足或与No-A2A无可辨质量区分时，停止当前支持域或判断尚未建立信息依赖空间，不自动增N/训练。正差异仍可能受模型随机性影响，仅为存在性线索，不证明通信因果效应、内容排序创新、净收益或可发表性。G1和GP-ID科学No-Go保持。


实际超时边界：客户端校验共同期限并拒绝晚响应，HTTP读/连接有timeout；它们不等于已核验每次OS级强制中断或取消服务端生成。未来获批driver需要请求级watchdog及总6000s硬中断、总产物cap，触顶保留已用成本并将未完成配对blocked。256MiB还须对实际wire事件/审计输出投影并共同限额，不仅约束客户端单个JSONL；缺少这些执行层核验时，本提案仍不可执行。
