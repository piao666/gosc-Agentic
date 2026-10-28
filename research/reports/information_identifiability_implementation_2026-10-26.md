# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 接收端摘要是否提供超出native时间戳阈值规则的增量任务价值，且足以支付获取成本？本轮落实可识别对照、观测、审计和写作内核，不产生效果答案。
- **已核验前人工作**：[PAPER] 沿用既有GOSC纸码映射与A02/D02等笔记，本轮未新增PDF阅读/出版状态核验。GOSC已有ToM/AoI/throughput/belief与无线调度；receiver-aware、counterfactual/offline-online和动态price本身均不作为新颖性主张。
- **实际阅读源码**：[CODE] 基线253a14b19c4410a4606a40c98b8ba24791c7ee43：CausalPaidSimulation.select/valuation_view、CausalPaidService的反馈/估值CPU/重播、NativePaidSimulation的局部view/phase_communicate、PaidReceiverService的UL/DL/CPU事件、PoseKnowledge的native/摘要资格、WireGOSC/WirePeriodic、原lagrangian_select与事件索引随机场。原realistic/schemes两条核心调度路径均不修改，新入口独立。
- **本轮新增或修改**：新增InformationSimulation/ObservedCausalService与权限/selector辅助函数；新增合同测试、HPC prepare/probe及独立stdlib审计；GP-ID-v1协议和降费静态候选；四份writing骨架、P1缺口清单、任务日志与证据索引；更新research/协议/RQ/next_steps/project_status导航。具体路径如下。
- **实际运行**：[RUN，本地管理] git status/rev-parse/remote、源码与协议只读定位、文件编辑、差异/空白/保护范围及轻量文件核验。尝试ssh -o BatchMode=yes -o ConnectTimeout=12 hpc 'bash -s'做只读preflight，退出255、连接172.18.101.241:22610超时；没有取得远端身份/环境/配额/活动进程事实。用户随后明确“目前无法连接，先完成实现”。没有上行同步或创建HPC科研run。
- **测试与结果**：**全部新增测试、prepare、world查重冻结、probe与独立审计未运行**；没有本地pytest/仿真/编译/统计。仅本地Git/文件管理检查，结果见任务static_checks.json；它不是源码运行正确性证据。没有可报告CI、新world效果N或信息净收益结果。
- **失败/负面证据**：SSH连接失败，见hpc_preflight.txt；初次非升级沙箱ssh被denybin拦截，升级后的合法只读尝试实际超时。已有两版科学No-Go完整保留；没有因网络失败回退到本地计算。
- **与原 GOSC 的差异**：[CODE] 新独立标识GP-ID-v1复用GP-v2原生语义wire/有限服务与原Planner/selector，新增的只是信息使用规则与被动观察；不是作者旧wire的精确复现。没有新编码器、任务、LLM、学习器或服务降费优化。
- **公平性与泄露检查**：native-only不读取paid cache；只用实际收到/有效/更新的摘要；age在pose投影之前的本地view计算；位置不写Planner。观察器不调用RNG/调度或读取未来reward。观察本身的实测开销必须在HPC开/关probe报告，逻辑服务没有免费部署的含义。整个策略差分不是单消息直接因果效应。旧test封存，候选新probe世界尚未核验；不能称已独立冻结。
- **成本**：本轮0新增实验LLM/API/token调用、0GPU、0测试/仿真/统计/训练。未来合同240s、prepare60s、probe120s、审计60s均只是硬上限，不是实际耗时；单worker/数值线程1。52个24slot短fixture的入口已写，但未运行且不作为任务效果N或功效数据。
- **可否进入下一阶段**：本地实现/写作资产可审阅；运行验收 **Pending（HPC不可达）**。原正式test、扩旧样本、复杂训练仍 **No-Go**。不因实现完成把信息价值主张改为成立。
- **用户需要批准的下一步**：本轮按用户要求先完成实现，无需重复批准。恢复HPC后先执行已写合同/有界成本关卡；实际独立收益校准的world/N/比较族/预算需在这些证据到位后另立具体提案，不自动执行。未Git提交/push。

## 可识别设计的具体补足

原五类对照进一步增加paid-native-age和两种位置×时间戳控制，避免把购买成本、时间戳使用和位置内容混为一谈。native-price/paid-price只是缩放与显式price形式诊断，不是事后主方法。

| 问题 | 对照 | 可解释边界 |
|---|---|---|
| 本地age阈值是否已足够 | native-age vs public-fixed | 策略机制，非新增购买信息 |
| 购买服务有什么影响 | paid-ignore vs public-fixed；paid-native-age vs native-age | 包含内生轨迹/服务变化，非纯固定成本分解 |
| 买来的时间戳有没有额外使用价值 | paid-age vs paid-native-age | 共同购买和服务规则，闭环状态仍会分化 |
| 位置是否有额外价值 | paid-pose vs paid-ignore；paid-pose-native-age vs paid-native-age；paid-pose-age vs paid-age | 固定或共同时间戳阈值规则下的内容使用策略 |

强简单参照包含bits/AoI/periodic k8 eps0；同price并不等于同实际成本。未来正式比较还须事前定义有限候选/成本支持/统计功效。当前不是单条消息deliver/drop克隆分支采集。

## 新增文件与入口

| 文件 | 用途 |
|---|---|
| extensions/information_identifiability.py | 10机制arm、前瞻本地决策/typed UL/DL/CPU观测；GP-v2源码不改 |
| tests_ext/test_information_identifiability.py | 观察等价、旧arm fixture、权限/TTL、完整账本/censor、selector与独立审计篡改拒绝 |
| scripts/repro_information_identifiability.py | HPC prepare需成功JUnit及相同源码SHA；probe固定矩阵/硬超时，仿真后同候选目录scale/price重选诊断；只有prepare/probe模式 |
| scripts/audit_information_identifiability.py | 不导入仿真或producer分析函数的typed资源/决策算术审计 |
| research/protocols/information_identifiability_v1.{json,md} | 新合同/成本probe协议、scope与恢复执行命令；不是收益试验授权 |
| research/protocols/acquisition_cost_candidates_2026-10-26.md | 延后编码/合并/捎带/ACK处理的静态候选，不实施新服务 |
| research/writing/{problem_statement,system_model,experimental_protocol,paper_outline}.md | 说明书9.1要求的四份技术内核草稿 |
| research/reports/p1_evidence_gaps_2026-10-26.md | 原作者校准/cache/历史差异等未恢复证据单列 |
| research/logs/information-identifiability-2026-10-26/ | brief、真实连接失败/管理命令/静态检查/文件SHA索引 |

## 恢复后的验收顺序

HPC身份/环境/配额与无活动任务 → Git/历史工作区保留与同步SHA → 全合同通过 → 同源码prepare/新probe世界查重 → 最多52短成本fixture → 独立审计和完整回传receipt → 可审阅的新独立校准提案。

正式test/训练不在此链的自动下一步。若合同失败用新runID修复复验并保留失败；若信息/成本证据不支持，则收缩主张，不扩N或换任务找阳性。
