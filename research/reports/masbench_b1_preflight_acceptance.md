# MASBench Reasoning B1-pre 准入验收

日期：2026-11-10。**静态审查与独立保护原型验收完成；真实B1能力诊断仍Blocked，当前不具备完整申请准入条件。** 可另行批准补齐精确部署计数与执行保护；不得把本轮17合同、历史147+5合同当作模型能力、任务收益或可发表贡献。

交付入口：[Tokenizer / Context](../benchmarks/masbench_context_tokenizer_preflight_review.md)、[数据与统计](../benchmarks/masbench_data_split_and_power_feasibility_review.md)、[执行安全规格](../protocols/masbench_b1_execution_safety_spec_v1.md)。本轮LLM chat/generate=0、真实Reasoning episode=0、训练=0；未安装/下载/改服务/新增数据/改变registry/gold/评分或Git commit/push。G1/GP-ID科学No-Go保持。

## A. 当前证据与版本

| 身份 / 证据层 | 核验结果 |
|---|---|
| 当前Git归档 [CODE/RUN] | 本地/HPC HEAD 4754bede84bb6e6defd8e646a63e81ccd6a20b4b，研究分支research/progress-audit-2026-10-19；本轮新增源为dirty快照 |
| 科研基线 [CODE] | 014b85dfc472c45d8ea5f15e83e0c1ed8e938daf+冻结扩展；旧run Git/sync身份不改 |
| Benchmark [CODE] | BUPT-GAMMA/MASBench c0301a650db95958924bb080192c09fef39389a5；本轮未换版本/任务 |
| 模型 [RUN] | qwen2.5:7b固定manifest845dbda0…b697e；完整SHA见Tokenizer报告；模型metadata头及小层核验不冒充全权重重哈希 |
| 数据 [RUN] | 11月3日原data与registry证据；本轮registry文件SHA再次匹配，确定性描述性汇总，不生成新成绩 |
| 历史合同 [RUN，非本轮] | 11月3日最终147pytest与独立httpx MockTransport5；未在本轮重跑，不累加为本轮169或其他总数 |
| 本轮合同 [RUN] | 17个新独立安全合同通过；无真实HTTP/模型；不等价整合Driver已经通过 |
| 尚无证据 | Full比No-A2A好、精确部署tokens、实际长context承载、GPU推理峰值/时延、完整真实driver硬停止、正式统计功效 |

[RUN] 初次SSH核验因HPC旧Git不支持 `branch --show-current` 失败，改只读 `symbolic-ref --short HEAD` 后确认n1/UID8301880。随后发现远端Git HEAD014b85d仍未更新至已归档4754bed；按AGENTS E1暂停同步并询问，用户明确允许核验后仅快进引用。825个归档管理文件比较发现33个缺失（主要11月4日归档副本/说明）与6个文档/规则差异，其余已匹配。bundle校验、祖先关系核验后update-ref快进；没有reset/checkout/工作文件删除。正常同步备份变化并保留远端独有文件，838文件SHA mismatch0。

[RUN / 解释限制] 只更新远端分支引用，未改写旧index；因此本轮HPC manifest的dirty状态含旧index产生的D/MM及重复untracked标记，**不表示同步后的文件实际被删**。逐文件source_snapshot的remote_sha256与运行源码是事实边界，source_changes.patch/untracked快照如实保留，不为“干净状态”修改历史或用户index。本地原工作区干净，本轮dirty均有来源。授权与核验见 `research/logs/masbench-b1-pre-2026-11-10/`。

## B. Tokenizer / Context 结论

[RUN] 实际serve PID8964白名单环境为1024 context、单并发/单加载，GGUF架构metadata为32768；无params覆盖层。GGUF tokenizer词表/merges存在，GGUF模板2509bytes与实际Ollama模板层1482bytes不同。独立Python仍无已登记的tokenizer实现依赖；runtime/bin只有ollama，无已核实独立tokenize工具。未加载模型或发HTTP探测。

[CODE/HYPOTHESIS] `client.py:158–299`的绑定/溢出/usage拒绝机制正确性的前提是计数器与部署一致。必须先完成实际Go模板+同GGUF tokenizer/special-token策略的精确计数，并绑定生效runner context、配置、manifest；每次完整请求满足 `exact_prompt_tokens+512<=effective_num_ctx`。不能以bytes、架构上限、debug已裁剪prompt或fixture的verified代替。**A Pending/Blocked。**

## C. 数据与统计结论

[RUN] D1预留248行164家族4分量，余52行**36家族34分量**（35easy/17hard，含2条原异常）；D2假设只预留选中4家族则6行，余294行196家族，2个文章分量跨开发边界。没有实际改划分。

[HYPOTHESIS] 建议保留原四题及当前保守曝光边界用于未来开发screen，不重选题。D1可以做受限独立评价设计，但不能从名义34分量承诺多策略正式研究功效；D2可另提“固定语料中的新问题”协议，文章复用必须披露，不能声称与D1同严格或新证据泛化。正式calibration/eval尚未冻结，效应/方差/文章相关未知，power与统计精度Pending。跨任务/证据泛化主张建议第二独立公开数据集；本轮不接入。**B静态Go；研究设计Conditional Go，正式评价Pending。**

## D. 执行保护的实际支持域

| 接口与源码 [CODE] | 已有能力 / 缺口 |
|---|---|
| client.py:71 LivePermit | 协议/registry身份合同；不是科研授权或进程安全沙箱 |
| client.py:158 ContextBinding / :166 ControlledClient | 未核绑定拒绝、精确token接口、metadata+generation共同操作期限、响应/usage核验；不能物理取消外部服务 |
| client.py:301 JsonlAuditSink | exclusive/fsync及单文件cap；未接入新Ledger总cap |
| client.py:323 run_controlled | 原生单episode语义/已启动失败；无跨episode持久预算、恢复和外部watchdog |
| application.py:56/77 PrivateView/LocalAgent | 只给自有证据、自有完整历史、已送达peer及本地累积板；审计transcript不进入对方输入 |
| wire.py:84 ContractTransport | UTF-8实际帧/CRC/ACK/UL/DL及有限重试；模拟CPU slot与模型wall不能混用；本轮不改 |
| execution_safety.py:50 Ledger（本轮） | flock/hash-chain/fsync，固定身份/plan，预留requests/tokens/metadata/shared bytes，失败不退款，跨boot/孤儿inflight拒绝恢复，started分母不消失 |
| execution_safety.py:228 supervise_owned_worker（本轮） | 对自有假worker组真实TERM/KILL、操作/全局较早deadline、有界管道；不杀Ollama，不证明服务端取消 |
| scripts/hpc_runs.py run / scripts/sync_hpc.py RECEIVER | manifest/status、source snapshot/patch/untracked、日志/产物SHA及独立回传receipt；不是整个科研driver的6000s/256MiB强制执行器 |

[RUN] `hpc-masbench-b1-safety-20261110`：17tests、0failure/0error，unittest1.045s、登记elapsed1.225419s。实际fixture覆盖：身份/计划/限额漂移、独占锁、损坏/尾行截断、崩溃后已启动分母与预算、失败不退款/不重跑、请求输入输出/metadata额度、resume停机计全局时间、JSONL/wire/journal共享字节上限、路径/覆盖拒绝、超时fence、TERM-ignore及继承pipe后代强杀、输出洪泛停止、正常返回与GPU未知值。新合同runner在父进程禁socket connect，假worker只执行内置固定脚本；未用真实题目或Ollama调试。

[CODE / 未满足] 以下不是通过项：真实HTTP与Ledger/worker的完整接线；96任务+2合成子配额；新日志与现有JsonlAuditSink/无线事件的单写者接线；外部监督器在Driver自身崩溃时仍兜底；任意临时/子进程写盘的目录硬quota；Ollama服务端取消/空闲确认；可归属实际模型的CPU/GPU采样；所有产物及管理开销的实测投影。C为**独立原型支持域Go，真实Driver准入Blocked**。不能将小fixture额度缩放为6000s/256MiB真实campaign实证。

[CODE] 假worker截止后仍有50ms TERM宽限与有界reap；若整轮6000s包含清理，未来应预留清理窗口并验收外部监督器。当前不能宣称CPU/服务在deadline瞬间已经停止。实际模型GPU峰值和推理wall均未测。

## E. 将来最小真实能力诊断的完整准入条件

[HYPOTHESIS / 全部满足才申请真实运行] 以下清单不构成本轮授权：

1. 精确部署tokenizer/实际模板、模型manifest、服务/runner num_ctx及每次完整请求计数身份核验；如改context或安装构建依赖另获授权。任何漂移/溢出拒绝，不改历史或删context。
2. 研究人员在模型曝光前审阅D1保留代价与D2限定主张；保留当前registry，或**另行批准**正式修订。原四题身份不临时替换：25/sample_251_f128c587；124/sample_153_1d14c5cc；294/sample_278_79ddf47b；259/sample_152_1d4d49b1。完整家族SHA与registry绑定。
3. 固定qwen2.5:7b及上述manifest；base主、protocol辅，temperature0但不宣称绝对确定性；Full-reliable与No-A2A同题/模型/Prompt/参数/任务私有观察/环境配对，先验固定顺序，不按结果重排。
4. 预算：4家族×2Prompt×2设置=16episodes，最多6总发言/episode；96任务+2合成API预检=98生成、106metadata/204总HTTP、retry0、单active；512输出/次、50176总输出上限；输入3161088仅是候选32768窗口下算术上界，不是实际工作量；操作60s包含GET与generation，整轮6000s、任务产物256MiB。管理source snapshot单列，整体磁盘需单独够用。实际投影与硬cap验收仍须补齐，不能把98次当必须耗尽。
5. 完成真实driver的durable预算/恢复/全写路径/请求及外部全局watchdog无模型集成验收。授权后合成端点预检也必须计费；服务取消若不确定立即fence，直到有明确受控处理与确认，不能继续下一调用。真实服务取消测试本身也需单独授权。
6. started先fsync再请求；模型错误、parse/None、输入超限、usage异常、输出截断、超时/中断都保留记录，失败计0，原生EM/F1/None与工程失败单列；未启动另列，配对不完整不通过。有效答案/消息仍按原生parser/协议，不用金标驱动策略。
7. 资源记录覆盖usage或null、真实wall、CPU、采样GPU、UTF-8/headers/ACK/UL/DL uses与失败；关闭首次能力screen的新无线损伤，保持Full原生语义，禁止免费共享transcript；必须保存实际送达及下一请求输入的对应证据。
8. 仍用11月3日预定base质量screen：≥2 Full EM正确家族、≥1同题F1正差且有真实peer交付影响下一输入。只是描述性线索；失败则当前模型/预算/通信空间No-Go，不自动扩题/换模型/提示词救结果/训练。若通过，仅允许另提任务效用与内容级识别设计，不直接进入正式论文效果实验。
9. 上述缺口、预算与失败/停止规则全部可审阅后，取得用户**明确的新真实模型运行授权**；旧LivePermit/预算JSON不改成自动获批。正式测试集、训练、增加题目及付费API继续禁止。

## F. 判定与下一步

| 关卡 | 本轮判定 | 依据 |
|---|---|---|
| B1-pre静态研究交付 | Go | A/B/C边界和四交付完成，已有数据只读、17新合同 |
| 独立保护原型 | 限支持域Go | 固定fixture与自有进程保护；没有真实整合driver声明 |
| 路线B继续准备 | Conditional Go | 仍可补精确计数/执行合同，再看最小能力screen是否值得申请 |
| 现在运行真实B1 | **Blocked / No-Go** | tokenizer/context、服务取消、全Driver/存储硬边界等缺证据，且本轮明确禁止 |
| 正式评价、复杂估值器训练 | **No-Go** | 无真实通信必要性/内容识别/收益证据、划分与功效未冻结 |
| G1、GP-ID旧科学结论 | **No-Go保持** | 本轮不重估、改写或覆盖旧负结果 |

建议下一授权只覆盖**精确部署tokenizer/context方案及无模型Driver整合保护**；服务配置、依赖安装和真实取消预检按具体方案另审。先解决这些确定阻断，再申请四题诊断；不以更多保护测试掩盖尚无任务信息价值证据。完成本轮即停止。

# Research Task Report

- **Research Question / Hypothesis**: 逐请求无截断、独立评价边界及失败/预算恢复能否可信成立；不是检验新方法优越性。
- **已核验前人工作**: [PAPER]本轮没有新增论文结论或重新阅读全文；沿用既有MASBench静态审查。外部新核查为固定Ollama v0.11.11官方源码及GGUF格式，来源在Tokenizer报告，不冒充论文事实。
- **实际阅读源码**: [CODE]client/application/registry/wire、hpc_ollama/hpc_runs/sync_hpc；根AGENTS/说明书/README、用户指定环境/预算/规格/prepare与数据审查、冻结registry及已有审计。函数/接口映射见D；新独立模块与两入口/测试如上。
- **本轮新增或修改**: 三规格/审查+本验收；execution_safety、preflight脚本、safety合同入口及测试；task brief/log/experiment manifest/evidence index与当前导航。未改核心/旧客户端/数据/历史冻结文件。
- **实际运行**: [RUN]两个HPC登记run；精确launch/argv、source sync/dirty/manifest与receipt见下方及日志manifest，无seed/任务调用。另有本地Git/SSH/文件哈希/同步管理，不是本地科研测试。
- **测试与结果**: [RUN]17/17新安全合同；A/B只读分析exit0。没有新任务成绩或CI；旧147+5未重跑。
- **失败/负面证据**: SSH预检旧Git选项失败；本地PowerShell路径解析、rg glob、README patch标题不匹配及管理索引schema误读（KeyError）先后修正，未触发本地项目测试或修改HPC原件。tokenizer/context未verified、真实取消/整合预算缺口保留；未删除历史失败。
- **与原 GOSC 的差异**: 独立研究安全原型；不变原估值、候选、无线、BF-selector，不把工程模块宣称新调度算法。
- **公平性与泄露检查**: 无gold在线输入/新划分/实际曝光；D1/D2主张不同，全started分母/No-A2A自主作答及真实交付路径必须保持。
- **成本**: [RUN]A/B0.855051s，安全合同1.225419s；CPU/RSS含runner管理开销，GPU峰值null。模型tokens/channel uses无新增实测，固定wire合成文件不是任务通信。原始输出8898+276bytes；自动回传约120MB主要是管理source快照/历史metadata，不是本轮科学产物，也不计入未来256MiB任务预算。详见两receipt。
- **可否进入下一阶段**: Conditional Go仅指准备；真实B1 Blocked，正式test/训练No-Go。
- **用户需要批准的下一步**: 先审阅具体计数器/服务context方案与剩余Driver保护；之后另批最小能力诊断。本轮未请求也未获得真实生成授权。

## 实际命令及原件

本地发起，下列子命令实际在HPC执行；launch前均有同步哈希核验，完整命令保存在run manifest：

```text
python scripts/hpc_runs.py launch --run-id hpc-masbench-b1-preflight-20261110 --kind analysis --stage MASBench-B1-pre-AB --purpose "Read-only deployed GGUF/context inventory and immutable registry D1-D2 summary; no HTTP or model generation" --model qwen2.5:7b -- /usr/bin/timeout 120s /home/u202520081000097/jupyterlab/Paper/gosc/.local/envs/masbench-reasoning-v1/bin/python experiments_ext/masbench_b1_preflight.py
python scripts/hpc_runs.py launch --run-id hpc-masbench-b1-safety-20261110 --kind test --stage MASBench-B1-pre-C --purpose "Independent persistent budget, failure/resume and owned fake-process hard-watchdog contracts; network and models forbidden" -- /usr/bin/timeout 125s {python} experiments_ext/masbench_b1_safety_contract.py
```

[RUN] `research/sync/runs/hpc-masbench-b1-preflight-20261110/{manifest,source_snapshot,status,artifacts}.json`及outputs/preflight.json、stdout/stderr；`hpc-masbench-b1-safety-20261110`同结构及outputs/safety_contract.json。回传receipt `20261110T030625Z-0a4021`与`20261110T030748Z-00d31d`均all_outputs_mirrored=true并写回HPC；分别60,152,322与60,147,247bytes（管理通道为主）。最后文件/冻结源/同步核验见本轮management_verification.json和task_log，执行完成不与最后文档上行混为一谈。

[RUN] 本地轻量文件核验确认73冻结源码SHA无差异、本轮两个原始输出与artifact索引相符、四个新增Python源与最终HPC安全合同source_snapshot一致；无新测试重跑。最后文档上行结果单独记录为本轮日志的final_upload_status.json；该管理回执生成在同步完成后，不假称属于此前测试源码快照。
