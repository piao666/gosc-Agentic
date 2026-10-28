# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 能否以独立版本恢复选包预算合同，并保留旧可行调用？本轮落实[审阅规格](../protocols/selector_budget_feasibility_spec_v1_2026-10-27.md)，限定为工程验收，不检验新任务收益。主验收与补充7个修复到实际wire合同均通过，支持域工程Go、科学No-Go保持。
- **已核验前人工作**：[PAPER] 无新增论文核验，沿用GOSC纸码映射；数值可行性修订不构成新的语义估值贡献，不主张最优调度或新颖性。
- **实际阅读源码**：[CODE] base253a14b19c4410a4606a40c98b8ba24791c7ee43；已映射schemes/realistic正交与共享、GP-v1/v2、GP-ID与独立periodic路径。旧源码和默认入口未改；新显式入口`GP-ID-BF-v1`，选择器`BF-selector-v1`。
- **本轮新增或修改**：[CODE] [纯selector](../../extensions/budget_feasible_selector.py)、[新GP-ID入口](../../extensions/budget_feasible_information.py)、runner、独立目录/原始行/服务审计、合同/协议/报告/进度索引。旧源、原校准、失败run和frozen保持；没有全局替换或monkeypatch原调度器。
- **实际运行**：[RUN] 全部测试/目录回归/短fixture/审计均在HPC n1、UID8301880、Python3.11.15/NumPy2.4.6/pytest9.1.1，2CPU/24GiB，单worker/数值线程1，经hpc_runs登记。前次556文件哈希一致、无running后才同步；真实命令见[登记清单](../logs/selector-budget-implementation-2026-10-27/actual_commands.json)。本地只管理、编辑、Git、轻量SHA和回传。
- **测试与结果**：[RUN] 最终完整485项测试通过（pytest50.02s，runner50.333526s）。主验收37.690869s退出0：7条原违规目录全部修复，192条可行目录原对象/顺序兼容、重复选择稳定；199条样本逐原gzip行及确定性抽样独立绑定；13方案×2旧成本world×观察开关共52个24slot短fixture、真实提交wire/CPU/UL/DL右边界及版本重选独立核验通过。它们不是收益N。
- **失败/负面证据**：[RUN] 缺模块红测试退出2；首单位检查66通过/1失败是测试替身错误引用旧Group，修替身而未放宽验证；首版481通过/初次冻结/绑定核验保留。结果前补充有限算术溢出显式失败后另立485测试与最终freeze；sample SHA与首版相同。原156任务的7条违规和科学No-Go不撤销。补充wire合同的真实失败/修正另记。
- **与原 GOSC 的差异**：[CODE] 原返回满足有效数值域、预算/成员/组约束时原样返回；仅预算失败触发最多64次扩张/40步二分及最终硬检查。数值溢出/停滞/耗尽报错，不静默空包、裁包、改price或吞失败。支持域为显式GP-ID正交Planner search；未将修订接入原realistic共享路径。
- **公平性与泄露检查**：[RUN/CODE] 新后端共同适用于ToM/native/paid/age/price/bits/AoI；periodic保持独立FIFO，额外验预算/wire合同。旧12world目录只作开发回归，选样依据原文件顺序/可行性，不用reward；未扩N、扫参或重跑原156任务。原任务效果不按修复重算或回写；无新科学CI。
- **成本**：[RUN] 主验收37.690869s、child max RSS60140KiB；最终全回归50.333526s、RSS87000KiB，都是runner子进程范围。7次修复首次调用合计process0.002662345s/wall0.002658792s，最多扩张1次、二分40步；192可行目录首次调用合计process0.009639162s。这些小目录计时不含重复调用/诊断，不能称硬件速度保证或旧新加速比。观测关/开各26短fixture的端到端合计4.612795/5.599584s；逻辑CPU仍是固定模型，实测开销单列。无LLM/GPU/训练/付费API。
- **可否进入下一阶段**：本版工程支持域验收Go，全部原件回传。科学仍 **No-Go**；未授权收益campaign、正式test、扩N或训练。单一固定目录集和短fixture不证明所有浮点输入总能成功或任意长mission均正确。
- **用户需要批准的下一步**：本轮授权范围内实现/验收完成后无需追加审批。建议先写入系统模型/数值可行性边界与负结果；若提出新的收益假设、服务修订或新world campaign，另行冻结比较/预算再决定执行，不能借本修复自动放行。

## 实现与验收边界

[CODE] 预算、正整数symbols、finite price/value、成员对象身份和每组最多一项均显式检查。跨不同Group共享只读Option合法；重复Group不合法。空组显式忽略，目录不变更；有限操作数若实际乘法/相减溢出则失败，可行调用兼容只限算术可定义域。这不是把有限输入一律视为安全的承诺。

[CODE] 已验证可行hi是二分不变量；贪心仅填剩余整数预算，返回前再验证。记录selector版本、legacy used/修复路径、上界探测、最终used、group/option稳定索引。重选按版本分派，旧无版本日志仍按legacy；实际任务提交有payload、CRC帧哈希并与选择、CPU入队、UL尝试独立绑定。独立审计新增“预算内同组选两项”拒绝，成员检查不再代替组约束。

[RUN] 52短fixture均未进入修复路径（budget_repairs=0）；因此只支持正常闭环入口/观察中性/账本核验，不能单凭它们证明修复后的真实入队。补充7个明确派生的control-only服务合同用于该缺口，不能冒称原历史闭环任务重放或新的独立任务样本。

## 冻结与证据

| 内容 | 路径/身份 |
|---|---|
| 范围/资源协议 | `research/protocols/budget_selector_acceptance_v1.json`；SHA c906c8af723de9176e5e45126c40c8e77c242029ec7d9a76de550cd0c20972c6 |
| 最终完整合同 | `hpc-budget-selector-contract-v2-20261027`，485 passed |
| 主验收 | `hpc-budget-selector-acceptance-20261027`，6子阶段全completed，独立日志/时限 |
| 最终freeze | [frozen.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/prepare/frozen.json)，SHA 2e89da0bda42cb05d51d12a39b249014b6b15cb47f836232d0fbd8a5c5fa9c38 |
| 样本gzip | SHA 2de83f80d3c7fe30c9a8aaa532b9043465addd3ffb95396d8da464d6f3869c3f，初次与最终一致 |
| 原始行绑定 | [binding.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/binding/binding.json)，156原gzip/199行/7旧违规 |
| 重选原件 | [replay.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/replay/replay.json)，SHA f80322e9ef261c3430153b9b818be40ba5556f3d291d52b51e1bb7e9d6384dbe |
| 短fixture原件 | [fixtures.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/fixtures/fixtures.json)，SHA a815350068868ba07cf14f593cbe8ed1e59b918af38e3f6c01e1947db65aa7c6 |
| 独立审计 | [audit.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/audit/audit.json)，SHA 37ba51bfdd3512c9b68b1b5d70f1ebf8af554828a402787aacaca3c90bc2c30e |
| 成本汇总 | [summary.json](../sync/runs/hpc-budget-selector-acceptance-20261027/outputs/summary/summary.json)，保留实际计时范围及各目录bytes |

[RUN] 主验收receipt `20261027T091527Z-0e55bc`，all_outputs_mirrored=true；新增下载28,516,798bytes含源码/管理快照，不等于实验输出大小。各阶段输出均低于64MiB；主作业上限720s，各阶段90/120/180/120/120/60s，串行失败即停；无新高占用/GPU任务。首版freeze、独立绑定和旧测试均保留，不用于冒充最终源码。

## 补充修复到服务合同

[RUN] `hpc-budget-selector-repaired-wire-v3-20261027`在0.264386s退出0，[wire_contracts.json](../sync/runs/hpc-budget-selector-repaired-wire-v3-20261027/outputs/wire_contracts.json)记录7/7通过。派生方式显式为：原目录仅保留CONF/INTENT，验证派生前的旧选择仍等于原违规选择；发送者/时间映射到sender0/slot0，在复用的27000000成本world构造3-slot服务夹具。实际修复分支、选包到payload/CRC/编码CPU/UL尝试及右边界账本均独立检查，逐例gzip原件保存。它们不是7个历史mission重跑或收益样本，未注入EVID或做任务质量统计。

[RUN] 前两补充run（无版本后缀与v2）均失败于夹具没有调用native `_start()`、缺curve；v2先补初始目标仍不完整，v3读取native启动顺序后补齐初始化才通过。生产selector、GP-ID-BF入口和冻结源身份在这三次之间未变；全部失败证据保留。

[RUN] 最新receipt `20261027T092327Z-4bb9c9`，all_outputs_mirrored=true，覆盖全部主验收/补充合同/失败原件；执行完成与镜像完成分别保存。最终源sync/交付SHA和真实命令见[执行索引](../protocols/budget_selector_execution_2026-10-27.json)及本轮日志目录。本轮未Git提交或push。
