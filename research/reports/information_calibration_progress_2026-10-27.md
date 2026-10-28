# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 在固定GP-ID工作点下，付费时间戳/位置使用是否超出native简单阈值且有成本匹配支持？本轮落实新独立校准的统计、样本与完整预算；当前停在资源关卡，尚无新校准效果结果。
- **已核验前人工作**：[PAPER] 沿用GOSC纸码和A02/D02等既有笔记，无新增原文/出版状态核验。原GOSC/ToM/AoI/throughput先例和原No-Go保留。
- **实际阅读源码**：[CODE] 基线253a14b、dirty/source身份以HPC snapshot为准。复用InformationSimulation/原Planner/selector不改，新增独立校准runner、配对统计分析与独立raw gzip/账本/统计审计；新配置只设既有13方案/固定1e-4及12新world，不事后换paid-age主方法。
- **本轮新增或修改**：research/protocols/information_calibration_v1.json与设计；scripts/repro_information_calibration.py、analyze_information_calibration.py、audit_information_calibration.py与3合同文件；结果前规格/代码审阅、freeze/预算及本报告。预算修订另存pending提案，不回写失败协议。
- **实际运行**：[RUN] HPC n1、UID8301880、Python3.11.15、NumPy2.4.6/pytest9.1.1；重新核验2CPU/24GiB、无登记running、526前次同步文件0差异。单worker/数值线程1，全部通过hpc_runs登记；本地只编辑/Git/轻量SHA/同步。
- **测试与结果**：[RUN] 完整379测试通过（pytest47.20s、runner47.533837s）；结果前freeze14world/13case；26个96slot预算fixture全部产生原始任务/全观测/重选gzip记录，预算run37.103030s退出1（门槛失败）；独立审计2.090139s退出0，确认26组数据和预算公式正确，科学status=blocked。无新校准CI，156校准任务0次，不用预算任务质量挑方案。
- **失败/负面证据**：[RUN] 缺新模块的两次测试先红导入失败保留；原资源上限未满足。2倍端到端时间投影1940.102682s>1080s，2倍产物投影279,485,872bytes>268,435,456bytes。不是仿真失败或信息无效证明；原预算/blocked证据保留，不擅改N/日志/阈值来过关。
- **与原 GOSC 的差异**：[CODE] 同GP-ID/付费服务，gzip是原始日志存储格式而非无线编码/新DeepSC；没有修改在线算法、服务计费、任务或LLM。原GOSC与冻结GP-v2保持。
- **公平性与泄露检查**：主要15端点族、配对gain/ratio-of-means、共享bootstrap20000/seed28200000、线性分位、合法400slot删失/软件失败、零分母/退化与停止规则均在新任务结果前固定。校准28000000–28000011与预算28100000–1分离；旧test范围保护，已发现历史无冲突。预算world只用于成本，不计收益N；策略差分不是单消息直接因果效应。
- **成本**：[RUN] 0新LLM/API/token调用、0GPU、0训练。预算与审计用时如上，逻辑通信/CPU账本不变。文件系统free约38.8TB，不等于已核验用户quota。完整观测原件已压缩而不删字段；回传以receipt判定。
- **可否进入下一阶段**：代码/统计/世界冻结/预算数据独立核验Go；原1200s/256MiB下执行校准 **Pending/预算blocked**；正式test/训练No-Go。不得把379合同或26预算fixture称任务净收益成立。
- **用户需要批准的下一步**：[预算修订提案](../protocols/information_calibration_budget_amendment_proposal_2026-10-27.md)：2400s硬上限、2160s投影门槛、384MiB产物cap、896MiB最低free，只改4资源字段，13×12×400及全部科学/统计字段不变。当前pending JSON明确user_authorized=false；真实批准前不执行。

## 原始证据

HPC根`/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs/`；本地镜像`E:/gosc/research/sync/runs/`。

| Run | 状态/含义 |
|---|---|
| hpc-information-calibration-runner-red-20261027 | 新runner实现前导入失败，保留 |
| hpc-information-calibration-stat-red-20261027 | 新分析/审计实现前导入失败，保留 |
| hpc-information-calibration-contract-20261027 | 完整379 passed |
| hpc-information-calibration-freeze-20261027 | 14world、13case、协议/源文件/合同SHA事前冻结 |
| hpc-information-calibration-budget-20261027 | 26条完整成本记录，预算关卡failed，未启动calibration |
| hpc-information-calibration-budget-audit-20261027 | 独立raw记录/预算核验completed，status blocked |

父frozen SHA `2c1723706ff9742e00e8b8a2a1c774e7a55e252a129b24da84f2dc14a3251b82`；预算SHA `b47f63b2bdce3af32ca34c1e67ea15739cb842bdb24af4d5cab5c9dacd410ff0`；独立预算audit SHA `c46f57aa249274d18e3ed5704be786fc830a07979dc7bd04343ef30408a98b7f`。

当前完整回传receipt为`research/sync/receipts/20261027T063106Z-7c6a5b.json`，all_outputs_mirrored=true；预算run新增27,019,303bytes（含源码/管理快照，不是仅任务gzip大小），HPC原件留存。源代码/协议未Git提交或push。

本报告为预算阻断时的进度快照。后续若真实批准资源修订，批准文件、派生effective_frozen与新run及单独最终报告覆盖当前执行状态，不回填此处“0校准”历史含义。
