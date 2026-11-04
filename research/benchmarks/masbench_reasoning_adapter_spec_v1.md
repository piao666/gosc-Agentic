# MASBench Reasoning无线适配静态规格 v1

2026-11-03实施更新：[独立无模型接口合同](masbench_reasoning_adapter_contract_v1.md)及[HPC验收报告](../reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)。最终67合成合同通过；正文300条但仅200规范化问题、100变体组，2条support异常，数据划分未冻结。只实现context/固定响应与串行传输合同；没有模型任务入口，不解封真实任务/训练。下文设计稿与历史Pending保留制定时含义；部署CPU/随机信道/模型上下文仍Pending，G1/GP-ID科学No-Go不变。

2026-11-02 15:32（Asia/Shanghai）环境维护完成：三个本项目历史digest模型的manifest/blob恢复并校验，独立Reasoning客户端依赖及SDK模型清单/metadata验收通过，见[环境说明](masbench_reasoning_environment_v1.md)和[维护报告](../logs/masbench-environment-repair-2026-11-02/report.md)。仅基础环境Go；无模型加载/生成、Benchmark集成或任务实验。下文空清单/超时为历史快照；规格设计、数据/能力/工程合同Pending与G1/GP-ID科学No-Go均不变。

2026-11-02 13:46（Asia/Shanghai）只读复核：HPC连接已恢复，基线/身份一致；Ollama在线但模型清单为空，已知三个标准manifest未找到，项目缺openai/httpx等依赖。连接阻断解除，环境就绪仍No-Go；不代表所有服务器位置均无权重。见[新快照与记录](../logs/masbench-reasoning-hpc-2026-11-02/task_log.md)。未调用模型、运行测试或修改规格设计。

2026-11-02复核：本规格仍为静态设计，无实现或运行授权。固定版本关键消息路径已再核；HPC只读连接重试均超时，当前环境状态Pending，不能将下引10月30日环境快照当作今日实况。见[复核记录](../logs/masbench-reasoning-static-2026-11-02/task_log.md)。规格、研究问题与G1/GP-ID科学No-Go不变。

日期：2026-10-30。状态：**设计稿，未实现/未集成/未运行，非可执行预登记**。GOSC基线`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`加冻结研究扩展；MASBench固定到`c0301a650db95958924bb080192c09fef39389a5`（main查询时的HEAD）。仅Reasoning，不接入其他任务或框架。

证据标签：[CODE]固定版本源码；[PAPER]原文；[RUN]本次只读环境盘点或已存在运行；[HYPOTHESIS]未来设计/研究判断。**G1和GP-ID科学No-Go均保留；本规格不声称它们可迁移成功。** 当前放行状态见[关卡矩阵](masbench_reasoning_gate_matrix.md)，研究风险与资源见[可行性审查](masbench_reasoning_feasibility_review.md)。

## 1. 研究问题与支持域

[HYPOTHESIS] 在双方拥有互补私有证据、只能通过真实交付的消息影响对方上下文时，任务信息交换是否存在超出发送频率/长度/简单价格的价值，并值得支付无线与推理成本？首先只验证任务能力、信息依赖和传输边界；不训练价值模型，不假定任意receiver-aware估值优于简单规则。

初始支持域：两个同模型agent Alice/Bob；`mode=context`，原私有全文/distractors保持；固定base或protocol提示族；一轮=一个speaker的生成机会，Alice先、严格交替，**不是一对Alice/Bob发言**；每次完整逻辑消息不可语义重写，物理分片对应用透明。一个任务中只允许当前turn的一条逻辑消息在途；不实现并发聊天、语义片段候选生成、重排或共享全局记忆。`support`只作另标的gold-selected-evidence设置，不与context混合成同任务的主结果。

研究边界：Reasoning不提供GOSC占用概率场、位置/意图或Search奖励，不能搬用G0/G1/TeamModel。单在途整消息接口可检验发送门槛、保护与任务信息依赖，**不能单独证明同状态下多个内容候选的排序贡献**；若该自由度不存在，后续内容估值主张应No-Go，不靠训练补救。

## 2. 已核实的原生消息路径

[CODE] 下表均为[固定commit](https://github.com/BUPT-GAMMA/MASBench/tree/c0301a650db95958924bb080192c09fef39389a5/Reasoning)中的实际活动代码；文件里被注释掉的旧实现不作当前事实。

| 入口 | 位置 | 原生事实 / 未来接口边界 |
|---|---|---|
| 数据 | `src/data_loader_v4_mas.py:69–150` | question/answer/两份context同在Sample；context仅按agent_a/b构建，support另取supporting_facts。`raw`不是可给agent/估值器的安全对象 |
| 私有初始化 | `src/run_asymmetric_agents.py:243–270` | Alice/Bob各收到同一question和自己context；不把reference answer、另一份context或difficulty传入system prompt |
| 模型输入 | `src/agents.py:142–167` | system+本agent memory；以姓名前缀判定self为assistant、其他为user，不是所有历史均为user |
| 生成 | `agents.py:169–187` | chat completion，strip、补`Name:`前缀，自己的完整输出先进入自己的memory；未在此验证协议标签或事实正确性 |
| base交换 | `src/conversation.py:101–142` | speaker.step→transcript→listener.add_memory(full)→parse_answer→首个truthy答案停止 |
| protocol交换 | `conversation.py:145–215` | 提取MESSAGE后，控制器累积所有`<R>`事实，给listener附加知识板，再从visible解析答案 |
| 答案解析 | `conversation.py:39–98` | 倒序查找非占位`<A>`内容，去一个末尾句点；否则首个boxed；MESSAGE找不到则返回全文，大小写规则不同 |
| 原计量/评分 | `run_asymmetric_agents.py:26–69,313–401`；`src/metrics.py:99–174` | 原comm_tokens是去答案span后的归一化words；平均F1剔除None，不是全样本正确率 |

[CODE] 原生protocol的MESSAGE是匹配`Name: MESSAGE`起始行至输出末尾的片段，不是严格XML容器；找不到标记时**整份生成文本会发给对方**。`<Q>/<R>/<A>`、首轮必须提问/不能回答、只写verified facts主要由prompt约束，运行时没有完整schema/grounding守卫。不能称protocol自动保证隐私、正确事实、首轮不作答或“思考内容永远不传”。

[CODE] `conversation.py:170–202`的shared_blackboard按生成的visible文本提取R、strip、精确字符串去重，保持插入顺序。它不是数据库真值；错误/互相矛盾的R也会进入。listener收到的实际字符串是visible加累计板后缀；原comm统计只重提取transcript里的MESSAGE，**没有完整统计附加的板副本**。`transcript`本身仅控制器保存；原生共享效果由每次add_memory完成。

## 3. 在线信息权限与最小适配接口

[HYPOTHESIS/设计] 未来独立扩展，不修改原GOSC或直接改写第三方活动代码；只在消息交付/本地记忆包装边界接入，并保存原生参考实现。建议接口名称如下，尚无实现文件：

| 接口 | 输入/输出 | 允许内容 |
|---|---|---|
| `build_private_agent(i)` | 安全agent view→system prompt | shared question、自己的context、原模板/模型配置；禁Sample.raw/answer/peer context |
| `generate_turn(i)` | 本地request→完整输出full | 沿用原消息角色/strip/姓名前缀与self memory追加，不注入全局transcript |
| `extract_peer_payload(full,style)` | immutable visible UTF-8 bytes | base=full；protocol=原extract_message_block结果或原fallback；保留答案span，不事后裁掉标签/空白 |
| `offer_message(meta,body)` | 发送端本地信息→admit/hold/reject | 本sender可见的body、自己的已收/自生历史、公开链路和本地队列；禁接收者真实memory/答案正确性 |
| `advance_transport()` | 帧队列→receive/drop/expire等事件 | 只处理bytes/公开元数据、合法CSI与外生随机场，不读QA gold |
| `deliver_once(receiver,id,body)` | CRC/重组完整→本地memory | 只在实际交付后可见；不得从日志、全局板或发送端私有输出补齐 |
| `publish_local_answer()` | 原parse_answer(本次source full/visible)→外部最终输出 | 与原任务相同的首个truthy答案规则；不能用gold挑最好答案/强制共识 |
| `evaluate_offline()` | immutable task outputs+gold→指标 | 与在线agent/调度器隔离；ground-truth只在这里及离线受控数据处理可见 |

`id/level/answer/supporting_facts/raw`留在loader/评测信任域。尤其level可能由含答案长度的难度指标生成，不作在线估值特征；可用于离线预登记分层。模型服务在HPC共享运行不意味着agent上下文共享；本研究模拟的无线是A2A，初始私有证据预置及LLM RPC不算A2A radio，但其推理tokens/延迟必须计入计算账本。若声称真实边缘推理offloading，还须另计prompt上传，当前不支持这种外推。

### 3.1 共享知识板的无旁路实现

[HYPOTHESIS/设计] 每agent维护本地有序R列表：只从自己的已生成visible、及**已完整收到**的peer visible中按原regex/strip/精确去重规则更新。收到当前visible后，用该receiver本地R列表拼接**与原生逐字符相同**的知识板后缀，再调用listener.add_memory；不额外给本次speaker的self memory附板。

这是本地重建/计算，不是免费同步：无法从丢失消息、controller全局transcript或另一agent的本地板获取事实。板重复占用后续模型输入tokens，更新/渲染占CPU，必须计价；无需再次传输receiver已经本地拥有的同一事实。消息body中的R仍正常计UTF-8无线bytes。

零损伤时双方以同一turn顺序观察全部自生/收到的visible，有序列表应与原全局板一致；损伤时可不一致，不能偷加“自动修复”。原prompt中“shared”的措辞原样保留，记录板可因实际传输损伤分歧；未来若改prompt解释分歧，须另作提示族，不能冒称当前零损伤完全相同。

### 3.2 最终答案与无通信对照的关键边界

[CODE/设计] 原任务是**第一个被parser识别的团队外部答案**，不是双方达成共识；原代码甚至在partner下一次调用前停止。为保持该语义，无通信/主动拒发时，source依然可以用自己可见信息输出最终答案给离线评测器。该输出不写入peer memory，不读取gold反馈，也不是免费A2A消息。否则“无通信得0”将是人为禁止答题的必然结果，无法识别信息依赖。

每turn：生成→self memory/本地板→形成真实A2A payload→执行transport barrier至交付或明确失败/拒发/过期→用原parser检查**该source本次full或visible**，无论peer交付是否成功；若truthy则停止，否则换speaker。答案发布时刻为barrier结束；有任务deadline时超时答案不计timely F1。被发送的消息含A/boxed文本时**全部bytes照收**，不沿用旧comm统计的答案免费扣除。无通信仅关闭A2A路径，不禁止source本地外部输出。若未来研究要求“答案必须经无线交付到专用sink”，那是新任务修订，须给所有方法同等sink通道及费用，不能混在本v1中。

## 4. 应用、队列、可见和推理时间

[HYPOTHESIS/设计] 同时保存真实单调wall/process时间和离散无线slot；slot长度Δ、CPU映射及绝对deadline在未来运行前冻结，不拿Python循环次数当时间。

| 时刻/事件 | 定义 |
|---|---|
| `request_start/end` | 实际模型请求发出/完整返回；失败也留attempt/用时/usage可得性 |
| `created` | 原strip/前缀处理、self memory及payload抽取完成；记录与该请求hash绑定 |
| `offered/admission/enqueue` | body提出、策略决策、实际进入编码/服务队列；三者不得合并 |
| `encode_ready/tx_start/end` | 编码CPU完成和帧占用无线资源；未服务不能算已交付 |
| `edge_receive/forward_ready` | UL解码/校验与edge缓存完成；不是Bob已可用 |
| `receiver_receive` | DL片段解码/校验；未齐片不进入应用 |
| `visible` | 全部片段合法重组、去重、receiver CPU与板更新完成后，恰追加一次memory |
| `next_inference` | barrier解决且轮到该agent时，才以当前local memory建request；已发request不能被晚到数据追改 |
| `answer_publish/episode_end` | 原parser识别/任务deadline/turn上限/运行失败；与最后一帧服务完成分别留账 |

一次只有一条逻辑消息在途，后续turn等该消息结果；这是最小顺序workflow，不做从未收到信息的伪全历史。reject/drop不添加“对方说了某事实”的占位文本，不为模型提供真实丢包结果/新任务反馈。ACK丢失但receiver已visible的消息不得撤销；它可造成sender等待与重复传输，但重组/memory幂等。

## 5. UTF-8、分片、CRC和资源合同

[HYPOTHESIS/设计选择，非已验证wire] body是不可变UTF-8；不按model token换算bits，不压缩、重写、自动修语法或将半个字符交给模型。逻辑消息SHA-256只进审计账本，若未来要在线发送该hash须另计字段。

候选帧v1：网络字节序，固定24byte header + payload + 4byte CRC32（共28byte固定开销）。字段：magic2、version1、kind1、episode_id4、message_id4、src1、dst1、created_slot4、fragment_index2、fragment_count2、payload_length2；CRC覆盖header+payload。episode_id在登记命名空间保证唯一，溢出/冲突/错路由/非规范UTF-8/长度不符显式失败，不靠hash截断碰撞通过。

kind区分UL_DATA、UL_ACK（edge→sender）、DL_DATA、DL_ACK（receiver→edge）；两个ACK均为空payload、同28bytes。src/dst包含Alice/Bob/edge公开节点编号。created_slot供合法age；TTL是公开冻结常数，expiry=created+TTL，不发送receiver私有状态。分片数/长度固定，重试不重组内容；序列化后以实际`len(frame)*8`计费。

**粒度建议**：静态候选P_max=16bytes/片，尾片可短；不是已批准部署点。其目的是使帧在原W100/rate集合的一部分档位可装下，仍需未来成本审查。28byte开销本身就有224bits，ACK和最小数据帧在W100下r≤2不可行；16byte满片44bytes在r4/5/6可行，不能假称所有原rate仍有用。若新wire使“调度自由度”再次退化，关卡失败，不能事后增W或省ACK掩盖费用。

| 规则 | v1设计 |
|---|---|
| 拓扑 | source→edge UL，再edge→指定peer DL；禁止edge把私有context或额外板广播出去 |
| 物理模型 | 复用GOSC Channel的合法统计CSI、公开rate、outage/FBL法则；QA无位置，固定公开链路条件/外生几何在各方法共同冻结，不从成绩决定SNR |
| 空口收费 | 各hop每次尝试`uses=ceil(8*len(frame)/rate)`，失败同样收费；UL包括source DATA和receiver DL_ACK，DL包括edge DATA和edge UL_ACK |
| 每slot预算 | 每UL节点/共享方式、edge总DL和ACK竞争均显式配置/检查；v1优先正交UL，不能默认为已验收共享上行 |
| ARQ | 每数据片每hop最多3次尝试（首发+2重试）；ACK不再要求ACK，丢失由对应数据超时重试；失败/重复/ACK费用全记 |
| RTO/因果性 | 至少覆盖编码、数据服务、解码、ACK服务与传播下界；禁止同slot递归即刻重试/新收即免费转发；具体值须未来成本合同冻结 |
| 幂等 | edge和receiver按episode/message/hop/fragment去重；重复数据可触发已计价ACK，不重复融合板或追加memory；重试也不调用LLM再生成 |
| TTL/deadline | 公开消息TTL与任务D_episode分别固定；晚到/过期片不进入新request；有部分服务时保留消耗与未服务量，不计为完整delivered |
| 容量/失败 | 帧单次不可装、队列满、编码/解码错误、次数耗尽均显式状态；不丢失败任务换新样本，不自动放宽budget |

ACK控制率/完整链路参数、队列/生成文本上限、TTL/任务deadline及单run总时限/产物cap尚**未冻结**。未来应共同确定最小合理服务配置，当前不能执行。GOSC原GP wire与receiver_summary服务不能原样声称覆盖新文本帧；需要独立合同，保留旧版。

## 6. CPU、模型和通信成本边界

[HYPOTHESIS/设计] 分别记录：payload生成、抽取、UTF-8编解码、分片/CRC、选择器、ACK、重组、板更新/渲染、request组装、模型prefill/生成与日志观察。CPU服务时间需未来实测或明确模型系数（如a+b·bytes），目前无系数，不允许默认为0或沿用旧固定.001s冒充LLM实测。模型wall延迟、可得process/GPU观测和逻辑队列收费分开。

模型call的prompt/completion/总usage、有效输出长度、失败次数、服务端digest/上下文上限均记录；API没回usage写missing，不用words估计冒充真实tokens。系统初始私有context和self完整输出不走A2A，但其每次模型输入/本地存储和计算成本不免费；知识板每次重注入也照计。ACK只证明传输，不泄露接收者belief/推理正确性。

所有资源同时保留offered/served/unserved、已成功/失败尝试与right-boundary在途量；任务提前结束后若冲刷队列，作为统一的单独drain账本，有硬上限，不混成免费完成。未来主要任务—UL+DL—compute前沿应使用共同冻结的边界，而非任意净效用权重。

v1的初始角色/问题预置、固定交替顺序与本地会话driver属于共同应用配置，不给peer额外QA事实。若以后新增无线START/GRANT/DONE广播、状态探测或模型RPC offloading，其帧和服务费用必须另列，不能借“控制面”免费传transcript；当前不声称覆盖完整物理部署控制面。

## 7. 零新增无线损伤等价合同

[HYPOTHESIS/待验收] Identity profile固定原数据view、prompt族、模型request参数、Alice先/交替顺序、max_rounds、原活动parser、self完整输出与本地板规则。传输可靠、无策略拒发、无过期/截断/队列溢出、无额外应用deadline终止；允许有限airtime，只在barrier内等待，不向模型暴露新时钟/反馈。若实现使用纯零时间stub作合同，只能称接口identity，不能当无线部署成本结果。

未来先用同一预先固定的返回字符串fixture检验：每次`_build_messages()`的role/content/order、两agent memory、listener板后缀、transcript、首个停止位置、final_answer、原legacy统计逐项相等；覆盖base/protocol、fallback、重复R、多A、占位/空A、boxed、首轮早答及None结尾。只用fixture验证接口，不把固定回答回放说成动态LLM任务能力。

再对相同模型request+相同响应证据核验；不能因两次真实模型输出不同就强行修改parser/prompt使数字相等。源码/数据/依赖/模型digest/配置/请求与响应hash、随机流键、失败与产物索引均冻结。无损控制如果仍改变输入或任务输出，**No-Go，停止能力诊断**。

## 8. 评价分母与原生兼容字段

[CODE] 活动`metrics.py:99–174`用SQuAD式归一化：lowercase、删ASCII标点、删a/an/the、压空白，以words多重集算F1，空/空返回1。旧注释中的“非字母数字切分、保留冠词”不是当前实现。原生没有独立EM/任务正确率主字段，不能把F1叫作严格准确率。`run_asymmetric_agents.py:363–374`只对非None F1取均值，效率是该均值除以**全体总comm words/1000**，会随样本数改变。

[PAPER/解释边界] 论文附录C.4是framework-level评价，包含未识别答案计0及不同normalization表述；本轮不接入该框架，不能把该口径当原生runner已实现，也不能只据此否定原论文全部主表。[论文](https://arxiv.org/html/2610.04672v1#A3.SS4)

[HYPOTHESIS/设计] 并列保存两套字段，禁止覆写旧指标：

1. `legacy_native`：完整保留原F1/None/comm_words/效率口径与源码版本，供identity与原生复现。不能用它作有损传输条件下的唯一主指标。
2. `wire_eval_v1`：在结果前冻结的已启动任务集合N上，未回答、解析失败、模型错误/超时、任务deadline失败全部F1=0；答案只取第一个按原规则提交的，不以gold挑选。报告`mean_F1_all`、同normalization下新增EM、answer rate、timely answer rate、错误类型及分母。EM新增字段单独命名，不冒称原指标。

所有方法共用预登记问题ID/重复索引。`N_planned/N_started/N_completed/N_error/N_unanswered/N_not_started`同时报告；全局hard cap导致未启动项必须列出，不能称完整配对实验通过。未启动不是已测能力为0，亦不得删除后只呈现较小有利分母。任何提前中断使完整比较Pending/blocked。

金标为空、类型不合法或归一化后为空等数据异常必须在数据关卡明确登记并审阅，不从评估集合静默删除/替换；不能利用原F1的空/空=1制造正确答案。各任务保留互斥`end_reason`与独立错误flags，避免把error和unanswered重复相加后得到错误分母。

通信另报UTF-8 body bytes、封装/CRC/ACK bytes、UL/DL真实uses、重传/失败/排队/latency；模型usage与旧comm_words分别报。效率可另报`sum(F1_all)/(sum_radio_uses/1000)`与每任务均值成本；零通信分母记N/A，不制造无穷效率。收益主要看任务质量与实际资源前沿，不只看一个比值。

## 9. 未来最小基线与可迁移范围

[HYPOTHESIS/设计] base/protocol是两个提示与记忆机制族，不是只换传输策略。以下策略分别在**同一族**、同私有输入/模型/turn预算/帧/服务上比较；跨族成绩是系统差异，不能全归因于估值。

| 对照 | 明确定义 | 用途/限制 |
|---|---|---|
| 原生完整通信 | 固定commit、原瞬时内存交换 | identity与能力参照，不是无线成本匹配工作点 |
| Full-wire | 所有真实A2A消息均准入，仍付UL/DL/CPU/ARQ且可受损 | 任务—通信参照，非任务最优上界 |
| No-A2A | 全拒绝peer交付，保留自身推理、同turn上限及本地最终答复 | 检验信息依赖；不得因没有无线最终答案通道而强制0 |
| Native base/protocol | 原prompt/解析/板机制分别保留 | 强系统基线，板不得免费补齐丢失事实 |
| Periodic-opportunity | 按每sender自己的发言机会计数h_i，每k次准入；相同k/相位规则 | 避免按全局turn奇偶永远只传Alice；不是改变发言次序 |
| Random | 按公开固定随机键/概率准入，不使用答案或未来信道 | 同一校准规则/实际成本支持，非仅相同发送概率 |
| Length/Freshness | 发送端已知body长度、created/排队age做阈值/优先规则 | 立即新建且仅一消息时age可能恒0；记结构退化，不假称有receiver-state信息 |
| QA-Bits-RatePrice-v1 | 以片payload bits为吞吐代理，`Option.value=8l_f·P_s(r)`，`symbols=ceil(8(28+l_f)/r)`；同组率选项经BF/定价，拒绝/等待受同TTL控制 | 合法借用GOSC bits/rate/price结构；只优化字节goodput，不称QA真实效用，分片不各自重复领取“全消息任务奖励” |

最后一项是**新命名迁移基线**，不是直接运行`WireGOSC`（它拒绝LLM且只支持Search）。如果作为frame-level后端比较，应给其他消息准入策略同一后端；如果研究rate-price作用，单列该轴，不用不同粒度假称固定所有控制变量。参数单位需独立开发/校准集按共同资源上限选择，不能强制与ToM或其他代理用同一数值price；当前未做任何校准。

不能直接迁移：Search TeamModel/空间G0/G1、私有Lc/真实目标位置、搜索confirmed_pending/奖励、Genie定位结果，以及原Search下的性能数字。AoI思想只可使用合法本地timestamp，原“sum age of Obs”不是文本任务现成效用。若提出Q/R类型或请求匹配代理，须另命名、只用本地已收内容并单独审查，不自动引入新LLM judge或受监督估计器。

## 10. 待冻结项目与停止规则

本规格定义接口语义，不提供可立即运行授权。仍需：完整数据身份/分组划分、可用模型digest/许可/端点与context容量、依赖锁、帧/队列/TTL/链路/CPU/总预算参数，以及identity/权限/失败分母合同的HPC证据。未来最小能力诊断只能在这些关卡通过且用户另行批准后开展。

出现旁路事实、未计价共享板、无损不等价、失败样本被剔除、模型/预算不足、没有真实通信信息依赖，或只有门槛差异却声称内容排序，均应No-Go/Pending；不扩任务、增加模型复杂度或改变指标救结果。本轮到静态规格交付即停止。
