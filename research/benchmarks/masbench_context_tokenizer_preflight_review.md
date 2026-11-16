# MASBench Reasoning：Tokenizer / Context 前置核验

2026-11-10。结论：**A审查完成；精确计数器与逐请求有效context绑定Pending，真实生成Blocked。** 未安装依赖、下载模型、改变/重启服务或调用chat/generate。原提案32768不得填入verified的ContextBinding。

## 证据与身份

[RUN] `hpc-masbench-b1-preflight-20261110/outputs/preflight.json`（位于 `research/sync/runs/`）由独立Reasoning Python 3.11.15执行，耗时0.855051s，exit0、HTTP请求0。源码归档HEAD为4754bede84bb6e6defd8e646a63e81ccd6a20b4b+本轮dirty快照；科研基线014b85d+冻结扩展、第三方MASBench c0301a650db95958924bb080192c09fef39389a5、旧run版本不变。HPC n1/UID8301880，quota 2CPU/24GiB；GPU环境限额不是新推理实测。

| 对象 | 本轮事实 [RUN] | 不能推出的结论 |
|---|---|---|
| 固定候选qwen2.5:7b | manifest SHA `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`匹配 | 不是原论文作者模型身份、能力证明 |
| GGUF模型层 | 4,683,073,952 bytes；digest `2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730`；本轮只核大小及metadata | 本轮没有重新全量哈希权重；完整blob SHA使用11月2日历史证据 |
| GGUF metadata | v3、qwen2、context_length=32768；头至metadata结束5,934,631 bytes，prefix SHA `b4b14a8391ba681981664b3747933eb2e8615f86857ed78ff2e672254f69eb65` | 架构窗口不是请求生效窗口 |
| tokenizer | gpt2 / pre=qwen2；152064词项、151387 merges；数组原始编码SHA在JSON | 具备原料不等于已经有与部署等价的计数实现 |
| GGUF内置chat template | 2509 UTF-8 bytes，SHA `d5495a1e5db0611132a97e46a65dbb64a642a499421228b9c8b93229097fa9a4` | 不能直接当作Ollama执行模板 |
| Ollama独立template层 | 1482 bytes，SHA `eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175`；小层实际SHA匹配 | 不同模板语言/封装不能仅按名称宣称等价 |
| 当前serve进程 | PID8964，exe位于runtime/0.11.11；白名单环境 `OLLAMA_CONTEXT_LENGTH=1024`，单并发/单加载、正确模型目录、回环端点 | 未发实际请求，未核验runner实际参数、加载/截断情况 |
| 现有独立环境 | openai1.101.0/httpx0.28.1；transformers/tokenizers/sentencepiece/tiktoken/llama-cpp-python/gguf均未登记安装 | 不能凭缺一个包断言完全不可实现；当前确无已验证部署计数器 |

[CODE] `experiments_ext/masbench_b1_preflight.py::gguf_metadata`依GGUF头/typed metadata读取，跳过tensor区，只输出计数/哈希与选定元数据，不载入模型。格式依据[GGUF官方规格](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md#specification)；此链接为访问时主分支格式参考，并非模型来源版本证明。`tokenizer.ggml.add_bos_token=false`、BOS/pad151643、EOS151645均已读到，仍需部署实现的special-token策略。

## 1024与32768的关系及静默截断风险

[CODE] 本地 `scripts/hpc_ollama.py::settings`固定1024，且本轮从正在运行的进程环境再次确认1024。manifest中没有params覆盖层。Ollama v0.11.11的默认NumCtx读取环境；模型options、请求options可依次覆盖。因此目前有**服务默认1024的强证据**，没有“已部署32768”的证据。[api/types.go DefaultOptions](https://github.com/ollama/ollama/blob/v0.11.11/api/types.go#L683-L706)、[envconfig ContextLength](https://github.com/ollama/ollama/blob/v0.11.11/envconfig/config.go#L172-L175)、[modelOptions](https://github.com/ollama/ollama/blob/v0.11.11/server/routes.go#L91-L102)。

[CODE] v0.11.11 `chatPrompt`模板化并tokenize后裁减历史，保留system/最后消息；`ChatHandler`在debug返回之前已scheduleRunner并执行此流程。不能把HTTP成功或debug-render结果当“原请求未截断”；本轮连debug chat也没有调用。[prompt.go](https://github.com/ollama/ollama/blob/v0.11.11/server/prompt.go#L17-L108)、[ChatHandler](https://github.com/ollama/ollama/blob/v0.11.11/server/routes.go#L1486-L1550)。

[CODE] `/v1/chat/completions` 的max_tokens映射num_predict，并不因此设置num_ctx；现有ClientConfig.context_tokens只是客户端核验参数。更改其值不会自动扩大服务窗口。[OpenAI兼容转换](https://github.com/ollama/ollama/blob/v0.11.11/openai/openai.go#L380-L545)。故不能将1024→32768当作无需服务配置的本地修复。

## 每个请求的合法计数对象

[CODE] `application.py::LocalAgent.request`实际数组含原生Benchmark模板形成的system（角色、问题、该agent私有context）、自身完整输出历史及仅已送达并可见的peer消息。protocol的累积知识板附在每次收到的历史项，重复出现也必须重复计数；不能把板当免费全局共享。自身full与peer visible边界不同，角色由原生前缀规则决定。不得加入另一方私有context、gold或审计transcript。

[HYPOTHESIS / 准入合同] 对冻结后的完整请求R，先精确重现 `/v1`转换、模型默认system/预设messages处理、filter及**实际Ollama Go模板**，得到完整prompt P，再用同GGUF tokenizer及同special-token策略得到token IDs T(P)。不对JSON序列化本身计数，不只拼content，不用UTF-8 bytes、word或比例估算。

`exact_prompt_tokens = len(T(P))`

`exact_prompt_tokens + max_output_tokens <= effective_num_ctx`

每turn调用前重新验算，保存R/P/token-IDs摘要、计数器版本、模板与metadata SHA、manifest、服务配置/runner实参证据。当前512输出提案在默认1024下仅留下512输入预算；**未得精确计数，不能声称16个初始请求均超限或均可装入**。历史最大system16423bytes不是tokens。后续多轮历史仍需逐请求验算。

[CODE / 限制] `client.py::ControlledClient`已有未verified绑定拒绝、超context拒绝、usage prompt_tokens与预计数不符拒绝、finish_reason=length拒绝及响应hash；这只能在计数器真实正确时工作。`verified`布尔值本身不是证据。事后usage对账有助检出异常，不能替代派发前无截断证明；缺usage保留null，不能默认0或替代验证。

## 尚缺项与可执行解决方案（本轮未实施）

| 缺口 | 最小解决建议 [HYPOTHESIS] | 额外权限/负担 |
|---|---|---|
| 部署等价的模板renderer与tokenizer | 优先审查现有固定Ollama runtime是否有可离线导出的渲染/tokenize接口；否则固定对应源码、构建最小离线helper或安装隔离绑定，读取现有GGUF | 需另批第三方代码执行/构建或依赖安装；先提交版本/hash/依赖清单。不能承诺HF apply_chat_template天然等价 |
| 等价验收 | 无真实题目的Unicode/空白/角色/多system/历史/special-token边界fixture，逐render字节和token IDs与部署实现对照 | 当前只读范围不能提供全部runner对照；如需加载模型或合成chat预检，另批且计入预检预算 |
| 生效context | 用户批准固定配置方案后核验加载runner实参、服务进程/模型/模板身份；若要32768必须明确修改及内存预算、重启影响 | 本轮禁止改配置/重启；实际KV显存/耗时未知，不能由架构metadata推算为已足够 |
| 全请求无截断 | 在以上证据成立后，对每次完整请求验算与usage对账，溢出即失败，不删历史或自动扩窗 | 绑定失败或服务身份漂移立即停止；不得手工置verified |

[HYPOTHESIS] 离线metadata/tokenizer准备通常不需GPU，但实现/构建资源上限须在方案确定后估算，当前不虚报安装体积/运行时间。新GPU负载、精确tokens与上下文承载能力均未测。A结论为Pending/Blocked，值得申请的是**精确计数和服务配置方案**，当前尚不具备真实四题诊断的完整准入条件。
