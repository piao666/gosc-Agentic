# 2026-11-04 / 01：G1负诊断、路线B研究审查及MASBench准备验收归档

- 日期与时区：2026-11-04，Asia/Shanghai。
- 用户授权：一次Git提交并正常推送GitHub；本说明随提交归档，并将以后每次提交的五部分说明格式写入仓库约定。没有授权新的模型/任务实验、训练或预算执行。
- 分支：`research/progress-audit-2026-10-19`。
- 提交前base HEAD：`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`；本轮只读`ls-remote`核对远端同分支为同一HEAD，正常push、不强推、不合并main。
- 科研基线仍为014b85d加各run已冻结扩展；MASBench固定`c0301a650db95958924bb080192c09fef39389a5`。历史运行commit/dirty/sync身份按原manifest保留，不回填本归档版本。不填写自身尚未生成的提交哈希，以包含本说明的Git历史和远端引用核验。

## 1. 提交内容

本次归档014b85d之后、2026-10-29至11-03已完成的工作：

- Native-Information G0/G1静态技术规格、可行性审查、独立观察/估值/Shadow实现与合同、运行授权/冻结/执行索引和负诊断报告；旧GOSC/GP-ID/BF算法与默认不改。
- FIFO候选表达、价值与调度耦合、Planner Search环境适配性和路线A/B比较审查。
- MASBench Reasoning静态适配/科研关卡、独立环境与模型恢复记录、精确授权清理的审计、数据核验/分组修订/开发预留、无模型wire/应用/受控客户端、测试及预算提案。没有实施其他MASBench任务。
- 各阶段任务记录、HPC状态/日志/manifest/source snapshot/receipt；[20份关键小型输出副本](../research/artifacts/native-masbench-20261104/README.md)与来源SHA便于GitHub阅读核验，不公开完整题库/轨迹/模型权重。
- [固定提交说明模板](TEMPLATE.md)、[提交约定与索引](README.md)和根AGENTS规则：以后每次commit均按本说明五章节写，含负结果、实际验证和下一步授权边界。

新产生的68份重复运行源码补丁/压缩快照约730,873,123bytes只保留在HPC与本地，不加入本次Git；已跟踪的旧归档历史不删除。`.gitignore`只改变新未跟踪文件的归档范围，失败记录/结果均不删除。新证据范围的`.gitattributes`保留原字节，不批量重新规范化旧证据。同步.partial临时文件继续本地保留。

## 2. 主要尝试

### 无额外接收端同步的信息价值路线

[CODE/研究设计] 明确G0与G1，仅替换EVID估值；逐字段审查本地Lc已包含证据、防重复计算、合法原生位置/intent与回退、量纲及计算成本。固定候选/FIFO/source filter/无线与BF-selector，不改CONF/INTENT/EVID生成来隐式救结果。

[RUN/既有HPC] 先完成最终519项合同及源码冻结，再在两个已曝光world各24slots捕获同决策前状态，做G0/G1及公开简单控制的Shadow重选、观察中性和独立标量/成员/预算/wire审计。不将它们当独立任务收益实验。

### 候选机制与任务适配审查

[CODE/HYPOTHESIS] 审查每rate最长FIFO前缀的表达上限、嵌套/可行性，以及价值差距、可靠性和离散选择器的共同限制；现有相关证据不足以证明唯一因果机制。路线A保留为候选生成研究备选，路线B收束为一个公开Reasoning任务，先验证私有证据、消息边界和信息依赖，不先训练更复杂估计器。

### MASBench环境与最小工程准备

[CODE/静态] 核实Alice/Bob私有context、self full、peer MESSAGE/fallback、本地知识板、原parser/首答案、F1非None分母及原word通信统计；提出真实UTF-8、两跳/ACK/CPU及全启动分母边界。

[RUN/既有HPC] 恢复三个本项目历史digest模型，建立独立Reasoning Python环境；保留下载/配额/慢尾续传失败。用户明确逐项批准后，仅清理指定hai-study、两份Laya目录及完整Ollama安装包，不删除llama或旧失败partial。该维护没有模型推理。

[RUN/既有HPC] 完整数据审计和跟进，修正空/无文章绑定的支持句连边，比较旧新图；按固定hash/问题家族/记录级难度选择四题，异常家族事前不选pilot而保留原件。实现受控客户端与持久审计，使用替身与实际httpx MockTransport验收，不联系模型服务。

## 3. 结果

| 已有证据 | 实际结果 | 边界 |
|---|---|---|
| [Native工程合同](../research/reports/native_information_contract_acceptance_2026-10-30.md) | 最终519项通过，34个新case | 不是任务收益 |
| [G1最小Shadow](../research/reports/native_information_shadow_results_2026-10-30.md) | 82快照、492比较；EVID前缀切换0，速率16/开关9，合格内容witness0 | 所有完整G1选择被声明的有限控制集合复现；不证明任意调价普遍等价；本版内容路线No-Go |
| [模型/依赖维护](../research/logs/masbench-environment-repair-2026-11-02/report.md) | qwen2.5:3b/llama3.2:3b/qwen2.5:7b的历史manifest与全部blob核验；独立环境四直接依赖/20包与metadata通过 | 无加载/生成/Reasoning任务；不等于原论文作者模型版本 |
| [数据/第一轮适配](../research/reports/masbench_reasoning_adapter_acceptance_2026-11-03.md) | 300行、200easy/100hard、200规范化问题、100变体组；最终67合同通过；2条support异常保留 | 唯一ID不代表独立问题；原数据SHA固定，未清洗原件 |
| [P0/P1/P2准备](../research/reports/masbench_reasoning_preparation_acceptance_2026-11-03.md) | 排除14空键后仍38分量/最大242，同组关系差0；4题覆盖4分量、预留248/余52；最终147pytest＋独立5项httpx mock通过 | 历史119/123与重复5项不累加；开发预留未实际模型曝光；不是实际服务能力/通信收益 |
| [上下文/预算](../research/benchmarks/masbench_reasoning_context_resource_budget_v1.md) | 16初始请求bytes/哈希，最大system16,423bytes；98调用/6000s/256MiB提案 | bytes不是tokens；精确tokenizer、有效num_ctx、运行watchdog/完整产物投影仍Pending，未批准执行 |

负面证据完整保留：G1没有内容级决策见证；旧GP-ID科学No-Go不撤销；数据同题跨难度、重叠文章形成大组、两条支持句/索引异常、旧模型许可归档单文件歧义及配额/连接/续传失败均有记录。现有大组由context文章连边已足以产生相同结构，这是有限数据图结论，不是任务性能的因果证明。

上述统计均引用历史run原件，关键小包逐字节复制，不在本轮重新算实验值。本轮未运行项目测试/仿真/统计/模型；确定性合同、完整文件盘点不作任务效应CI。

## 4. 当前进展

- **已完成**：G1静态设计→HPC工程合同→最小机制诊断→本版内容路线No-Go；候选/任务适配静态审查；MASBench Reasoning静态规格、基础环境恢复、数据身份审计、开发预留和受控客户端无模型合同。
- **工程Go有支持域**：147合同与5项实际httpx MockTransport验证接口及错误语义，没有调用真实LLM，不能冒称Reasoning能力已过关。
- **路线B仍Conditional Go**：精确部署tokenizer/实际num_ctx未验；现有启动脚本为1024，32768只是模型metadata/候选配置；未核实完整多turn容量、实际吞吐/显存、服务级取消/全局cap和未来独立评价池充分性。
- **科学未过关**：本任务能力/信息依赖N0，正式校准/封存划分未冻结；单整消息接口不支持多内容候选排序主张。没有新论文收益、创新或可发表性结论，G1及GP-ID科学No-Go保持。
- **版本与执行分开**：此次Git归档是可复核进度快照，不会自动批准预算、改变研究身份或重写历史“未提交/未推送”的当时事实。

## 5. 下一步安排

1. 优先具体审阅部署tokenizer/实际context核验方案，明确是否需要轻量依赖或隔离服务配置；实际调用前每turn核对模板＋自身full历史＋peer visible＋板的精确tokens，禁止静默裁剪。
2. 审阅四题预留248条、剩52条的保守隔离代价与未来独立校准/评价可行性；不能为改善比例事后拆大组、换hash种子或按模型成绩选题。
3. 完成未来执行driver的请求级watchdog、全局请求/墙钟/日志/无线产物cap与恢复账本核验，再审[98次调用、6000s/256MiB预算提案](../research/protocols/masbench_reasoning_minimal_capability_proposal_v1.json)。当前execution_authorized=false。
4. 只有进入条件满足且用户单独批准后，运行四个不同问题的Full/No-A2A最小能力诊断。Full能力不足或质量无可辨差异时停止当前支持域，不自动增N/换模型/训练挽救；正差异也只是存在性线索。
5. 后续每次Git提交新增同格式说明并更新索引；是否提交/推送及新科研运行仍按用户授权，不因模板存在而自动执行。

## 本次提交验证

- 本轮实际只做Git、文件、哈希、暂存与普通push管理；源码/文档和小型产物来源检查见[归档管理日志](../research/logs/git-publish-2026-11-04/task_log.md)及同目录审计JSON。
- staging前排除新重复源码快照/临时partial，原件在本地/HPC保留；检查模型/缓存/环境/私人PDF/凭据/大文件、run原始outputs以及暂存证据字节。敏感信息检查是有范围的检查，不是绝对保证。
- [20份证据](../research/artifacts/native-masbench-20261104/provenance.json)绑定HPC artifacts索引的SHA，分组和registry不手工改写；本轮无新HPC测试。
- 本次提交与推送身份由Git历史、远端分支和提交所含`Commit-Note`关联；不在本文自填自身hash，不制造只为回填hash的第二次提交。

## Research Task Report

- **Research Question / Hypothesis**：归档与说明格式规范化，无新增科学假设。
- **已核验前人工作**：[PAPER] 无新增文献检索/论文结论。
- **实际阅读源码**：[CODE] 本地待归档源码/研究报告、原运行状态/索引、Git和归档规则。
- **本轮新增或修改**：本说明、未来模板/AGENTS约定、证据白名单、归档边界和管理审计；归档上述此前未提交成果。
- **实际运行**：本地Git/文件/哈希/暂存管理及普通commit/push，精确结果见审计与Git历史。
- **测试与结果**：[RUN] 本轮未运行项目测试；引用的519、67、147及5均为既有HPC记录。
- **失败/负面证据**：G1/GP-ID No-Go、全部旧失败与Pending保持。
- **与原 GOSC 的差异**：独立研究扩展归档，原核心/历史结果/许可证不改。
- **公平性与泄露检查**：无新样本、调参或模型输出；raw数据/模型/秘密不入本归档。
- **成本**：Git/文件管理，0新增科学任务/模型调用/训练。
- **可否进入下一阶段**：Git归档可交付；真实诊断仍待既定关卡与单独批准。
- **用户需要批准的下一步**：本次commit/push已授权；未来模型/实验预算另行决定。


暂存复核发现固定MASBench原生参考源码自带尾随空白，作为不可变参考原样保留，不修改以通过格式检查。新科研源码、报告/日志和参考文件按路径设置-text，防止Windows checkout转换破坏既有raw SHA/原生Git blob身份；未对旧tracked文件重新规范化。空白检查排除这些官方参考原件与不可变证据，其余当前源码/文档另核。暂存字节审计结果见staged_audit；加入审计自身结果后最终文件数以Git提交为准，不自哈希。

保留字节的历史CRLF JSON在默认空白检查下会报CR；实际采用cr-at-eol-aware的当前源码/文档检查，官方参考原件单列保留。默认全量空白检查未宣称通过，字节完整性与源码检查分别记录。
