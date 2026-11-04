# MASBench Reasoning关卡、反证与最小能力诊断条件

2026-11-03 P0–P2更新：[验收](../reports/masbench_reasoning_preparation_acceptance_2026-11-03.md)。G01版本化分组核验通过但大组仍242，G02开发预留248/余52、正式三分与功效Pending；G09受控客户端无模型/实际httpx MockTransport工程合同Go，真实chat/context能力Pending；G10资源上界提案已完成、运行授权false。最终147＋独立5合同通过、真实模型0。新registry只是开发预留、未实际曝光；G11/G12仍N0/G13/G14 No-Go，G1/GP-ID No-Go不变。下文为历史快照。

2026-11-03当前覆盖矩阵（替代下方历史表的当前状态，不改旧证据）：[数据审计/合同验收](../reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)、[实现边界](masbench_reasoning_adapter_contract_v1.md)。最终67项合成合同通过；实际模型任务N0。

| 关卡 | 当前状态 |
|---|---|
| G00 | 原基线/73冻结源码保持；新包独立，工程Go |
| G01 | 正文bytes/blob/SHA、300条/200规范化问题核实；context结构通过；2条support一致性异常，Conditional Go |
| G02 | 原许可声明保留；100重复题组/共享文章保守分组已审计，最大242条；9/17/274只是提案，分组/异常处置与正式划分Pending |
| G03 | 白名单PrivateView与admission合成合同Go；可信同进程接口，不声称恶意代码沙箱 |
| G04 | 两提示族固定响应逐request/memory/stop/legacy与原源码一致，有限支持域Go；真实模型能力Pending |
| G05 | 本地R板、fallback、丢失事实不旁路、幂等合同Go |
| G06 | 全启动分母、失败/未启动显式、No-A2A可本地答题合同Go；真实运行注册表Pending |
| G07 | 串行两跳bytes/CRC/ARQ/ACK/预算/部分服务和GOSC概率接口合成合同部分Go；部署CPU、随机场/CRN、共享UL/BF等Pending |
| G08 | 沿用11-02模型文件/独立依赖/metadata证据；本轮未安装/加载/推理 |
| G09 | 只支持无模型fixture；实际chat/context/usage/timeout兼容性Pending |
| G10 | 本轮无模型有界预算已执行；真实能力诊断完整预算未冻结/未授权 |
| G11/G12 | 实际能力/通信依赖均未运行，N0、Pending |
| G13 | 单整消息无多个内容候选，内容排序学术主张No-Go不变 |
| G14 | 净收益/正式验证/训练/可发表性当前No-Go；不得自动运行 |

本轮授权已完成后停止；下一步仅建议审阅数据分组和异常处置，再形成独立能力诊断预算。下文各日期为历史快照。

2026-11-02 15:32（Asia/Shanghai）最新：G08的模型文件、独立依赖环境和metadata端点核验已完成，基础环境Go，详见[维护验收](../logs/masbench-environment-repair-2026-11-02/report.md)。没有推理/模型加载或任务，G01/G04/G09/G11等仍Pending，不能据环境修复解封实验。历史超时/空清单/配额失败说明保留当时含义。

2026-11-02 13:46（Asia/Shanghai）最新状态：HPC已恢复连接并完成只读核查；G08仍**Blocked/运行No-Go**，现因模型注册清单为空、已知manifest未见及依赖缺失，连接超时不再是当前阻断。数据/模型能力/工程合同的Pending不变；[新证据](../logs/masbench-reasoning-hpc-2026-11-02/task_log.md)。下列早前超时注记保留历史含义。

2026-11-02复核增补：G08环境当前核查因SSH超时而**Pending/连接阻断**；表内服务/模型清单和包信息均为2026-10-30历史快照。其余静态关卡与停止规则不变；[复核日志](../logs/masbench-reasoning-static-2026-11-02/task_log.md)保存失败和实际命令。未开始工程实现或能力诊断。

日期：2026-10-30。对应[静态规格v1](masbench_reasoning_adapter_spec_v1.md)与[科研可行性审查](masbench_reasoning_feasibility_review.md)。**静态审查交付Go；方向Conditional Go；当前运行Blocked/No-Go。** 本表是后续研究的必要条件，不是本轮或未来计算的自动授权；所有未验项目保留Pending。

## 1. 当前关卡矩阵

| ID | 关卡 / 进入要求 | 本轮证据与状态 | Go/停止判断 |
|---|---|---|---|
| G00 | 范围/版本与旧负结果保护 | [CODE] GOSC014b85d+冻结扩展；MASBench固定c0301a6；仅Reasoning。G1/GP-ID负结果不改 | **Go（静态身份）**；不是新方法Go |
| G01 | 数据正文身份与合法schema | [CODE] blob9cfc774…、11,996,959bytes；300/200/100为README声明，正文读取未返回内容 | **Pending/运行阻断**：需HPC完整字节SHA、实际计数/唯一ID/字段/重复与证据分区核验；不能按metadata直接宣称全数据通过 |
| G02 | 数据/代码/模型许可及划分 | [CODE] 代码MIT，Reasoning数据README声明CC BY-SA；当前无train/calibration/eval划分；未来模型许可未核 | **Conditional Go（许可声明可追溯）**；分组/模型许可/再分发范围未定前不能进入正式研究 |
| G03 | 私有输入与gold隔离 | [CODE] 原初始化只给对应context，但Sample/raw/logger有全量数据 | **Pending**：agent/request/调度对象权限白名单；禁止gold/peer context/level/共享日志旁路；硬违规No-Go |
| G04 | 无损原生等价 | [CODE/设计] 已追踪self full、listener visible、姓名角色、首答案/board顺序 | **Pending**：future HPC fixture逐request/memory/终止/legacy结果一致；不一致即停，不改原prompt/评分救匹配 |
| G05 | 板与协议解析合同 | [CODE] 累计R/全文fallback/非严格QRA均已识别 | **Pending**：本地板仅own生成+delivered；丢失事实不得从全局板重现；fallback/重复/非法tag全记录 |
| G06 | 评价分母/终止公平 | [CODE] 原mean F1排None，No-A2A若禁答会成为人为零分 | **Pending**：legacy并列、wire_eval_v1全已启动分母、原parser首答案、失败0分；No-A2A可答；无gold选优 |
| G07 | bytes/CRC/ARQ/UL-DL/CPU | [HYPOTHESIS] 28byte候选帧与两跳/ACK/3尝试上限设计 | **Pending**：实际编码、整数预算/部分服务/重复/右边界和CPU独立审计；省ACK/DL/板输入成本No-Go |
| G08 | HPC模型文件/端点/依赖就绪 | [RUN] 2026-11-02三模型manifest与历史一致、所有blob哈希通过；独立环境四项直接依赖/20包、pip check/导入和SDK GET清单/metadata通过；原GOSC环境未改 | **Go（文件/依赖/metadata）**；加载/生成与Reasoning能力未验，不自动放行任务；默认云端回退仍禁止 |
| G09 | context/输出/SDK失败语义 | [CODE] 原参数不显式给模型seed/timeout/retry，system+历史可能超context | **Pending**：未来用已确认模型固定digest、上下文、无静默截断、显式重试/timeout/usage；旧短JSON验收不能代替 |
| G10 | 完整运行/存储预算 | [RUN/设计] 磁盘free不等于quota；吞吐/上下文/费用未测，只有静态调用上界 | **Pending/运行阻断**：独立环境、资源/并行、任务/消息/CPU/输出总cap与事前投影须共同冻结 |
| G11 | 完整通信任务能力 | 未运行；效果N0 | **Pending**：Full下合法输出与原生语义可用，不靠选择有利题/强迫更大模型过门槛 |
| G12 | 通信内容依赖 | 未运行；原任务构造声明不代替当前模型证据 | **Pending**：相同问题/提示族Full与No-A2A比较；终止/分母/调用预算一致，检查差别非人为禁止答题 |
| G13 | 价值机制区别于简单规则 | v1仅单在途整消息，没有多内容排序自由度 | **当前内容排序主张No-Go**；未来若只改变开关/率，应如实收缩；不自动扩候选或训练复杂模型 |
| G14 | 净收益/正式验证/可发表性 | 无本任务新运行；模型与数据未就绪 | **No-Go（当前）**：不得启动校准campaign、封存评估、训练或宣称收益/创新成立 |

Go只对明确列出的静态事实生效。当前缺口包括正文数据、环境与所有工程合同，不能把“Conditional Go方向”解释成允许开始benchmark运行。

## 2. 后续最小诊断的顺序与进入条件

以下均为[HYPOTHESIS/未来提案]；本轮未实施、未选择真实题目、未冻结运行预算。

### S0：先决策是否实施，再验无模型工程合同

1. 用户明确授权下一阶段范围后，先定完整数据与模型恢复/独立环境方案；安装、模型下载/恢复与测试仍按用户授权和HPC登记执行，不在原GOSC venv原地换依赖。
2. 无LLM返回fixture验证base/protocol消息、板、parser、self/peer角色、重复/丢失/过期/CRC、失效ACK、答案发布/无通信答题及评价分母；fixture不能称任务能力。
3. 所有零损伤字段等价、权限、预算/账本合同通过，源码/第三方commit/数据SHA/模型digest/配置/资源绑定后，才可提出能力诊断的实际预算；任一硬失败保留原件并停止，不绕过登记或自动放宽阈值。

### S1：最小能力与信息依赖检查，不设计新价值模型

建议的**预算情景**为4个唯一开发问题（2 easy/2 hard）、base/protocol两提示族、Full/No-A2A两个传输设置、一个已合法可用的本地模型。6个总发言turn、512输出token cap的算式为最多16episodes/96请求（若无SDK重试）；**不代表这些上限已能容纳任务，不是已冻结可执行协议**。上下文/输出不足时回规格审查，不能运行后逐项加长直到模型答对。

Full/No-A2A首先在无新增无线损伤的共同应用语义下比较，不用低SNR把Full也压到任务下限。原生与适配器的等价优先由共享响应fixture验证，不能将两次独立LLM输出相等作为唯一合同。所有实际请求/失败/usage/终止均保存，模型随机性另标；temperature0和数据seed不能保证模型确定。

选择规则必须在模型调用前确定：按完整数据身份和公开难度分层，从不重复的开发ID清单中确定；不得看某模型回答、Full-NoComm差或隐含奖励选题。预先标记这些题为已曝光开发，后续不能流入独立校准/held-out。该小诊断不做功效或显著性主张，不把16episodes当16个独立问题。

### S1的继续/停止建议

| 观察 | 研究动作 |
|---|---|
| Full下输入/上下文被截断、parser或接口不等价、隐藏共享板/ground truth泄漏 | **硬No-Go**，工程/信息边界先修订，保留失败，不评价新方法优劣 |
| Full下几乎无法产生合法有效答案 | **当前模型/预算支持域No-Go**，先判断能力/格式/context原因；不扩大题库或自动调用收费/更大模型 |
| 无通信因禁止提交最终答案而全0 | **实验无效**，不是通信有价值，修正终止合同后另议；不能报正结果 |
| Full与No-A2A在所有开发题均无可辨差异或均靠已有知识答对 | **该小诊断未建立通信识别空间**；不自动加N寻找正结果，不训练估值器 |
| 出现同题Full/No-A2A质量差异且消息交付/输入变化可追溯 | 仅作存在性线索，**不当作已识别因果效应、稳定收益或可发表性**；单次LLM波动仍是替代解释 |
| 简单规则已解释全部差异、或整消息只产生开关/率变化 | 内容排序主张**No-Go**；不能把门槛机制换名字成为新主方法 |

具体最低继续线应在预算/ID冻结时事前规定。例如要求至少两个不同题在同一提示族Full下产生有效答案，且至少一个同题质量差异可关联到真实接收路径，只能筛查“是否值得继续设计”，不是显著性或泛化保证；**该例不是本轮已经批准的成功阈值**。任何无效/超时/中断都计入已启动任务分母，完整配对未完成不得通过关卡。

### S2：只有S1有依据才审阅机制对照

先加入同提示族的Periodic-opportunity、Random、Length、合法Freshness及新命名QA-Bits-RatePrice基线；用独立校准数据与共同实际成本选择参数。不先增加LLM assessor/训练，不直接迁移Search ToM/G0/G1。若要让同状态下存在多内容候选、改变消息粒度/并发，另作研究修订，不能算当前v1已经成功。

S2的价格/次数/样本/总时限、存储与评估族均未制定/批准。即使通过机制关卡，也需另审净任务效用、完整推理费用、独立样本和封存验证；不自动推进正式实验。

## 3. 本轮最终动作

三份静态文档和审查证据交付；不集成benchmark，不改候选/value/任务，不运行任何新测试、任务、模型或训练，不使用付费API，不提交Git。**保留全部历史失败与G1/GP-ID科学No-Go，停止并等待新研究决策。**
