# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 选包预算可行性是否能通过最小、共同且可审计的修订恢复？**审阅结论：方向有条件通过；原候选不足以直接实施验收。** 已补具体规格，代码/合同仍Pending；新收益实验、扩N、正式test/训练No-Go。
- **已核验前人工作**：[PAPER] 本轮无新增论文核验，沿用[既有纸码映射](../logs/GOSC_paper_code_map.md)。预算恢复是工程修订，不新增语义估值贡献或方法新颖性主张。
- **实际阅读源码**：[CODE] HEAD253a14b19c4410a4606a40c98b8ba24791c7ee43；工作树是前次任务留下的同批实现/证据，前次delivery逐文件SHA全部相符。阅读原selector、schemes/realistic平行入口、native/causal/GP-ID/periodic、服务入队/实际UL和独立审计/诊断。准确位置见下方。
- **本轮新增或修改**：本报告、[审阅后规格](../protocols/selector_budget_feasibility_spec_v1_2026-10-27.md)、[task brief](../logs/selector-budget-review-2026-10-27/task_brief.md)及进度指针；原候选仅追加后续入口。未修改在线/分析/审计程序、旧失败或原始结果。
- **实际运行**：本地只执行`git status --short`、`git rev-parse HEAD`、`git remote -v`、`rg`/`Get-Content`及轻量`Get-FileHash`与文档编辑。没有执行HPC项目测试/分析/仿真，也没有本地运行项目计算。引用的7条重建/156记录核验均为前轮[RUN]，不是本轮新运行。
- **测试与结果**：本轮测试**未运行**；静态核对及下述条件推导完成。前轮诊断文件SHA `14d3fc7125dc56752aec4a1af3482110e486890a57de25cccf620a4fa4c0456b`，全量诊断audit SHA `35d86d84594328282fbe6d13f697319f7d196b7a6e57278966b94cd08f81809e`轻量核验相符；原状态blocked_selection_budget。
- **失败/负面证据**：[RUN，沿用] 7条违规位于bits6/AoI1，初始端点不可行，40步后选择仍152/228/304>100；没有新失败run。不能因常规测试先前通过而否认该反例。
- **与原 GOSC 的差异**：[HYPOTHESIS] 建议独立selector版本与新的显式GP-ID入口，保护上游和旧默认。此次未实现，也未声称真实任务改善或恢复上游历史精确一致。
- **公平性与泄露检查**：不按reward决定修复路径；相同后端适用于所有相关估值对照，periodic单独验合同；旧目录作开发回归、N不增加。修复影响早期选择后，不能要求后续闭环轨迹仍等于旧轨迹。原paid-pose主要比较No-Go保持。
- **成本**：新增实验/训练/LLM/GPU/付费API=0；修复的CPU/wall尚未测。不能以沿用逻辑CPU常数声称新计算无成本。
- **可否进入下一阶段**：修订设计 **Conditional Go**；待实现、HPC合同与独立审计后才可工程验收，当前 **Pending**。不放行收益campaign或正式test/训练。
- **用户需要批准的下一步**：本轮“做审阅”已完成；建议下一任务仅实现独立selector与冻结的HPC目录/短合同预算，不自动重跑156矩阵。是否开展后续收益研究另行决定。

## 审阅发现（按优先级）

| 优先级 | 发现/证据 | 必须满足的修订要求 |
|---|---|---|
| P1 | 原候选只说扩大上界，没有完整失败合同。原`gosc/schemes.py:288–295`未验证初始hi可行；7条旧目录已构成反例。 | 验证实际pick，上端点只由可行点替换，有限扩张/溢出/停滞后显式失败，最终硬预算检查。单次nextafter或epsilon不作为充分验收。 |
| P1 | 现有`decision_audit`在`scripts/audit_information_identifiability.py:147–156`仅逐选项核对Counter目录成员，未单独限制同组最多一项。两个不同的同组选项可以分别属于目录。**这是静态覆盖缺口，未声称原156任务已出现同组违规。** | 新版观测稳定group_index，审计独立检查组唯一性；须有“总预算内却选同组两项”的篡改拒绝合同。不能把重放一致当可行性证明。 |
| P1 | 将“原可行选择不变”理解为修复后整条mission相同不成立；仅修改bits/AoI也使共同后端不一致。 | 同输入逐调用保留原可行返回对象与顺序；新GP-ID所有适用估值使用同后端。原基线独立保留，闭环差异另立版本。 |
| P2 | `select_rule`与`catalog_diagnostic`共同固定调用旧后端，见`extensions/information_identifiability.py:115–143`；只改在线入口会导致诊断重放旧算法。 | 明确版本写入/分派及selector SHA；新诊断重放同一后端，独立审计保持独立；旧日志缺字段按legacy，不补写修复。 |
| P2 | 旧预算只覆盖旧selector；GP-ID计时与服务逻辑估值收费是不同量，见`extensions/information_identifiability.py:243–279`、`extensions/causal_paid_service.py:61–64`。 | 记录旧调用+端点扩张/重选全部实测CPU/wall；先合同和新成本界，不用固定逻辑CPU常数掩盖开销。 |
| P2 | 入队批次超预算与实际UL超容量不同：`native_paid_adapter.py:104–108`逐项提交，`paid_receiver_service.py:82–90`每项预约CPU，`:160–184`按真实帧长限制每slot UL。 | 保留“决策合同失败、物理UL容量核验通过”区别。多入队可改变CPU/队列/后续规划，不能事后删除额外symbols或按比例修正旧效果。 |

## 调度路径映射与范围

| 路径 | 真实调用点 | 本次修订边界 |
|---|---|---|
| 原GOSC正交 | `gosc/schemes.py:471–475` | 原函数/默认路径保持；没有新版验收 |
| realistic正交 | `gosc/realistic.py:176–181` | 同一旧函数但独立apply，保持原版 |
| realistic共享 | `gosc/realistic.py:403–416` | 用shared_budget聚合多个agent；不可用单sender修复合同冒充覆盖 |
| GP-v1/GP-v2历史 | `native_paid_adapter.py:86–88`、`causal_paid_simulation.py:41–59` | 原身份/默认保持，非本次自动扩域对象 |
| GP-ID非periodic | `information_identifiability.py:253–257` | 建议新显式入口共同接入所有适用arm/mode |
| GP-ID periodic | `information_identifiability.py:251–252`、`wire_periodic.py:20–49` | 原独立remaining扣减路径；核查预算及实际wire，不改为另一调度方法 |
| 逐项入队/实际UL | `native_paid_adapter.py:104–108`、`paid_receiver_service.py:82–90,160–184` | 只接受最终验证的选择再入队；不能用服务容量兜底替代决策合同 |

上述映射意味着原selector是公共依赖，有其他入口暴露；**未运行新诊断，不能推断所有历史场景/结果已触发同一问题或失效**。现有异常直接证据仅为已登记7条GP-ID目录。

## 接受的技术方向与验收门槛

[HYPOTHESIS，静态推导] 成功返回可行的充分结构是：输入合同成立；实际验证hi可行；二分只用实际可行中点更新hi；贪心只填剩余预算且每组一次；最终独立检查再返回。该推导不保证总能找到可表示端点、不保证最优或任务增益。

建议保留旧selector可行返回，只有预算失败时进入有界端点修复；不选择全量改用精确knapsack、改price、事后裁包或永久返回空包。这些替代会引入额外策略变化；当前反例无需它们即可定义最小修订。倍增上界与64次上限是工程规格候选，必须实测/对抗验证，不预先宣称已解决。

[审阅后规格](../protocols/selector_budget_feasibility_spec_v1_2026-10-27.md)已明确：输入/输出合同、旧可行调用兼容、有限失败、稳定身份/重放、所有对照共同接入、实测成本，以及七历史目录/可行目录/数值对抗/篡改拒绝/短服务闭环七类验收。**全部新增合同仍未实现、未运行。**

科学判决维持：付费信息净收益未建立，不扩N/训练；工程修复不是新语义估值方法成功。可以继续撰写负结果、状态可见边界和真实成本模型，不能宣布信息普遍无价值。
