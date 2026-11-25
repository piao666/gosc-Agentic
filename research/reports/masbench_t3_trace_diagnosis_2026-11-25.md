# Research Task Report — T3-R A：原始轨迹诊断

2026-11-25，Asia/Shanghai。**A 工程/证据 Go；原 T3 科学 No-Go 保持。** 本轮重建已有记录，未运行新的任务 episode。四家族用 F01–F04 表示，避免公开复制私有题目、完整视图或回答。

## 1. 问题、身份与核验范围

- **Research Question / Hypothesis**：[HYPOTHESIS] 早答、协议活性、证据覆盖和整合失败能否解释已有 T3 轨迹？本报告只确定观测与代码行为，不指定唯一因果主因。
- **已核验前人工作**：[CODE] 固定 MASBench `c0301a650db95958924bb080192c09fef39389a5` 的本地 reference，重点为 `Reasoning/src/prompts.py` 与 `conversation.py`。本轮未新增论文全文阅读，不把代码观察标成 [PAPER] 作者结论。
- **执行身份**：[RUN] 本地 HEAD `bda3027e17883c1c41dd4ed6d1dd431f0a0657ba`；HPC 及历史 T3 为 `b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0` + 实际 dirty snapshot。T3 snapshot `20261125T034132Z`；本轮登记复用远端已验证的 `20261125T040145Z`，没有源码上行覆盖。关键九份源文件含固定 Prompt 与 T3 snapshot 哈希一致，详见 verification_summary 的 `execution_source_bindings`。
- **权限**：完整阅读 AGENTS、研究说明书及 T3-R 任务书；11-17 的六关路线属于历史分阶段计划，当前任务书只授权 A/B/条件 C/D。本轮未执行其后续 T4–T6，也不采用旧 6000 秒提案为运行授权。

证据附件：[完整文件索引](../logs/masbench-t3r-2026-11-25/evidence_inventory.json)、[逐轮索引](../logs/masbench-t3r-2026-11-25/episode_trace_index.json)、[交叉核验](../logs/masbench-t3r-2026-11-25/verification_summary.json)、[命令与成本](../logs/masbench-t3r-2026-11-25/task_log.md)。原始根为 `/hdd/u202520081000097/gosc-t3-runs/hpc-masbench-t3-live-20261125`；下文原始相对路径均在该根内。

## 2. A0：684 文件完整性与类型

[RUN] `hpc-masbench-t3r-inventory-20261125`：期望/实见/实际读入均 **684**；字节通过 **684**，SHA 通过 **684**；合计 **16,983,131 bytes**。缺失、额外、不可读、非普通文件、路径穿越、软链接、内容类型解析异常均为 0。逐条验证 JSON/JSONL 或 UTF-8 文本；预分配 JSONL 仅在解析副本中去掉尾部 NUL，没有截短原件。文件以 `O_NOATIME|O_NOFOLLOW` 读取，读取前后 atime/mtime/ctime/size 相等；目录枚举也使用 noatime FD。

[RUN] 本轮重新核对主账本 **835** 行、控制链 **2733** 行的序号、前驱和规范化 SHA；全部 bytes 事件重新绑定文件字节与哈希。18 个卸载栅栏逐一绑定控制事件、旧 runner 的启动标识退出、空驻留及账本 tip。51 次请求的精确输入计数、渲染文本、实际 16384 窗口和固定模型 digest 一致。用量复核为 **131,147 输入 / 5,286 输出 tokens**（含两次合成），与旧摘要一致；16 条评分、请求数、wire 成本和 12 条 receiver-next-request 证据与旧审计无差异。

核验的是已有内容与登记之间的一致性，不是对服务端隐藏推理或通用 tokenizer 等价的证明。684 文件均被程序读取；人工语义审阅集中于 49 条任务输出的 Q/R/A、关键正文摘录及四题的支持证据，未把完整私有视图复制到报告。受控读稿附件只保留在新 HPC 审计目录，不回传；684 原文也未镜像进 Git。

## 3. A1：真实上下文、动作和消息生命周期

[CODE] 执行时 `application.py:56–124`：system 由当前 Agent 的 question 与其 `context.agent_a/b` 生成；不注入 gold、supporting_facts 或对方 context。请求随后按记忆插入：以自身名字开头的消息为 assistant，其他为 user。自身全文先追加自身 memory；base 发送完整正文，protocol 从 `Name: MESSAGE` 标记起保留至全文末尾，找不到标记则全文回退。它不解析 Q 的语义、不限制 bullet 数，也不只传标签内容。

[RUN] 独立工具用 AST 提取固定模板字面量，未执行第三方 Prompt 文件；重新构造两方私有视图和 system，核对 16 份初始请求计划哈希。49 次实际 system 与合法本方信息完全相等；随后每个 memory 元素、角色、顺序及最终 memory 均从原始 response 和已交付 body 逐条恢复并匹配原件。No-A2A 没有对方私有视图或 transcript 旁路；本轮 gold 只在离线评分及覆盖审查中读取。

[CODE] `client.py:323–390` 的顺序为：请求 → 生成 → 本地后处理 → UTF-8 消息 → admission → wire transfer → listener.receive/板更新 → parse_answer → 非空答案则终止。**先传输，再判终答**，所以最终答案消息本身仍可能收费及送达，但没有后续模型消费。

[CODE] `wire.py:84–252`：整消息一次 outstanding，经16-byte片段、24-byte header、4-byte CRC、UL_DATA/UL_ACK/DL_DATA/DL_ACK串行服务。实际是确定性合同传输，不是原 GOSC 随机无线信道的新效果实验。逐帧索引和 `raw_hex` 的 CRC、长度、uses、分片重组重新核对。No-A2A admission 拒绝；Full 投递后才更新接收方本地状态。

[RUN] 可审计偏序为 request 预留/文件账本序号 → 响应 → message created/enqueued → UL/DL帧slot → receiver_receive/visible → 下一 provider request。控制链有 monotonic 时间，wire 是合成 slot；不把它们拼成虚假的统一物理时钟。索引保留各自的时间/序号和 SHA。

## 4. 16 episode 摘要与全部逐轮动作

[RUN] 下表 F1 为原合同的 all-started 分母，未答为0；EM 仅 F03 的两个 base episode 为1，其余为0。N=4 个问题家族，不是16个独立问题。turn 从0开始，偶数 Alice、奇数 Bob；`E` 表示真实 raw content 长度0；`N` 为非终答自然语言或非标准标签。

| Episode | 请求数/动作（按序） | 结束 | F1 | wire bytes | channel uses | L1收信数 |
|---|---|---|---:|---:|---:|---:|
| 01-base-Full | 1：A | answer | .1142857143 | 12814 | 25628 | 0 |
| 01-base-No-A2A | 1：A | answer | .1142857143 | 0 | 0 | 0 |
| 01-protocol-Full | 3：Q2 → R1/Q1 → R2/A1 | answer | .5263157895 | 7736 | 15472 | 2 |
| 01-protocol-No-A2A | 6：Q2 → Q2 → E → E → N → N | turn_limit | 0 | 0 | 0 | 0 |
| 02-base-Full | 1：A | answer | .0625 | 10500 | 21000 | 0 |
| 02-base-No-A2A | 1：A | answer | .0625 | 0 | 0 | 0 |
| 02-protocol-Full | 3：Q1 → R1/Q1 → R1/A1 | answer | .2191780822 | 15378 | 30756 | 2 |
| 02-protocol-No-A2A | 6：Q1 → R1/Q1 → E → E → N → Q1 | turn_limit | 0 | 0 | 0 | 0 |
| 03-base-Full | 1：A | answer | 1 | 16834 | 33668 | 0 |
| 03-base-No-A2A | 1：A | answer | 1 | 0 | 0 | 0 |
| 03-protocol-Full | 6：Q1 → R2/Q1 → R1/Q1 → R1/Q1 → R1/Q1 → R4/A1 | answer | 0 | 21086 | 42172 | 5 |
| 03-protocol-No-A2A | 6：Q1 → Q2 → E → E → R2 → N | turn_limit | 0 | 0 | 0 | 0 |
| 04-base-Full | 2：N → A | answer | .0701754386 | 21412 | 42824 | 1 |
| 04-base-No-A2A | 2：N → A | answer | .0701754386 | 0 | 0 | 0 |
| 04-protocol-Full | 3：Q2 → R1/Q1 → R1/A1 | answer | .3661971831 | 11480 | 22960 | 2 |
| 04-protocol-No-A2A | 6：Q2 → R1/Q3 → E → E → R2 → N | turn_limit | 0 | 0 | 0 | 0 |

每一行的原始 application-result 路径和 SHA、每一 turn 的 provider/client 路径、ledger_seq、request/response/answer/payload SHA、输入分段角色、Q/R/A数量与SHA、board来源、帧事件索引、tokens及Python CPU计时均在逐轮索引。无字段推填0；未观测的模型独占 CPU/GPU、物理无线耗时及取消因果成本不能由这些值推出。

## 5. A2：base 早答与零差配对

[CODE] parser 大小写敏感，跨行匹配精确 `<A>…</A>`，逆序选择最后一个非占位候选；去掉一个尾随句点。仅无可用 A 时才回退到首个 `\\boxed{…}`。它不核验答案资格、证据充分性或标签是否在最终行；多标签可覆盖早先候选，异形 `〈R〉`/缺尖括号不被当成标准标签。

[RUN] F01/F02/F03 的 Full 与 No-A2A 在 t0 的 raw response 已各有1个真实 A，finish_reason=stop，独立解析与原结果一致；未见这六条的 parser 误检。原始 client 路径分别为 `000052-40`/`000073-56`、`000255-204`/`000234-188`、`000416-336`/`000437-352`（后缀均 `-client.json`）；完整 SHA 见索引。F01仅答比较主体，漏捕食者；F02比较方向错误且遗漏所问研究要点；F03主体名与gold一致。

[CODE] 原生 conversation 也会接到非空 parse_answer 就停止，因此应用接受早答与原控制语义一致。**但不能说 Prompt 允许早答**：生效 base 模板 `prompts.py:25–50` 明确要求先协作、几轮交换后再答；被注释掉的宽松模板不生效。实际是自然语言规则被输出违反，而控制器没有执行阶段资格门。三种解释的判定：原生控制允许（支持）；Prompt约束没有被可靠遵循/强制（支持，但不足以区分模型与控制责任）；parser凭空产生答案/错误投递导致意外终止（受测链未支持）。

[RUN] F01–F03 两条件不仅 F1 相等，完整 raw response 与 final answer 字符串也逐一相等。F04的 t0相等，t1正文不同，Full明确致谢并复述收到的分析，final answer 字符串仍相等；不是“两段不同最终答案碰巧同F1”。全部4对初始请求、私有视图、模型与温度匹配，不表示已控制服务推理的所有随机性。

[RUN] base Full 共5条消息，全部交付；仅F04 t0进入下一请求。F01/F02/F03 t0及F04 t1共 **4/5** 标记 delivered_but_not_consumed，占 **52,216/61,560 wire bytes**（相应104,432 channel uses）。这能确定“未进入本episode任何随后模型请求”，不能声称它们的文字天然无价值或无限未来都不会被使用。任务在当次答案后已经结束。

## 6. A3：protocol 交互、知识板与未答

[CODE] `LocalAgent.add_facts/receive` 只抓标准 R 字符串，strip后精确去重、追加；无语义核验、更新覆盖、过期或纠错机制。发送者也把自身 R 放入本地 facts；接收者只在真实交付时添加R，并把本地累计 facts 重附在收到消息后面。两端独立维护，非免费中央共享板；No-A2A 的自身 R 可能进入 facts，但没有 receive 就不会自动把累计板附入请求。板中的来源是模型生成的R，不是数据集 supporting_facts或gold。

[RUN] 各Full交付后的 body与附加板完整进入下一接收方请求：F01两次、F02两次、F03五次、F04两次；base另一次，共12次。标准R的新增/重复、顺序及源turn/R_index完全重建，最终memory匹配。无证据显示有效正文被传输层截断；所有51响应stop且用量已知。F03的输出自己复写板，导致全文/历史中重复板文本；精确去重不能去掉同义改写，也不纠正错误事实。

| 家族 | Q/R与后续内容的受控审阅 | 可观察利用与边界 |
|---|---|---|
| F01 | t0问亮度与捕食者，t1给亮度又问捕食者，t2补捕食者并给较完整答案 | L2：t2沿用已收的比较事实并结合本方捕食者线索；但本方本来已具这些事实，无法认定消息必要；F1=.5263/EM0也含答案措辞与长gold差别 |
| F02 | t1明确传来对方三名成就者及领域，t2仍选本方机构、重复研究方向 | 到L1可靠；整合明显不足的局部证据。结论不随人数事实修正，不能从缺少显式引用证明完全没利用 |
| F03 | 多轮重复物种数/制图事实，询问加分，t4产生“没有首次接触加分的具体记载”式R，板保留；终答人物名字发生变形 | L2：终答复述累计R；其中否定加分与Alice合法支持证据冲突，真实首次接触事实未有效传出。答案没有完成计分整合，名字变形又被精确评分惩罚；不是parser把正确名字改错 |
| F04 | t1给先前测试的比较描述并继续问正式评估；t2补本方追溯评估，终答比较方向对但未写完整资源项 | L1成立，L2至多部分：对已收描述有衔接，但关键比较可由本地部分信息猜出；遗漏资源及完整时序使EM0 |

[RUN] No-A2A 的四个episode均在t2/t3出现 **8次 raw content为空**，每次finish_reason=stop，不是超时或输出长度截断；后处理只添角色前缀，不产生A。t4/t5恢复部分自然语言/事实，但都没有标准终答。F01 t4使用异形尖括号R，F02 t4出现不完整R标记，原parser不会把它们变为A。未答主分母保留24请求/4episode，不能改用legacy非None均值。

[CODE]+[RUN] No-A2A第二次轮到各自时，请求只有system+自己的assistant历史，没有peer user消息，也没有新的公共轮次提示/最终回答指令。Prompt强调必须结合伙伴、protocol首个消息必须Q，控制器却只循环到max_turns，没有最后一轮本地证据终答阶段。**代码并未禁止No-A2A答A**，但这不保证公平的实际答题机会。[HYPOTHESIS] assistant-only历史/角色模板、等待伙伴指令与信息缺失可能共同影响空输出；没有对照干预，不能确定空输出的服务/模型根因。

[RUN] protocol Full有效回答4/4、turn_limit0/4；No-A2A有效回答0/4、turn_limit4/4。三组正差=.5263157895/.2191780822/.3661971831，全部是已回答对未回答；F03是错误回答对未回答且零差。形式响应差异与信息整合无法从此比较中单独分解，不能给“多少增益因果来自活性”的百分比。

## 7. A4：证据分层、成本与未核项

- [RUN] L0：Full base5条、protocol15条完整传输/交付；No-A2A零交付。protocol4条终答消息也没有下一请求，涉及23,876/55,680 wire bytes。
- [RUN] L1：12条逐字消息+局部板进入真实下一请求，有request SHA及frame/ledger位置。
- [RUN] L2：F04 base明确引用伙伴；protocol F01有事实衔接、F03复述板（含错误），F02/F04存在部分/不足证据。L2可体现使用错误信息，也不等于正确整合。
- [RUN] L3：八组配对中base四组零差；protocol三组正差、一组零差，仅为开发观测。
- [HYPOTHESIS] L4：本轮无内容替换/等成本受控干预，**不可识别**，不能宣称因果内容价值。

[RUN] 历史UL/DL uses：base各61,560，protocol各55,680，总234,480；无重传收益/随机无线外推主张。task tokens **123,889/5,282**，加合成后131,147/5,286。索引逐episode保留应用和wire的实测Python process_ns，二者可能嵌套，不能相加冒充独立成本；wire logical CPU slots为合成合同。模型独占CPU、逐题GPU、端到端同步成本匹配比较均未建立。

## 8. 本轮新增、运行、失败与关卡

新增独立审计工具、三份JSON索引、任务日志及本报告；未改应用、Prompt、gold、原评分、历史结果、GOSC核心或用户任务文件。实际四个HPC离线登记均exit0，命令和资源见task_log；没有运行pytest、fresh simulation、模型调用、训练或新实验。管理探测曾遇profile失效、SSH引号、旧Git/cgroup选项及Windows命令长度错误，均保留说明，没有失败任务被删除。

**A Go仅在上述已存支持域成立。** 仍不能识别隐含理解、模型先验、空输出根因、通信内容的稳定因果贡献及净收益。下一步在本次授权内完成B非互斥归因；任何新能力实验另批。
