# T3-R-v2 合同与验收矩阵 v1（待审、未执行）

2026-11-25，Asia/Shanghai。配套[字面规格](masbench_t3r_v2_fair_final_spec_v1.md)、[D1/预算审查](../reports/masbench_t3r_v2_d1_budget_review_2026-11-25.md)、[综合决定](../reports/masbench_t3r_v2_preimplementation_decision_2026-11-25.md)。**矩阵是验收设计，不是测试通过记录。全部新版动态合同未运行。** 静态查见旧机制不等于新版合同通过。

## 1. 可追溯源码与证据层级

[CODE] 以下行范围均为当前 `f91d01070740703dc1ee845510569c0b31e66c51` 文件的1基行号。历史T3使用b05ea73加20261125T034132Z快照；九个关键文件逐项LF SHA与当前一致见[source_inventory](../logs/masbench-t3r-v2-review-2026-11-25/source_inventory.json)。其他当前辅助文件的阅读不自动证明历史字节相同。新规格行为没有实现函数，不伪造新函数名/通过记录。

| 现行文件/函数/行范围 | 静态事实 | 新合同差距 |
|---|---|---|
| `extensions/masbench_reasoning/application.py:17–38`，parse_answer/peer_payload | 宽松A/boxed与MESSAGE回退全文 | 新版需全串/分阶段语法、禁止fallback |
| 同上 `56–73`，private_view | 仅选择己方context格式化为information及公共question | 保留此信息边界，不把完整record给在线Agent |
| 同上 `77–124`，LocalAgent.request/add_facts/generate_fixed/receive | role由内容前缀推导，R累计板精确字符串去重 | 新版显式role、原始本地历史、无累计板；不是现有支持 |
| `extensions/masbench_reasoning/client.py:41–68,187–298`，ClientConfig/ControlledClient.generate | 完整请求冻结、计数/窗口/身份/usage及长度检查；旧默认60s | 可复用安全思想，必须明确180s和新绑定；不表示直接可跑 |
| 同上 `323–383`，run_controlled | 交流后解析A立即break；失败break | 不具备固定六slot/独立final，需要独立版本化应用入口 |
| `extensions/masbench_reasoning/evaluation.py:7–17,30–43,46–85`，normalize/f1/legacy_summary/summarize | 原词袋、排None的legacy及started计零的T3统计分开 | 新两方评分/配对NA/失效分母需独立实现，不改旧统计 |
| `extensions/masbench_reasoning/registry.py:19–63,66–153`，graph/build_registry | 严格文章关联、家族去重、整分量开发预留 | 不重新选择/更新曝光字段来掩盖旧四题 |
| `extensions/masbench_reasoning/wire.py:18–57,61–81,84–252`，Frame/ContractConfig/ContractTransport | 真帧、CRC/ACK、UL/DL/uses、重传/TTL等；默认确定性合同 | 仅前四turn合法MESSAGE可入队；无final、无免费板/控制事实 |
| `extensions/masbench_reasoning/execution_safety.py:50–205`，Ledger | 持久journal、reserve/finish、未知用量及恢复约束 | 新分区/slots/计数和never-refund须逐合同验证 |
| `extensions/masbench_reasoning/live_driver.py:75–128,263–337,539–597`，require_authorization/LiveLedger/LiveDriver.__init__ | 旧授权、T3计划18项/98calls/420metadata硬绑定 | 不可将旧授权路径/数量换名后开跑；需独立审批schema与新快照 |
| 同上 `350–362,615–638,710–742,744–895`，runtime_files/http/attest/generate | service/模板/计数绑定，debug每epoch前额外GET，身份GET | 50次准备及完整管理账本，不能只数V1POST |
| 同上 `639–708`，recover | 1前置ps+最多6轮ps，一次unload，旧PID/新runner检查、receipt | 新7E cleanup_GET与失败不重开epoch，不能误记6E |
| 同上 `897–1050`，run_episode/_guard_application | 原应用沙箱与IPC、文件证据 | 不提供新slot/final隔离保证，新六slot最大字节需验证 |
| `experiments_ext/masbench_t1b_live.py:41–111`，process_rss/Monitor | 排除服务子树避免双计，0.5s资源采样 | GPU/RSS采样不能宣称硬隔离/绝对峰值 |
| `experiments_ext/masbench_t2_live.py:39–106`，service/assert_idle/stop_idle/start_checked | 服务身份、空闲核查和自有实例生命周期 | 新有界准备/恢复须接入所有计数、lease和预算 |
| `experiments_ext/masbench_t3_live.py:24–69,79–147,150–179,182–276`，CAPS/profile/limits/run_synthetic/main | 旧16384服务切换/1024回滚、旧固定计划和资源 | 不能直接运行旧launcher承载新版，无新授权 |
| `scripts/hpc_ollama.py:25–89`，api/settings/ready/start | readiness在Driver外，有首次GET及60s循环；固定单模型环境 | 生命周期GET需新持久计数/61cap，禁自动重启和生成warmup |
| `research/logs/masbench-adapter-contract-2026-11-03/reference/Reasoning/src/conversation.py:101–215` | 原团队单答案、先A停止与protocol板 | 与新双本地final不是同一终点 |

[RUN/既有] [T3-R审计验收矩阵](../logs/masbench-t3r-2026-11-25/acceptance_matrix.md)和[索引](../logs/masbench-t3r-2026-11-25/README.md)绑定684原件、51请求、18栅栏及旧轨迹；[T1](../reports/masbench_t1_validation_archive_2026-11-19.md)/[T2](../reports/masbench_t2_context_acceptance_2026-11-25.md)只证明各自所测工程支持域。下面没有借用这些通过记录冒充新版结果。

## 2. 未来无模型验收设计

“预期”全部为[HYPOTHESIS/规范]。使用固定合成字符串/伪后端；不得读四题gold或封存正文，不发任何模型HTTP。若未来获批执行，仍须HPC登记、独立输出目录、独立审计；本轮只写矩阵。

| ID | 输入/故障 | 必须观察的预期/反证 | 当前状态 |
|---|---|---|---|
| C01 | 两条件完整6slot | A/B/A/B/A/B；四exchange+双final；无早停/第7请求 | Pending，未实现/未运行 |
| C02 | 同turn公共时钟 | 两条件字节相同，只含固定五字段；无条件/状态/事实 | Pending |
| C03 | No全程无peer消息 | t4/t5仍派发，不等待peer、不伪造消息 | Pending |
| C04 | t0出现正确形状的A | invalid_exchange、计slot、无线0、继续t1；不计final | Pending |
| C05 | exchange Q/R全串合法与尾随散文 | 前者可发，后者整条拒绝；不salvage、不全文fallback | Pending |
| C06 | 空/白响应、错名字、小写标签、boxed、空Q/R | 明确异常类别、消耗slot、无自动修复生成 | Pending |
| C07 | 重复R、相互矛盾R | 原文与重复次数保留，wire/tokens不免费去重，无truth oracle | Pending |
| C08 | 同一合法候选Full/No | Full才admit，No候选及blocked原因留账，No帧0 | Pending |
| C09 | t3成功/丢失 | 仅成功进入Alice t4；每接收的payload/source/turn hash可追 | Pending |
| C10 | t4含特殊哨兵答案 | Bob t5完整请求、mutable state、peer日志无该哨兵；final帧0 | Pending |
| C11 | 私有证据/控制器哨兵 | 己方可见、peer未送达前不可见；gold/supporting/全record在线不可达 | Pending |
| C12 | reference/控制器故意注入外部状态 | 输入schema/域隔离拒绝；无隐藏共享board | Pending |
| C13 | 合法A、U、E无效引用、多A、A/U并存、空/占位A | 精确分开valid_format/valid_answer/unanswered，非法全零 | Pending |
| C14 | 规格V01–V05 | 手工有理数预期一致；失败留分母，重复词F1正确 | Pending，未执行示例 |
| C15 | 原四题成绩/IDs不作为输入 | scorer只离线；新Prompt模板与向量无四题答案/题号特化 | 静态文档可查；动态Pending |
| C16 | 两答案不同、一个未答 | 字符串不一致、未答及语义冲突分开；joint00/01/10/11准确 | Pending |
| C17 | 启动一条件后故障、另一条件未启动 | started失败零，不启动者单列，pair主结果NA；不得剔除家族称过门 | Pending |
| C18 | 输入15872/15873+512 | 前者允许边界、后者HTTP前拒绝；完整render计数，绝不截断 | Pending |
| C19 | 角色/模板/窗口/模型digest/runner漂移 | 派发前拒绝，持久栅栏；不切模型/自动恢复生成 | Pending |
| C20 | unknown usage、length、HTTP error/超时/崩溃 | 预留不退，整轮停发，所有剩余slot显式not_dispatched | Pending |
| C21 | 各生成/metadata cap恰好耗尽及超1 | 超界在尝试前拒绝；失败尝试也扣计数，子计数对总468 | Pending |
| C22 | 首debug每epoch、准备失败、生命周期ready多次失败 | 额外ps正确计，readiness≤61/start、总生命周期≤128 | Pending |
| C23 | 每epoch6次清理poll仍未确认 | 1前置+6poll=7GET；不第8GET/第2unload；保留lease/锁 | Pending |
| C24 | 无旧runner绑定/新runner/外来service | 不强行卸载外来实例，不伪造成功，不自动rollback覆盖 | Pending |
| C25 | SIGTERM/SIGKILL/主控意外退出 | 自有worker退出证据、锁持久；重启程序不重放旧请求 | Pending |
| C26 | 时间各阶段耗尽 | 预留清理/回滚/审计/回传；总19100s，禁止时间借用开额外请求 | Pending |
| C27 | driver/service同树、RSS/GPU突增 | 无树双计；超过观测阈值停发；不谎称采样硬上界 | Pending |
| C28 | SSD/HDD/日志/IPC/HTTP临界或写失败 | 写前cap，失败证据空间保留，原结果不碰、不丢失败前缀 | Pending |
| C29 | wire分片/CRC/ACK/重传/TTL失败 | 只交付成功payload可见；UL/DL/header/ACK/失败成本全计 | 旧合同存在；新版入口Pending |
| C30 | 新registry或数据body路径误传 | 固定registrySHA拒绝漂移，不选择/解封新题，不拆D1 | Pending |
| C31 | 首模型预检失败 | 立即停止，无任务请求、无第二次补预检、无借用任务额度 | Pending |
| C32 | 审计或回传缺件/错SHA | execution与sync状态分列；原件保留，不能称整轮验收Go | Pending |

## 3. 通信合同与控制边界

[CODE] wire默认合同为rate4、budget100、ttl/deadline各100000、attempts3、rto6、cpu_slots1、max_body_bytes65536；Frame每片payload≤16B，header24B+CRC4B，ACK同样计帧。新版应用文本上界4096B不修改wire默认上界。未来候选固定 `faults={}`、`link_contract=None`，只作确定性服务可见性合同，不引入GOSCProbabilityContract/随机SNR来冒充真实无线试验；失败注入仅无模型合同另列。

双方每episode都可生成最多四个exchange候选，Full最多4条合法消息实际入队，No0。候选有效率、本地生成tokens与真实RF发送分别记录；final生成有计算成本但**radio payload=0**。公共时钟是双方预置本地表，无任务事实且输入tokens/CPU计价；若实现需要逐轮无线控制消息，本候选成本假设失效，必须回到审阅而不是填零。

No-A2A不是等实际wire成本的baseline：它是删去peer内容/传输的消融，总预算上限相同，但Full会产生额外通信和输入计算。只可解释此应用下端到端差，不能由F1或每k字节比值证明无线净收益。真实rate/噪声/成本匹配前沿均未运行。

## 4. 停止门审查：保留原候选，不擅自替换

旧C原样语义记录：完整4家族配对；Full至少2个不同家族双方final均EM1；家族平均Delta_F1≥0.10；至少2家族正差且两条件双方final有效，并有L1及可追溯L2。四题是能力筛查，不是显著性检验。**全部仍是未批准候选**。

| 门 | 一致性/风险 | 审查建议（未批准） |
|---|---|---|
| 完整4家族配对 | 与家族单位一致；基础设施缺对不能按剩余几对过门 | 保留完整要求；有NA即Blocked |
| ≥2家族双方EM1 | 与双本地终答对象一致，是绝对能力门，不是相对内容收益门；不允许把两Agent当2N | 保留为描述性开发筛查候选，不能据此宣称消息必要 |
| mean Delta≥0.10 | 尺度合法但没有成本效用/独立功效论证；由已知失败后提出，存在事后门槛风险 | 文档明确0.10是探索性研究者选择，必须事前接受；不足则暂不以其作科学Go，不事后改数 |
| ≥2正差且双条件双方有效 | 能排除这些正差完全由弃答造成；但只筛有效样本会有处理后选择偏差 | 总体主指标仍含全部失败；条件化差只描述，不推无偏内容因果 |
| L1+可追溯L2 | L1可审计，E自述不充分；正确事实来源和答案需求需人工盲化可行性说明 | L2需合法接收→请求→正确引用事实→完整终答证据链；不能用词重合自动判通过 |
| 成本吞没/无内容收益 | 四题无成本匹配、无线价值未识别；不能用额外成本“合理”主观豁免 | 内容价值及无线净收益门持续未建立，不随工程过门开放 |

这些门是在原四题已曝光后设计，即使没有逐题答案特化，也不是四题的确认性预注册。新Prompt的严格E语法可能提高格式负担，形成新失败来源；不把格式惩罚导致的差异解释为知识能力。规则变更多项同时发生，不能单因子归因。

建议把决策层次明示为：①公平与安全工程合同；②已曝光开发能力线索；③未来独立证据整合/成本研究。①通过不代替②，②达到未批准数值门也不代替③。此为**未批准的决策表述修订建议**，没有替换旧C数值、重算旧结果或放行下一实验。若研究者不接受阈值依据，应在任何新运行前审定并版本化，不能跑完看结果再调。

## 5. 申请实施之前必须提供的审阅材料

研究者接受字面Prompt/语法/失败分母、时钟部署假设、去累计板变化、D1只用旧开发四家族建议和停止门解释；限定独立新增代码及旧路径不变；冻结计数器/时间/资源/合成输入计划；获得**实现与无模型合同的单独授权**。此后还要新HPC合同/独立审计、真实配额/部署核验、新运行授权，才能谈模型生成。

当前结论：静态合同定义可审议 **Conditional Go**；新版无模型验收 **Pending/未运行**；真实运行 **Blocked**。T3/G1/GP-ID No-Go、D1、T4停止均保持。
