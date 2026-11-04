# MASBench Reasoning科研可行性审查

2026-11-03当前结论：[数据与最小无模型工程验收](../reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)完成，67合成合同通过。方向仍Conditional Go；数据为300行/200唯一规范化问题/100重复组，2条support/context异常，保守文章分组形成242条大组，不能直接随机按行切分。没有真实任务/模型调用，能力与通信依赖N0。先审阅分组及异常处置，再另批能力诊断；下文旧数据未取回/工程未实施等为历史快照。

2026-11-02 15:32（Asia/Shanghai）最新环境结论：用户授权修复并逐项批准清理后，三个模型文件与本项目2026-10-20 digest一致、所有blob SHA-256通过；独立Python环境的四项直接依赖及20项总包、uv pip check、导入、SDK GET模型清单和Ollama show metadata验收通过。原GOSC环境包元数据保持；没有调用chat/generate或加载模型。见[维护报告](../logs/masbench-environment-repair-2026-11-02/report.md)。此前模型缺失、配额失败及超时原件保留。基础环境阻断已解除；Reasoning数据、上下文配置/能力、无损与权限合同仍Pending，任务运行未获放行，路线Conditional Go不变。

2026-11-02 13:46（Asia/Shanghai）更新：[恢复连接后的只读证据](../logs/masbench-reasoning-hpc-2026-11-02/task_log.md)。HPC身份/HEAD确认；Python3.11.15、2核CPU/24GiB、可见L40 34304MiB。Ollama0.11.11在线，tags/ps为空、v1/models.data=null；三个已知标准manifest未找到；openai/httpx/requests/python-dotenv/pandas/tiktoken包元数据缺失。当前环境由“连接失败未核实”更新为“已核实但运行未就绪”，并非模型能力已验证。旧超时记录及§4历史快照保留；未安装、恢复或调用模型。数据/合同/能力关卡仍Pending，当前运行No-Go/Blocked。

2026-11-02交付复核：[新记录](../logs/masbench-reasoning-static-2026-11-02/task_log.md)。本轮HPC只读SSH两项查询均超时，沙箱外重试仍超时；当前模型/包/资源状态**Pending，未核实**。Windows同端口GET不可达。§4是10月30日历史快照，保留原件，不据此断言当前模型仍为空或已恢复。方向Conditional Go、实际运行No-Go/Blocked仍保持，原因是当前环境及数据、工程合同均未满足进入条件，而非已证明任务不适合。未运行任何新测试、任务或推理。

日期：2026-10-30。**结论：静态研究适配Conditional Go；当前实际运行No-Go/Blocked。** Reasoning提供值得检验的私有证据交换问题，但源码包含共享板、非严格协议及特殊评价分母；当前HPC无可确认的已注册模型且缺运行依赖，数据正文/分组划分尚未完成核验。本轮没有建立模型能力、通信增益、方法创新或可发表性。

## Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 在不免费共享历史和不泄露gold的条件下，公开Reasoning任务能否提供可识别的消息任务价值，并在真实无线/推理成本下研究？先解决传输与评价合同，再判断能力与信息依赖。
- **已核验前人工作**：[PAPER] MASBench，Qizhi Chu、Zekai Yu、Sijie Wen、Yang Liu、Chen Qian、Cheng Yang、Chuan Shi、Zhiyuan Liu，arXiv:2610.04672v1（2026-10-03；正式发表状态未另核验）。读Reasoning相关§4/D.1/E.1与C.3/C.4评价范围，非全篇所有任务复现。[论文](https://arxiv.org/html/2610.04672v1)。BANDMAS等先例边界沿用[路线审查](../reports/research_route_decision_2026-10-30.md)，不能宣称消息价值/packetization首次。
- **实际阅读源码**：[CODE] 固定MASBench commit`c0301a650db95958924bb080192c09fef39389a5`；读取Reasoning的6个功能模块及包入口、api_key_loader、README、指标后处理及根LICENSE/requirements；未阅读/实施其他任务代码。逐文件blob/长度/链接见[source_index.json](../logs/masbench-reasoning-static-2026-10-30/source_index.json)与[补充核对](../logs/masbench-reasoning-static-2026-10-30/source_index_supplement.json)。
- **本轮新增或修改**：三份`research/benchmarks/masbench_reasoning_*`文档及本轮日志/只读环境盘点/证据索引，更新research入口；未修改或集成GOSC/MASBench算法、任务、候选、数据、历史记录或冻结规格。
- **实际运行**：[RUN] 仅Git/文件阅读/哈希/文档检查、GitHub原文件读取、两次只读SSH元数据盘点、localhost Ollama GET。未调用chat/generate，未加载/注册/下载模型、安装依赖、跑benchmark/pytest/仿真/训练/统计，无付费API、HPC源码同步或Git提交。命令与返回保存在[任务日志目录](../logs/masbench-reasoning-static-2026-10-30/task_log.md)。
- **测试与结果**：本轮**未运行新测试或任务**。所有“identity/权限/CRC/模型能力”是待验合同；GOSC旧519通过不等于本适配通过。只读环境事实见§4；新任务效果N=0。
- **失败/负面证据**：数据头读取返回空content但有非空blob身份，网页读取cache miss，未假称数据本身为空；两次GitHub MCP临时错误重试后源码可读，原事实保留。HPC模型清单空、旧标准manifest不存在、依赖缺失；protocol可fallback全文、原mean F1排除None、全局板可形成旁路。G1和GP-ID科学No-Go不撤销。
- **与原 GOSC 的差异**：将来若实施是新任务/文本wire/时钟接口，非原Search精确复现；Channel/定价/BF思想可借用但须独立命名、重新验收，不能借用真实Lc/位置/任务奖励。
- **公平性与泄露检查**：loader持有gold/双方context不等于online可见；只允许各自context与实际收到消息。禁止用共享transcript/board补丢包，禁止把support模式当无额外标注的context主结果，禁止剔除无答案/超时后比较。
- **成本**：本轮无新增任务channel uses/模型tokens/推理计算；只读管理成本不作算法效率结论。未来预算只有公式和明确标记的情景，不是实测吞吐/已批准额度，见§5。
- **可否进入下一阶段**：文档交付Go；路线研究Conditional Go；当前模型能力诊断/正式实验No-Go/Blocked。工程实现亦须用户新指令及各关卡，未自动放行。
- **用户需要批准的下一步**：如继续，先确认数据核验、独立依赖环境与模型恢复/许可方案以及最小工程合同范围；之后另批有完整预算的能力诊断。本轮结束停止，不自动补环境或运行。

## 1. 科研适配性：有潜力，但不接受任务构造保证当作实测信息价值

[PAPER] 原文D.1说明从HotpotQA改写并分配证据，构造/筛选过程使用LLM辅助检查；这不是对任意模型“单agent必不能答对”的数学保证。E.1描述base/protocol及首答案停止；C.4另属framework-level口径，不能直接当原生脚本行为。[原文](https://arxiv.org/html/2610.04672v1#A4.SS1)

[CODE] 原生runner初始化两agent时不传gold；这使隔离适配在结构上可行。最小接口可以严格限制peer memory写入点，保留原prompt和任务目标。但公开问题可能被模型记住、双方context可能有重复/推理捷径，且第一个可解析答案不要求共识；需要未来Full/No-A2A对照验证实际依赖，不能先宣布有因果任务价值。

[HYPOTHESIS] 比Planner Search更合适之处是“消息可提供对方缺少的文字证据”，而非简单把任务变难。若当前可用模型在Full下也失败，测到的是能力不足；若No-A2A也同样好，可能没有通信识别空间。若Full很高而低通信仍能保质省成本，则依然有合法研究空间，不因天花板本身自动拒绝。

## 2. 必须显式处理的源码事实与差异

| 项目 | 固定源码事实 | 科研风险/规格处理 |
|---|---|---|
| 私有上下文 | `data_loader_v4_mas.py:69–150`分开构建；runner:252–270只传对应context | Sample.raw/answer/另一份context与日志不得进入agent、候选价值或共享工具 |
| 共享板 | `conversation.py:170–202`控制器累积R并附给listener | 本地可见事实重建，禁止全局板帮丢消息；zero-input逐字符合同待验 |
| 自身memory | `agents.py:179–187`保存full，listener在protocol只收visible+板 | 不能把自己的隐藏/前导文本丢掉来“省模型成本”却称原生等价 |
| protocol强度 | 活动prompt含shared board；MESSAGE缺失fallback全文；Q/R/A未完整验证 | protocol并非仅换几个tag；格式/事实失败另报，不偷偷换更严格parser/prompt |
| 首答案停止 | base/protocol均取第一个truthy parse结果，非最正确/双方一致答案 | No-A2A仍允许本地外部答题，避免人为零分；错误的首答案也停止，不用gold反馈延长 |
| F1 | 活动metrics删标点/冠词后按words多重集重合；不是旧注释中的regex tokenizer | 固定代码版本，新增EM另名，不能混作严格准确率或直接套其他Hotpot评分 |
| 未回答 | runner保存None，mean F1排除None | 传输实验主评价必须全已启动任务分母，失败计0，并列保留legacy |
| 后处理 | `script/analyze_first_answer_protocol.py:120–172`也剔None，且判断`ans is not None`不同于会话的truthy判断 | 不能假称跑此脚本会修正所有分母/空字符串差异；本轮未运行后处理 |
| 通信 | runner:26–69去A/boxed spans，words计数；板后缀/帧/ACK/重传未完整覆盖 | 原comm_words仅兼容字段，真实UTF-8/无线账本独立；答案若实际A2A传输也计bytes |
| API与超时 | agent未设显式timeout/retry/模型seed；api_key_loader默认base_url为云端API并可读.env | 将来须本地endpoint allowlist、无默认云端回退；显式冻结SDK重试/timeout，不从dataset seed推模型确定性 |
| API异常 | 未见逐sample推理异常捕获；异常可在保存本sample前中断 | 适配器登记失败与不可得usage；不能把上一个checkpoint当该任务已完成 |
| 采样/恢复 | 正num_samples为有放回随机抽样，-1依次全文件；resume跳sample_index不恢复采样RNG | 新诊断用事前唯一ID清单；同题重复不算独立N，恢复不能静默换题 |
| 输出覆盖 | 文件名实际只有model_key+style，未含mode/seed/预算；注释说含mode与代码不符 | 新run隔离且不覆盖原outputs，日志存gold但不让agent访问 |
| CLI语义 | max_rounds是总发言turn；CLI默认10，main函数默认8；seed CLI默认42而help有旧说明 | 所有参数显式冻结，不用help/README近似值代替真实入口参数 |

该表是活动代码审查，不是已经执行后的bug频率/任务损失测量；不将局部差异推断成原论文成绩无效。

## 3. 原始数据身份、许可、划分与泄漏

[CODE/官方资料] 对应commit中仅一个`Reasoning/reasoning.json`，Git blob SHA-1为`9cfc774f5828bb7b811612a16d0f7d209db627d7`，Git tree元数据大小**11,996,959bytes**。README声称300题、200 easy/100 hard；这是官方声明，本轮未对正文独立计数。代码可知期望字段包括question、answer、context.agent_a/b、supporting_facts.agent_a/b、id、level；缺字段默认空字符串/列表、部分非预期结构会跳过，不能据loader未报错认为所有记录合法。

数据头fetch返回空content（仍有该blob身份），GitHub网页cache miss，因此没有核完真实记录schema、唯一ID/重复问题、来源HotpotQA ID、上下文重叠、答案泄漏、分组和正文SHA-256。**不把元数据Git blob SHA-1冒称下载后的SHA-256，不把读取失败当作空数据集。** 未下载/集成整个数据集，亦未核验任何具体题目的能力。本轮没有新浏览到的实际题目ID可登记为开发样本；论文示例/公开暴露仍应纳入后续污染检查。

[CODE/许可文件声明] GOSC根LICENSE为MIT；MASBench代码根LICENSE为MIT，copyright2026 Qizhi Chu。MASBench根及Reasoning README明确将HotpotQA改编数据单独列为CC BY-SA4.0，不由代码MIT覆盖；引用原HotpotQA及修改说明等要求按其原声明保留。[固定Reasoning README](https://github.com/BUPT-GAMMA/MASBench/blob/c0301a650db95958924bb080192c09fef39389a5/Reasoning/README.md#data-source-and-license)、[固定LICENSE](https://github.com/BUPT-GAMMA/MASBench/blob/c0301a650db95958924bb080192c09fef39389a5/LICENSE)。本轮仅核查声明，不对再分发适配数据作超出原文的法律保证；实际模型许可仍须按未来可用权重版本另核。

[CODE] Reasoning目录/loader/runner没有实施研究用train/calibration/held-out split；easy/hard是难度分层，**不是训练/验证/评估划分**。paper的其他框架子集也不自动成为本项目的封存集。未来须在首次任务调用前固定development、独立calibration与held-out registry，按源问题/派生模板/共享文章证据族分组，防同题换措辞、同一原Hotpot问题、同样消息不同turn跨集合。不能将作者采样seed42理解为测试防泄漏。

公开数据的预训练污染无法仅靠本轮静态阅读排除；需要明确限制外推。support模式还依赖gold-selected supporting facts，不能把其成绩当作全文检索/证据选择已经解决。level可能含答案长度信息，online不给它；分层统计可在离线做。

## 4. 当前模型、环境与资源：本次只读实况

[RUN] 2026-10-30T10:13Z只读SSH：host n1、UID8301880、HPC项目HEAD014b85d/origin一致；Python3.11.15。证据：[environment_inventory.json](../logs/masbench-reasoning-static-2026-10-30/environment_inventory.json)、[原始stdout](../logs/masbench-reasoning-static-2026-10-30/hpc_inventory_stdout.json)。没有启动服务、调用推理或触发加载。

| 项目 | 本轮确认 | 不代表 |
|---|---|---|
| CPU/RAM | quota200000/100000，cpuset0–1；25,769,803,776bytes（24GiB） | 不可用宿主核数开workers |
| GPU | NVIDIA L40，驱动545.29.06，可见34304MiB；当时used5940MiB | 不代表这些显存由本项目占用、专用/空闲算力或实际吞吐 |
| Python包 | numpy2.4.6、pytest9.1.1；openai/httpx/requests/python-dotenv/pandas/tiktoken元数据均未找到 | 原生Reasoning不能据此称已可运行；无需整装所有其他任务依赖 |
| 原requirements | 推荐Python3.10；openai1.101.0/httpx0.28.1等，numpy2.2.6 | 不应在原GOSC venv原地换NumPy；未来需独立锁环境/版本并另批安装 |
| HPC服务 | 127.0.0.1:11434 `/api/version`响应0.11.11；`/api/tags`models=[]，`/api/ps`models=[]，`/v1/models`data=null | 服务在线不等于模型可调用、OpenAI chat参数兼容或上下文足够 |
| 历史三模型路径 | 10:16Z检查原models/ollama-gosc根存在，但qwen2.5:3b、llama3.2:3b、qwen2.5:7b标准manifest均不存在 | 不推断权重一定已删除，也未搜索HPC其他位置/服务；未自动恢复/注册 |
| Windows loopback | 同端口version/tags GET均URLError | 只说明该端口未核验可用，不断言整台电脑无其他模型 |
| 文件系统free | statvfs见38,685,304,565,760bytes | 共享文件系统空闲不等于账户/项目配额；可写quota仍Pending |

[RUN] 模型路径证据：[model_storage_stdout.json](../logs/masbench-reasoning-static-2026-10-30/model_storage_stdout.json)。与2026-10-20的三模型验收是**不同时间事实**，旧成功记录不改写。本次没有任务调用，旧1024context/短JSON标签验收即使仍有效，也不能证明全文Reasoning上下文/多轮能力。未来模型digest、权重/许可证、context上限、截断行为、request/usage/timeout兼容性和实际能力全部Pending。

## 5. 运行与存储负担：仅静态预算公式

[CODE/推导] 每episode最多T次模型生成（两agent交替，总计T而非2T）；K个唯一问题、F个提示族、S个传输策略、R个独立重复的最宽成功调用数为`K·F·S·R·T`。如允许最多A_call次请求尝试，须再乘A_call，并把隐藏SDK重试计入；未来最小诊断建议A_call=1，radio ARQ不额外生成LLM输出。

设每次输出cap为M（需endpoint确认），则输出token请求上界为calls·M；**不是UTF-8字节上界**。另设可审计U_max bytes，超出时显式失败，不截断后继续声称native identity。实际prompt长度分布、吞吐/费用均未测，不能从12MB数据大小或模型参数数编造运行秒数。

base每次重发system/private context与历史，累计模型输入可达`O(T·C + T²·U)`；protocol重复附累计板且将多个enriched消息留在memory，最坏可有额外`O(T³·F_R)`量级的重复事实输入（F_R为每turn新增R规模）。这只是源码结构上界，不是实际token测量；不可用“MESSAGE变短”直接宣称推理变便宜。重建式日志可保存system一次+增量/history/request哈希，仍须能还原每次完整调用。

[HYPOTHESIS/容量情景，非冻结计划] 如果将来使用K=4（开发级2 easy/2 hard）、F=2、S=2（Full/No-A2A）、R=1、T=6、M=512，最多16episodes/96次成功调用/49,152输出tokens；这是预算算式，**不是功效N、已选题目或足够能力证据**。完整题库300题的同配置则有1,200episodes/7,200调用/3,686,400输出token请求上界，当前不得启动。实际输入/时间/日志cap和模型能力未核实前，连4题方案都不能执行。

时间只能作条件预算：若未来单次请求等待cap为60s，96次请求的客户端等待上界就有5,760s，尚未包含传输/队列/序列化/审计/回传；这不是预测实际耗时，也不保证客户端超时会终止服务端生成。没有当前模型/吞吐证据，不能据此申请一个看似精确的总运行秒数。

存储也必须独立预算。例如假设每次完整request最多256KiB、生成文本最多8KiB（两个独立byte上限，**不是512tokens的字节换算**），96次完整请求/响应快照就需至多24.75MiB；加原数据约12MB、两端记录/配置/cache/审计和帧trace后会更大。按8KiB body、16byte分片、每hop至多3次尝试推导，最宽有`96×512×12=589,824`个DATA/ACK帧生命周期记录机会；若每帧一条1KiB记录，仅该项就达576MiB，不含更细状态事件。该保守情景包含No-A2A也全发的宽上界，不是实际消息量；它说明不能直接沿用旧Shadow的32MiB cap。未来宜用可重建增量/压缩日志并先确认每条事件大小和配额，不能为了省盘删失败或只存汇总。

[HYPOTHESIS/无线算式] 规格候选16byte满片+28byte封装，理想无重试每片两跳DATA+两个ACK共`44+28+44+28=144bytes`，16byte body相当于9倍空口bytes（尚未按rate变成uses）；失败/重试/尾片会另增，不能把它叫最优通信协议。普通长文本在W100下需要许多slot，若费用/时限使任务信息来不及使用，应No-Go或另审协议，不事后省略DL/ACK/CPU或放宽W救结果。

## 6. 创新空间、反证与审稿风险

| 审稿意见 | 当前可回答程度 | 必须避免 |
|---|---|---|
| “只是给benchmark套信道” | 只能提出严格可观测/计价/失败边界，尚非方法贡献 | 用系统适配工作量冒充已证实创新 |
| “原protocol已有记忆机制，你改了它” | 本地板重建有明确zero-input等价条件，未验收 | 暗删板/改prompt/更严parser后称原生完全一致 |
| “无通信低分是被禁止提交答案” | 规格保留本地外部最终输出 | 把ACK/peer共识新增为无通信必失败条件 |
| “漏计负结果/低估成本” | 已定义全已启动分母、legacy并列、真实wire与模型输入收费 | 剔None、沿用words作bits、隐藏板/重传/CPU/SDK重试 |
| “LLM小模型不会做题” | 当前Pending且实际环境blocked | 直接用更大/付费模型救场、不计推理费用或按有利题挑样本 |
| “又是单候选门槛，不能证明内容排序” | v1明确单在途整消息的识别范围 | 机制未分离时训练复杂估计器或复活G1 |
| “与BANDMAS等重叠” | 已知价值/packetization/资源调度非空白 | 未完成针对最终机制查重就宣称首次/SOTA |
| “公开数据污染/分组泄漏” | 目前不能排除，且正文/分组仍未核 | 随机按消息或题面变体切train/test、用level/参考答案作为在线特征 |

**建议**：[HYPOTHESIS] 先完成数据身份/环境恢复方案与无模型工程合同规格，再考虑极小Full/No-A2A能力诊断；不先写新估值器。若能力或通信依赖不存在、旁路无法堵住、成本远超支持、模型状态无法复现，停止该方向的任务效果推进，保留边界结论。本轮三文档完成后停止，等待新研究决策。
