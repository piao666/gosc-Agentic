# MASBench受控客户端与开发注册表实施说明

日期2026-11-03。范围为用户批准的P0–P2准备及无模型HPC验收；不放行真实模型、任务实验、训练或正式测试。

## 数据注册表

[CODE] 独立`registry.py`保留旧程序作为legacy逻辑，修正版本为`masbench-registry-v2`。空title/空支持句不形成边；支持句绑定文章；同问题和所有共享context文章连边保留。输出每条共享键的类型、哈希与行成员，以及旧新同组关系差异。缺失原始Hotpot来源仍unknown，不用ID后缀假充源ID。

开发选择硬条件为四个不同规范化问题家族、记录级2easy/2hard，每个家族一个代表；不同保守分量为事前软偏好，最大化其覆盖后按固定SHA排序取首个可行组合。该偏好在新数据处理前记录在brief，不依据模型结果/答案/文本长短。异常记录及同问题家族不能入选pilot；保留原数据与旧审计。

[RUN] 最终实际选择覆盖4个不同保守分量，无须触发放宽。清单固定的是**开发预留**，`actual_model_exposure=false`；本项目尚未调用模型处理这些题，预训练污染未排除。保守相关248条被预留，52条未预留，正式calibration/held-out划分和功效Pending。不能将开发预留说成已经实际模型曝光，也不能将剩余行数等同独立N。

## 客户端与应用边界

| 接口 | 合同 |
|---|---|
| `ClientConfig` | 唯一精确endpoint `http://127.0.0.1:11434/v1`；冻结model/manifest、输出/context/请求数量/请求与响应大小/时间上限；retries=0 |
| `OllamaHTTPBackend` | 无默认云端、无.env/key读取；生产httpx构造trust_env=False、follow_redirects=False；非200与redirect失败，不另追Location |
| `ContextBinding` | 必须有有效模型/context/部署tokenizer证据；未核验默认拒绝，不因模型metadata宣称32768就算配置通过 |
| `ControlledClient.generate` | 冻结request、SHA绑定payload/response/模型与执行身份；每次检查精确token预算和模型digest，禁止输入裁切；60s同时覆盖metadata与生成 |
| `JsonlAuditSink` | 新文件exclusive创建，逐phase flush/fsync；started/request_ready/completed；有界、不可覆盖旧日志，达到cap失败停止 |
| `run_controlled` | 新顺序应用driver，以原LocalAgent后处理、模板、parser和本地板运行；没有gold参数；No-A2A仍能提交本地答案；首请求失败也返回started记录 |

原`run_fixed`与旧67合同未被替换。新driver未来可接实际backend，本轮只接替身。读取全量数据/gold用于离线注册与评分的controller不能把它们传入agent/client；request日志属于审计，不是免费共享transcript。

`LivePermit`只是可信driver的协议/registry哈希绑定，**不是用户授权本身、不是恶意代码沙箱**。没有获批协议时不能构造permit使模型运行；本轮只在fake HTTP测试中验证它。没有真实campaign执行CLI；本轮不接通LLM服务。未来必须在同一全局预算对象中复用客户端，不每episode重开98次额度；resume与总存储/墙钟管理仍需由获批driver执行。

超时/连接/API/JSON/model mismatch/不合法finish reason/截断/usage错误都显式记failure，不能把部分答案当正常输出。缺usage保留null与flag，不按words补token；这不一定阻断描述性质量筛查，但阻断声称完整推理成本已核验。收到usage时与精确prompt计数及输出cap核对，差异fail-closed；兼容性尚未对真实模型验收。

## 验证层次

[RUN] GOSC项目venv中最终组合147pytest合同通过，包括旧67与80个新增case；独立Reasoning环境另有5项真实httpx0.28.1 MockTransport合同通过。后者用实际httpx构造/序列化/异常类/redirect语义，但socket.connect被禁止，未发生真实网络或模型请求。纯替身验收不能冒称实际服务chat/context能力。

阶段产物、运行ID与实际边界见[验收报告](../reports/masbench_reasoning_preparation_acceptance_2026-11-03.md)。[上下文与资源预算](masbench_reasoning_context_resource_budget_v1.md)已给出上界，精确tokenizer、有效num_ctx及未来独立池充分性仍是进入真实调用前的条件。

补充：新driver与24组既有原生等价fixture逐项一致，有效空完成保留原生语义。60s是操作接收期限＋HTTP timeout；物理中断/慢速流的外层watchdog在未来执行driver中仍需核验，不能凭晚结果丢弃推断服务端计算已被取消。
