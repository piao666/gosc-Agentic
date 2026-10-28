# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 验证GP-ID-v1是否已具备区分native阈值、付费获取服务、买来时间戳和位置内容的可靠实现/观测/核算基础；本轮不检验正式任务净收益。
- **已核验前人工作**：[PAPER] 沿用GOSC纸码映射及A02/D02等既有笔记，未新增原文/出版状态核验，不主张receiver-aware/动态price/反事实思想首次。
- **实际阅读源码**：[CODE] 基线253a14b19c4410a4606a40c98b8ba24791c7ee43，dirty/source SHA以每run snapshot与frozen为准；复核InformationSimulation、ObservedCausalService、local_age、select_rule/catalog_diagnostic、prepare与独立审计，及其GP-v2/原selector接入。
- **本轮新增或修改**：仅在新GP-ID协议显式声明原默认UL/DL速率1/2；补齐selector诊断与实际decision的逐条绑定、六段保护seed内部值检查及7个回归用例；新增HPC只读成本汇总脚本、执行状态/本报告/后续设计审阅与日志，更新导航。原GOSC核心、冻结GP-v2服务/策略、原始结果/cache/LICENSE未改。
- **实际运行**：[RUN] 全部科研计算在HPC n1、UID8301880、Python3.11.15、NumPy2.4.6/pytest9.1.1；重新核验cpuset0–1、quota200000/100000、24GiB RAM，无登记running任务，单worker/数值线程1。预检已核验485份前次同步文件0差异；备份远端索引/工作补丁并严格祖先快进47389eb→253a14b，仅更新引用与索引、不checkout覆盖；之后每run launch单向SHA同步通过。
- **测试与结果**：[RUN] 最终完整合同 **343 passed**；prepare、52短fixture、独立账本/决策审计及只读成本汇总均exit0，见下表。观察开关26对的保存科学结果完全相同；1958次实际decision中1825个非periodic同候选目录scale/price数值对照0差异，不证明普遍逐位等价。原形式重选与实际选择绑定核对通过。
- **失败/负面证据**：[RUN] 首轮335通过/1失败，因JSON未显式包含独立审计需要的dl_rate；实际ServiceConfig默认2未改变，补齐UL1/DL2后336通过。独立静态复核又发现selector记录未绑定实际decision及旧预留范围内部值检查缺口；专门红run保留7失败（1个未拒绝篡改、6个新保护helper未实现），最小修复后完整343通过。初次管理preflight的PowerShell heredoc换行、旧Git不支持branch --show-current已定位并改用UTF-8字节/兼容symbolic-ref；失败日志保留。没有以删失败或改科学参数通过验收。
- **与原 GOSC 的差异**：[CODE] GP-ID-v1是独立命名的原生语义wire+有限UL/DL/CPU机制对照，复用原Planner与lagrangian_select，非作者旧wire精确复现。两条原核心调度路径未修改，不将服务模型进展冒充估值创新或原作者复现缺口已解决。
- **公平性与泄露检查**：[RUN/CODE] 全部13方案固定既有工作点/共同服务与事件索引潜在随机场；native-only不读paid cache、只用实际本地native/收到且有效更新摘要，pose只进估值副本。2个probe world27000000–27000001事前查重/源码冻结，发现范围内无碰撞；旧0–99/1000–1079/3000–3099/4000–4099/20000000–20000199/24000000–24000199保护。不同策略的实际后续接收/轨迹可不同，不声称相同实现事件或单消息直接因果效应。cache资格由冻结源码/合同和序列化状态核对保证，独立审计未从wire原始bytes重建全部cache。
- **成本**：[RUN] 52个24slot短fixture包含两个成本world、13方案及观察开关，**不是52个独立效果样本，任务收益N=0**。最终合同runner47.1918s、probe10.1489s、独立审计0.4361s、汇总0.3156s；CPU/RSS含runner Git管理，不是模型独占吞吐。0GPU/0新LLM/API/token调用/0训练。实测观察开销与逻辑固定预留分别报告。
- **可否进入下一阶段**：合同/有界成本探测/独立审计及完整回传 **Go（已验收）**；信息任务净收益尚未识别，新独立收益校准 **Pending（新协议与完整预算未冻结/未授权）**；原正式test、扩旧样本、训练仍 **No-Go**。
- **用户需要批准的下一步**：本轮完成既有授权范围，无需重复批准。下一校准需要具体比较/端点/新world/N/存储与总运行预算，见[设计审阅候选](../protocols/information_identifiability_calibration_review_2026-10-27.md)；只读外推不是可执行授权。本轮未Git提交/push。

## 登记运行与证据

HPC根目录`/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs/`；本地镜像`E:/gosc/research/sync/runs/`。

| Run ID | 状态 | 实际结果/耗时（runner秒） |
|---|---|---|
| hpc-information-contract-20261027 | failed | 335 passed/1 failed；48.1398 |
| hpc-information-contract-v2-20261027 | completed | 336 passed；46.8556 |
| hpc-information-audit-gate-red-20261027 | failed | 故意红回归7 failed/52 deselected；0.6925 |
| hpc-information-contract-v3-20261027 | completed | 343 passed，pytest46.88s；runner47.1918 |
| hpc-information-prepare-20261027 | completed | 成功JUnit/源码SHA、13case/2world registry gate；1.9245 |
| hpc-information-probe-20261027 | completed | 52fixture、26观察对；10.1489 |
| hpc-information-audit-20261027 | completed | 52fixture独立typed账本、决策和重选绑定通过；0.4361 |
| hpc-information-cost-summary-20261027 | completed | 只读汇总/输入SHA；0.3156 |

这些测试集合重叠，不相加成独立验收数量。完整命令、模型/cache/seed/config、source_sync/manifest SHA与status在各run和本任务actual_commands.json中；源码恢复以snapshot/patch/tar为准，不把当前HEAD当全部dirty源码身份。

## 本轮可支持的成本观测

[RUN] 下列为两个24slot成本world、观察开启分支的均值，单位channel uses；只是固定工作点短fixture的实际账本，不是完整任务收益、成本匹配前沿或因果费用分解。

| 方案 | 全UL+DL | 精确摘要UL | typed摘要DL已服务 | 逻辑CPU预留秒 |
|---|---:|---:|---:|---:|
| public-fixed | 4220.0 | 0 | 0 | 0.2870 |
| native-age | 2911.5 | 0 | 0 | 0.2445 |
| paid-native-age | 8891.5 | 3336 | 2644 | 0.5750 |
| paid-age | 8929.5 | 3336 | 2644 | 0.5755 |
| paid-pose | 10647.0 | 3336 | 2764 | 0.6210 |

完整13方案、观察off/on时间与输入SHA见`hpc-information-cost-summary-20261027/outputs/{summary.json,cost_probe.md}`。1958决策中1096次存在至少一个有效更新本地摘要条目；这不是1096个独立样本，也不证明摘要产生任务增益。新typed分类不能回填旧252mission缺失的DL类型或取代原保守识别界。

## 下一关卡与数据交付

HPC粗外推13方案×假设12校准world×400slot为975.0946s的2倍mission部分与1,550,749,200bytes日志线性体量，但尚缺完整后处理/序列化/传输和长horizon增长成本；12不是功效N，1200s也不是已授权总预算。因此本轮不生成可执行校准N、不运行原预留test、不启动训练。

最终回传receipt `research/sync/receipts/20261027T053948Z-ecd236.json`为all_outputs_mirrored=true，覆盖全部上述run及失败/JUnit/原始fixture/观测/selector/audit/summary。probe阶段新增37,402,967bytes，其他阶段各自在100MiB默认上限内完整拉取；HPC原件保留，不强制把ignored outputs加入Git。

本轮管理/验收证据索引：`research/logs/information-identifiability-acceptance-2026-10-27/`中的task_brief、preflight/reconcile、code_review、actual_commands、delivery。原10月26日未运行报告保留历史含义，以本报告/执行状态更新当前事实。
