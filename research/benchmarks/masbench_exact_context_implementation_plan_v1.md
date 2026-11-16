# MASBench精确计数与Context实施方案 v1

2026-11-10。用户本轮批准补齐**方案与无模型Driver保护**。本文件是具体可审阅方案，未安装工具链、构建/执行第三方helper、加载模型、改服务或生成。机器可读提案：[JSON](../protocols/masbench_exact_context_implementation_plan_v1.json)。旧[前置审查](masbench_context_tokenizer_preflight_review.md)保持当时事实；真实ContextBinding仍不得置verified。

## 1. 已核实路径与本轮新证据

[CODE] 官方release v0.11.11指向commit **92b96d54efd6b49322b7cf046f9a0dc16b00cd0a**，不跟随main。记录模型manifest845dbda0…b697e、GGUF模型层2bada8a7…3730与实际Ollama模板eb440283…5175，全SHA在JSON。来源：[官方release](https://github.com/ollama/ollama/releases/tag/v0.11.11)、[对应commit](https://github.com/ollama/ollama/commit/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a)。不能因此认定当前二进制已与自构建helper逐行为等价。

[CODE] 固定源码 `llm/server.go::NewLlamaServer/Tokenize`：旧engine加载 `VocabOnly:true` 的词表对象，计数调用 `Tokenize(content,false,true)`；新engine可走TextProcessor.Encode。由此可设计无tensor推理的部署同源计数器，不能默认安装任意tokenizers包就等价。[同源实现](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/llm/server.go#L135-L165)、[Tokenize路径](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/llm/server.go#L1503-L1522)。

[RUN] 本轮SSH只读确认n1、UID8301880、HEAD4754bed、无running任务、2CPU/24GiB、kernel5.4.0-100-generic；PATH有gcc/cmake，**没有go**。实际PID8964的OLLAMA_NEW_ENGINE/OLLAMA_EXPERIMENT未设置，CONTEXT_LENGTH仍1024（白名单读取）。这支持旧engine作为候选，不证明模型加载后必走该分支；model-required engine与实际runner仍须核验。证据在 `research/logs/masbench-b1-integration-2026-11-10/{preflight_stdout,engine_environment}.json`。

[CODE] 同版本go.mod声明Go1.24.0；template包使用Go模板与自定义处理，不能把GGUF中的Jinja模板直接替代实际1482byte模板。[go.mod](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/go.mod#L1-L3)、[template包](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/template/template.go)。API查询tag一度不可访问，随后从官方release的commit链接核实全SHA；没有猜测版本。

[RUN / Pending] 官方Go下载JSON本轮访问失败；工具链archive版本/官方SHA仍为null。Go1.24.0是该源码的最低声明，**不是建议安装未经维护核验的旧基础版**。实际安装批准前须固定受维护且兼容的官方补丁版本、archive SHA与依赖清单；当前方案不能直接当作可执行下载清单。

## 2. 首选方案：同源离线CPU helper

[HYPOTHESIS / 拟实施] 在HPC独立目录准备固定源码与Go1.24工具链，依赖锁/下载hash单列，不修改项目两套Python环境、不覆盖Ollama运行库。最小helper仅接受纯文本messages和绑定manifest；读取现有GGUF词表及Ollama模板，不创建LLM context、KV cache、生成器或HTTP服务，不载tensor、不下载模型权重。

处理顺序应为：

1. 校验manifest/blob metadata/模板SHA，读取实际model options及预设messages/system（本模型manifest目前无messages/params层，仍需按源码核验）。拒绝tools/images/非当前白名单角色，不偷偷支持未验收输入。
2. 复现当前 `/v1` 纯文本消息转换及ChatHandler的必要前处理；采用同源template.Parse/Execute，对**未裁剪的全messages**生成P。避免调用会裁剪历史的chatPrompt作为唯一原始输入来源。
3. 核实实际engine：legacy时使用同commit的llama封装、VocabOnly:true、addSpecial=false、parseSpecial=true；若实际为新engine，则选择同源TextProcessor，不能自动偷换实现或混合两个token计数。
4. 输出request SHA、完整rendered prompt SHA/UTF-8 bytes、token IDs SHA、精确token数、source/build/toolchain/模型/模板/metadata/flags身份。只保存摘要不足以重新核验时，应在受控本地产物中保存可复算输入；不向公网发送私有上下文。
5. 先返回 `offline_exact_candidate`；只有部署renderer/tokenizer与服务参数的独立对照通过，才能形成真实ContextBinding。helper编译成功不是verified。

[CODE] Ollama chatPrompt会裁剪历史；因此完整P的生成与“服务实际输入未裁剪”必须分别核验。[prompt.go](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/server/prompt.go#L17-L108)。`llama.go`封装支持词表专用加载与tokenize，不代表当前二进制暴露可直接调用的CLI接口。[封装](https://github.com/ollama/ollama/blob/92b96d54efd6b49322b7cf046f9a0dc16b00cd0a/llama/llama.go#L195-L215)。

## 3. 精确等价的验收证据

[HYPOTHESIS / 冻结后合同] 先在合成字符串上覆盖ASCII/中文/emoji、组合Unicode、连续空白/CRLF/空内容、system/user/assistant顺序、最后为assistant、特殊token字面串、重复本地板、多轮完整历史。逐项比对完整render字节与token IDs，不能只比总数或decode回原文。计数必须包含system中的私有证据、自己的完整输出、已交付peer可见消息及每次历史板重复。

对边界测试使用人工fixture窗口使 `n+max_output` 分别等于、低于、高于effective_ctx；前两者可准入，后者在派发前拒绝，绝不删历史。再以固定同源server pipeline离线harness核验全prompt与服务输入路径；必要的真实部署对照留待额外授权。两个复用同一helper的自比较不能冒称部署独立验收。

真实逐请求合同仍为：

`exact_prompt_tokens(full_render(messages)) + max_output_tokens <= effective_num_ctx`

记录完整计数实现证据SHA，并在每次请求前核身份。事后usage不一致或finish_reason=length即失败并保留分母；usage缺失为null，不能用它补造verified。fixture Driver中的固定“四tokens”及全零manifest仅是替身合同，**不得复制进真实Qwen绑定**。

## 4. Context变更的独立关卡

[HYPOTHESIS / 提案] 保留当前1024服务，本轮不动。若离线计数显示原任务请求不能在1024下满足512输出预留，再申请将固定服务配置设为32768（模型架构声明上限），明确PID/无活动任务检查、服务配置/启动日志、模型加载与KV显存预算、回滚1024的方法。现有客户端仅允许11434，不隐式换端点或新建旁路服务。

32768是候选配置，不是已测承载力。先获批的合成API预检须使用不含真实题目的短prompt，核实际runner context、helper计数与usage、模型加载/推理/显存；若它们不一致即停止。必要的真实取消/idle核验也必须明确计入批准请求总额，不能新增免费预检或以 `/api/ps`模型驻留代替“仍在生成”的判断。

此后真实任务每turn重新计数；即使所有初始请求装入，也不能保证后续板与历史装入。溢出计失败，不能自动扩窗或摘要压缩。首次真实任务调用仍须另行批准；本轮不改变98请求/6000s/256MiB提案、registry或screen规则。

## 5. 成本、权限及反证

以下是**拟申请的硬停止上限，不是测得的运行投影或完成保证**：

| 阶段 | 拟申请资源上限 | 允许的成果与停止 |
|---|---|---|
| 隔离工具链/同源helper构建 | 1800s、2CPU、构建并行1、进程树内存4GiB、新下载≤1GiB、新增峰值磁盘≤4GiB、模型权重下载0、GPU0 | 事先核配额、官方来源/hash/许可证、最小依赖清单；超限保留失败，不自动加预算或安装其他版本 |
| 离线合成计数合同 | 120s、内存2GiB、产物16MiB、无生成/HTTP | exact render/token IDs匹配；不匹配No-Go，不用字节估算救结果 |
| 服务context/运行时对照 | Pending单独方案与批准 | 当前无法给实测GPU峰值/吞吐；复用既有2次合成调用预算是否足够需明确任务分配，不超额调用 |

[HYPOTHESIS] 首选同源方案比手写Python BPE更易保留部署预处理；HF/tiktoken/独立llama-cpp绑定仍只能作为候选交叉核验，版本/模板/regex/special token任一不同都不能冒充精确部署实现。若工具链成本过大、分支无法确定、模板或token IDs不一致，应保持Blocked并重新评估诊断成本，而不是增加模型复杂度。

**本轮交付Go；helper构建、依赖安装、服务修改和真实生成均未执行。** 需要批准的是以上具体隔离构建/离线合同方案；服务变更与真实调用仍独立审阅。精确部署绑定Pending，G1/GP-ID No-Go及正式test/训练禁止保持。
