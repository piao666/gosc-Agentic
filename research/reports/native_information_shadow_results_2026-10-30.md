# Research Task Report — 最小有界Shadow机制诊断

日期：2026-10-30（Asia/Shanghai）。基线HEAD为`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`，实际源码是其上的未提交扩展，以冻结SHA和run归档标识。

**结论：[RUN] 最小诊断正常完成，独立审计通过；当前G1内容估值路线在预设诊断范围内No-Go。** 两world都有多前缀覆盖，但G0/G1在全部492次“快照×价格”比较中没有发生EVID前缀切换，未建立不能由简单控制解释的内容级决策差异。停止沿本版G1增加估计器复杂度；不进入任务效用验证、扩N、训练或正式test。该结论不证明信息普遍无价值，也不证明任意调价与G1普遍等价。

- **Research Question / Hypothesis**：[HYPOTHESIS] 在固定候选、FIFO、信道、速率集合、UL/DL服务与BF-selector下，仅改变EVID价值评估，G1能否产生不能由预声明有限价格/尺度/age控制解释的内容级选包差异？本轮不检验G1是否优于GOSC或是否可发表。
- **已核验前人工作**：[CODE] 沿用已验收[静态规格](../protocols/native_information_value_spec_v1.md)、[研究可行性审查](native_information_feasibility_review_2026-10-30.md)和[研究决策](research_decision_existing_information_2026-10-29.md)中的原GOSC/ToM及既有负结果定位。本轮未新增论文检索，不新增[PAPER]贡献或首创性主张。GP-ID负结果和旧失败原件保留。
- **实际阅读源码**：[CODE] 本轮核查`extensions/native_information_shadow.py::analyze_snapshot`、`scripts/repro_native_information_shadow.py::prepare/check_authorization/run`、`scripts/audit_native_information_shadow.py::scalar_reference/audit_records`；上下文/证据来源与观察中性由`native_information_value.py`、`native_information_observer.py`及最终519项合同冻结绑定。源码—接口细节仍以原规格与[工程验收](native_information_contract_acceptance_2026-10-30.md)为准。
- **本轮新增或修改**：新增运行授权侧车、[执行索引](../protocols/native_information_shadow_execution_2026-10-30.json)、本报告及[任务日志](../logs/native-information-shadow-2026-10-30/task_log.md)；新增`scripts/summarize_native_information_shadow.py`只汇总既有输出，不改变评分/决策/停止规则；更新研究进度入口。核心算法、冻结科学源码、静态规格和可行性审查正文未改。
- **实际运行**：[RUN] 仅HPC n1、UID8301880、Python3.11.15项目`.venv`，2CPU/24GiB配额，单worker及数值线程1。冻结、诊断和描述性报告分别登记，命令逐项保存在[actual_commands.json](../logs/native-information-shadow-2026-10-30/actual_commands.json)。world27000000/27000001均为已曝光成本world，各24slots；每sender前8次真实EVID入口，最多96快照；实际各41，共82。Planner，`llm_agents=[]`，没有LLM调用、模型训练、付费API或依赖安装。
- **测试与结果**：[RUN] 复用最终`hpc-native-information-regression-v2-20261030`的519通过（34新case）；本轮未重复测试。冻结验证其JUnit/status/source身份成功。诊断运行内的独立标量数学、身份/整数预算/成员/wire约束和确定性捕获覆盖审计通过82快照；原BF/排序逻辑另作生产重放，不冒称第二个独立优化器。观察开关两条宿主轨迹的科学result、事件、随机字段及最终状态一致，仅墙钟观察耗时排除于结果相等检查。
- **失败/负面证据**：[RUN] 本轮三项登记作业均exit0；科学门槛失败而非运行失败。两个world合格内容witness均为0，详见下表；不删除或选择性报告不利价格点。
- **与原GOSC的差异**：[CODE/RUN] 所有替代估值均在原Public-ToM宿主结束后对同决策前状态离线重选，不发送替代包、不改变任务轨迹；G0/G1只改变EVID值。CONF/INTENT及原wire/FIFO/source filter/速率/BF结构保持。单独WirePeriodic参考允许其原有机制，明确不冒称同BF/同菜单对照。
- **公平性与泄露检查**：[RUN/CODE] 冻结身份匹配，重复EVID账本/已含证据防护及native元数据重放通过；估值上下文只取发送端合法本地belief、已收到的原生位置/intent，未读取真实接收端私有状态、edge全局状态、未来随机事件或未来回报。外层宿主最终状态摘要仅用于观察中性审计，不作为估值输入。曝光world和短horizon不提供独立任务效果证据。
- **成本**：[RUN] 主诊断runner5.681158s，内部计时5.591155s；实际原始outputs18,442,040bytes，低于120s/33,554,432bytes上限。主runner最大子进程RSS82,736KiB，包含Git管理；无GPU/LLM/token调用。回放估值成本见下，完整部署/通信净成本仍Pending。
- **可否进入下一阶段**：**No-Go：本版G1内容估值路线停止；原科学No-Go保持。** 工程通过不等于任务收益或可发表性；任务效果N=0。
- **用户需要批准的下一步**：如继续研究，应先另行审阅候选生成机制或GOSC搜救任务与论文目标的适配性；不得自动修改任务/RQ/划分、训练复杂模型或运行新实验。本轮完成归档后停止，无Git提交/推送。

## 全部诊断结果

[RUN] 六个价格为`0, 0.000025, 0.00005, 0.0001, 0.0002, 0.0004`。使用原始G0/G1共同量纲，未进行跨方法校准或选择最优价格。

| 指标 | world27000000 | world27000001 |
|---|---:|---:|
| 决策前快照 | 41 | 41 |
| 有至少两个EVID前缀 | 35 | 34 |
| G1/G0非统一比例的快照 | 35 | 34 |
| 快照×价格比较 | 246 | 246 |
| EVID内容前缀切换 | 0 | 0 |
| 仅EVID速率不同 | 8 | 8 |
| EVID发送开关不同 | 4 | 5 |
| 同EVID选择（不保证非EVID也相同） | 234 | 233 |
| 无法由声明控制集合复现的完整G1选包 | 0 | 0 |
| 合格内容witness快照 | 0 | 0 |

[RUN] 两world在六个价格点的内容witness均为0。原始/成功概率加权层面的不同前缀鲁棒排序反转均未出现；world27000000有4条“候选对×价格”的net层反转记录，world27000001为0。这些相关记录没有形成实际选中的不同EVID前缀，不能写成4个独立机制样本。82个快照及492个比较也不能当独立任务N或据此生成显著性/CI。

[CODE/RUN] 合格witness同时要求：非统一缩放、涉及最终选中前缀的鲁棒排序反转、G0/G1都发EVID且选不同前缀、G1完整选包不被预声明控制集合复现。本轮连“选不同前缀”这一必要条件都未满足，因此负判决不依赖事后收紧控制条件。控制集合覆盖各声明价格下Public-ToM、G0、同次EVID统一缩放、Native-Age、显式native动态价格、EVID-age和周期门控；“被集合复现”不等于由同一个固定控制政策跨时间复现，也不意味着任意动态价格等价。内容权重打乱和单前缀受限影子另存原始产物，不作事后挑选有利主对照。

[HYPOTHESIS] 本次说明区域权重虽在69个快照改变了跨前缀相对幅度，固定FIFO前缀/可行域仍未把差异转化为不同内容选择。它支持下一步审阅候选表达能力与任务适配性，不能单凭本诊断断言候选生成就是唯一原因。不得用扩大模型或重调权重绕过本轮停止规则。

## 回放计时与边界

[RUN] 对全部82快照，每方法每快照3次hot回放先取中位数，再对快照取中位数；cold是每快照首次回放的中位数。原始单位ns，描述性结果如下：

| 方法 | hot中位数(ns) | cold中位数(ns) |
|---|---:|---:|
| Public-ToM | 1,877,077 | 1,894,428.5 |
| G0 | 1,348,253.5 | 1,367,577.5 |
| G1 | 1,472,194.5 | 1,480,061.5 |

这是restore+native候选/TeamModel/wire+BF的总process时间，包含解释器和缓存影响，不是纯估值算子独占计时、部署队列时延、硬件节能或真实任务净成本；重复不独立，不报推断CI。不能据此断言G1部署比Public-ToM更快，也不把逻辑估值CPU收费假设当实测。

## 身份、运行与证据

[RUN] [预检](../logs/native-information-shadow-2026-10-30/preflight.json)确认无活动任务和上次642文件SHA一致；标准同步后冻结最终519合同与源身份。原计划`diagnostic_execution_authorized=false`保留历史快照，用户本次“运行最小Shadow机制诊断”的明确授权通过独立[授权侧车](../protocols/native_information_shadow_authorization_2026-10-30.json)绑定实际冻结/config SHA，而非改写计划绕过门控。

| 登记run | 用途 | runner耗时 | exit |
|---|---|---:|---:|
| hpc-native-information-freeze-20261030 | 最终合同/科学源码冻结 | 0.102029s | 0 |
| hpc-native-information-shadow-20261030 | 两world×24slot有界机制诊断及内置独立审计 | 5.681158s | 0 |
| hpc-native-information-shadow-report-20261030 | 同一批输出描述性汇总与输入SHA核验 | 0.094997s | 0 |

冻结SHA：`656185273034b13734cbe6b3caf8555f94e8870ab48060bfca76b9f25296f21e`；配置SHA：`eaafcc6b31f1ded6d8069f2c25080c17e7c4ae111dd3b478c1f1cc42199af5de`；授权SHA：`e492e41d357323b21c34ade893b58dd5d52969231f745861eef37d8090c12667`。原始run源码同步ID为`20261030T084431Z`；后续报告同步不回填运行身份。

- [原始summary](../sync/runs/hpc-native-information-shadow-20261030/outputs/summary.json)、[独立audit](../sync/runs/hpc-native-information-shadow-20261030/outputs/audit.json)、[全部shadow](../sync/runs/hpc-native-information-shadow-20261030/outputs/shadows.json)、[全部timing](../sync/runs/hpc-native-information-shadow-20261030/outputs/timings.json)、[宿主对照与捕获](../sync/runs/hpc-native-information-shadow-20261030/outputs/hosts.json)。
- [HPC描述性report](../sync/runs/hpc-native-information-shadow-report-20261030/outputs/report.json)，其输入summary SHA为`fe36d68fb4914a029706d8ba1b2f56f1b343e9012f8984e8c64f62338665d216`；所有原始产物SHA在summary内，汇总逐件核验。
- [最终回传receipt](../sync/receipts/20261030T085115Z-62116f.json)记录`all_outputs_mirrored=true`；主诊断单独回传receipt为`20261030T084554Z-35b09b`，冻结为`20261030T084147Z-875d34`。HPC执行完成与回传完成分别记录。
- 每run的manifest/status/source_snapshot/patch/untracked源码归档均保留于相应run目录；原始outputs继续忽略于Git，无旧结果覆盖或失败删除。

## 审稿判断与后续边界

1. “权重非均匀就证明任务感知贡献”不成立：本轮非比例估值变化没有内容级选包差异，更没有真实任务结果。
2. “无收益只是同步成本太高”不足以解释本轮：G1不购买额外状态，但仍未跨过内容机制门槛；这与此前付费摘要负结果属于不同证据层。
3. “没有区别是因为没有候选”与记录不符：两个world各35/34个多前缀快照；但这仍是有限FIFO前缀菜单，不能推广到任意候选生成机制。
4. “直接训练更强模型”缺少依据：当前门槛No-Go，继续复杂化会掩盖机制负结果。下一研究选择应先明确内容候选是否可识别、任务是否能测到所需决策价值，再申请相应审阅或执行授权。

当前进度：**静态设计完成 → 工程合同通过 → 最小机制诊断完成且No-Go → 本版G1路线停止，候选生成/任务适配性待另行审阅。**
