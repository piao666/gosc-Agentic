# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 在固定Planner search、GP-ID服务和price工作点下，购买时间戳/位置是否比native信息和简单对照提供可识别的净收益？本轮完成用户批准的13方案×12新world校准。预登记统计判决 **No-Go**；严格工程审计发现bits/AoI选包越界，整轮验收仍阻断，不能写“全部审计通过”。
- **已核验前人工作**：[PAPER，沿用既有核验] GOSC及D02/A02等机制先例见[纸码映射](../logs/GOSC_paper_code_map.md)、[Gap Matrix](../literature/Research-Gap-Matrix-2026-10-22.md)。本轮未新增论文阅读或出版状态核验，不主张新思想首次。
- **实际阅读源码**：[CODE] base `253a14b19c4410a4606a40c98b8ba24791c7ee43`，dirty源码由每run snapshot/patch/archive保存。阅读 `gosc/schemes.py::lagrangian_select`、`extensions/information_identifiability.py::select`、`extensions/native_task_wire.py::WireGOSC`、`extensions/wire_periodic.py::WirePeriodic`、校准/分析/审计入口。原`gosc`调度平行路径、在线策略、服务与原结果未改。
- **本轮新增或修改**：[CODE] 独立校准协议/设计/runner、全观测无损gzip、预登记分析和独立审计；仅四资源字段的批准派生wrapper与合同；结果后的诊断审计/forensic scan、报告/执行索引/写作进度。结果后审计变更只收集失败项，严格默认拒绝保持，审计源码SHA另存；不回填事前源身份。
- **实际运行**：[RUN] 全部计算由HPC `scripts/hpc_runs.py`登记，n1/UID8301880、Python3.11.15、NumPy2.4.6、2CPU/24GiB；单worker、数值线程1。校准seed28000000–28000011，预算seed28100000–28100001，最多400slots；无LLM、GPU、训练或收费API。真实命令见[actual_commands.json](../logs/information-calibration-2026-10-27/actual_commands.json)与各run manifest。
- **测试与结果**：[RUN] 事前完整379测试通过；批准wrapper另9测试通过。156任务在777.088717s正常结束，全部任务完成，原始结果/全观测/selector保留。预登记分析完成，5组主要比较0组达到联合门槛。严格审计失败；诊断全量核验完成，账本/重选/统计一致，状态仍blocked_selection_budget。结果后完整回归390通过/1失败（新增合成fixture漏字段）；仅修fixture后3项针对合同通过，共覆盖391个不同测试，不能称单次完整391/391通过。
- **失败/负面证据**：[RUN] 原预算投影1940.102682s及279,485,872bytes超过原门槛，原failed/blocked保持；用户另批2400s/384MiB后才执行。严格审计发现70,302条decision中7次真实选包越界（bits6、AoI1，最大304>100）；原严格失败不撤销，辅助对照不能宣称调度合同有效。另保留实现前红测试、合成fixture失败和两次Windows并发回传占用异常；后续receipt单列。
- **与原 GOSC 的差异**：[CODE] GP-ID是独立标识的native/paid时间戳与位置/动态price对照，继承原估值/selector和实际服务接口；无新DeepSC、LLM训练或原版性能主张。gzip是日志存储，无线计费没有因此减少。
- **公平性与泄露检查**：[RUN/CODE] 13方案/12独立world、固定主方法paid-pose、5×3端点族、共享20000次world bootstrap（seed28200000、linear quantile）、最小gain3与成本比门槛1.05均结果前冻结。原test封存，未扩旧N/扫price/换任务/事后改age为主方法。固定price不等于成本匹配；所有主要比较均无预设联合成本支持。闭环策略比较含内生历史，不是单消息直接因果效应。
- **成本**：[RUN] 校准777.088717s，child max RSS134548KiB（runner子进程范围，非模型独占）；逻辑CPU和UL+DL原账本独立于实测wall/process。批准cap402653184bytes；实际原始产物87,333,208bytes。0新LLM调用/token、0训练，GPU峰值未测，未以显卡可见性冒充GPU执行。
- **可否进入下一阶段**：计算执行完成；工程整体验收 **Blocked**；预登记科学 **No-Go**。不扩N、不重选age、正式test/训练不执行。即使最终诊断统计复算一致，也不能消除真实选包越界。
- **用户需要批准的下一步**：本次2400s/384MiB范围已执行，无需重复批准。建议先审阅独立版本的selector预算可行性修订及完整共同对照合同，再决定是否值得任何新实验；本轮不自动修在线策略、重跑矩阵或改变科学问题。当前可写系统模型、识别边界与负结果。

## 主要结果与解释边界

[RUN] 下表取自[预登记analysis.json](../sync/runs/hpc-information-calibration-analysis-20261027/outputs/analysis.json)，配对N=12。gain=对照完成slots−处理完成slots，正数表示处理较快；成本比=处理/对照的均值比。95%区间是探索性bootstrap区间，族区间按15端点Bonferroni尾部另报，均非正式显著性或等价性结论。

| 处理 / 对照 | gain slots [95% CI] | 通信比 | 逻辑CPU比 | 联合门槛 |
|---|---:|---:|---:|---|
| paid-age / paid-native-age | 13.50 [-1.17,30.75] | 0.958308 | 0.893515 | 未通过 |
| paid-pose / paid-ignore | -11.92 [-37.75,14.09] | 1.112573 | 1.078469 | 未通过 |
| paid-pose / native-age | -8.50 [-41.25,24.08] | 6.065509 | 3.543006 | 未通过 |
| paid-pose / periodic k8/eps0 | -33.83 [-73.50,3.17] | 2.142032 | 3.664153 | 未通过 |
| paid-pose / public-fixed | -11.92 [-37.75,14.09] | 3.298526 | 3.767468 | 未通过 |

[RUN] 主要gain族区间依次为[-7.444722,40.833333]、[-49.694722,26.028056]、[-57.083750,39.972778]、[-91.722778,21.445139]、[-49.694722,26.028056]；通信/CPU族区间、分位数和所有次要比较均保留于analysis.json。部署三比较的资源比远高于1.05；不以相同price替代真实成本支持。

[RUN] paid-pose平均完成162.666667slots；native-age154.166667、periodic128.833333、public150.750000。所有156任务均达到完成判据；bits一条恰在400slot完成，不能仅据最大值400称删失。false declaration总数按方案记录：public1、paid-ignore1、AoI2，其他0。bits/AoI有调度违规，因此其辅助描述不作为通过公平合同的有效效果证据。

[RUN] 次要机制结果：native-age/public通信比0.543817，但gain=-3.416667、95%CI[-36.5,28.416667]，逻辑CPU比1.063354；不能声称免费阈值已全面解决任务问题。paid-native-age/native-age的完成均值差0、通信比4.705078、CPU比3.420865。相同native-age下加入位置gain0（退化），相同paid-age下位置gain1、95%CI[0,2.666667]，未达到gain3。native-age/native-price、paid-age/paid-price三类任务/资源端点在本样本相同；不证明普遍等价，且不因此改换主方法。

[HYPOTHESIS] 时间戳使用有均值改善线索，但区间跨0、联合门槛不满足，无法宣称增量净收益已识别；位置在本设定未获得支持。当前结果支持收缩付费位置效率主张、先完成预算可行性审查，不能据小N、不显著或单一工作点推断信息普遍无价值、所有收益皆由调价解释，或服务优化必然成功。

## 执行、授权与不可变身份

[RUN] 原frozen SHA `2c1723706ff9742e00e8b8a2a1c774e7a55e252a129b24da84f2dc14a3251b82`；批准文件SHA `d7891e1605e30037b163a5276d477fa7b690c29128c9c732ffffb6a1580be00b`；[effective_frozen](../sync/runs/hpc-information-independent-calibration-20261027/outputs/effective_frozen.json) SHA `c1c2c19d35f10570e502bada6e1a5c21045898453352ddd7c9a76c88fb44ffec`；[results](../sync/runs/hpc-information-independent-calibration-20261027/outputs/results.json) SHA `8df6df09036ad3ff528fe346409bb71ed6c35c48f5a751d0a307698ebd46c77b`。新审计与诊断绑定同一results，未新采样。

[RUN] 批准派生仅修改硬上限2400s、投影门槛2160s、产物cap384MiB、最低free896MiB；方案/样本/400slots/price/服务/统计不变。事前源sync `20261027T064050Z`、manifest SHA `4acf0a1bb9df3856697df8ddce178f8f450c3feaec036be8b70ce2a13c3e9d1b`。父协议和pending预算提案的旧状态保持历史含义。

| HPC run | 实际结果 |
|---|---|
| hpc-information-calibration-contract-20261027 | 379 passed；runner47.533837s |
| hpc-information-calibration-amendment-contract-20261027 | 9 passed；runner0.551756s |
| hpc-information-calibration-freeze-20261027 | 14world事前冻结；1.949206s |
| hpc-information-calibration-budget-20261027 | 26原始成本fixture；37.103030s，原资源gate退出1 |
| hpc-information-calibration-budget-audit-20261027 | 2.090139s；预算公式/数据核验，status blocked |
| hpc-information-independent-calibration-20261027 | 156任务，777.088717s，退出0 |
| hpc-information-calibration-analysis-20261027 | 1.038688s，退出0，科学No-Go |
| hpc-information-calibration-audit-20261027 | 8.103159s，退出1，Selected budget |
| hpc-information-calibration-budget-diagnosis-20261027 | 11.558117s，退出0，7违规/70302decision |
| hpc-information-calibration-findings-contract-20261027 | 390 passed/1新增fixture失败；48.149921s |
| hpc-information-calibration-findings-contract-v2-20261027 | fixture修正后3 passed；0.347515s |
| hpc-information-calibration-audit-findings-20261027 | 全156记录/账本/统计复核；30.501279s，状态blocked_selection_budget |
| hpc-information-calibration-bracket-diagnosis-20261027 | 7目录初始上端点均不可行，重建选择全匹配；11.633064s |

完整失败/红测试和真实命令全部见各run及[故障登记](../logs/information-calibration-2026-10-27/audit_failure_review.md)。无Git提交或push。

## 最终诊断核验与回传

[RUN] `hpc-information-calibration-audit-findings-20261027` 在30.501279s退出0，完成全部156记录的双SHA/原始行绑定/typed UL、DL、CPU与右边界守恒/selector重选/15端点族和次要统计独立复算。输出[审计记录](../sync/runs/hpc-information-calibration-audit-findings-20261027/outputs/audit.json)状态 **blocked_selection_budget**，不是passed；完整保存7项越界。文件SHA `35d86d84594328282fbe6d13f697319f7d196b7a6e57278966b94cd08f81809e`；独立复算科学status=No-Go。物理UL/DL服务账本检查通过不消除选包决策合同失败，也不修复辅助对照的有效性。

[RUN] 产物实际87,333,208bytes。receipt `20261027T083223Z-07a3d6` 的all_outputs_mirrored=true覆盖校准、原分析、严格失败及诊断审计；HPC原件均保留。本地并发回传异常只影响早期收尾，两端执行status与receipt分开；不清理失败/partial以伪造顺利过程。最终新增文档与诊断的后续回传另见执行索引。未Git提交/push。

[RUN/CODE] 后续[二分端点诊断](../sync/runs/hpc-information-calibration-bracket-diagnosis-20261027/outputs/diagnosis.json)独立转录原`lagrangian_select`选取及40步二分，在全部7违规目录发现初始上端点不可行，最终超预算选择与原记录相同。说明这些目录不满足二分所需的可行端点前提；未改原算法、未宣称所有调用/其他任务均有问题。receipt `20261027T083457Z-d8e935`完整覆盖诊断。下一[修订审阅候选](../protocols/selector_budget_feasibility_review_2026-10-27.md)不授权新模拟。

[CODE] 最终[源码哈希核验](../logs/information-calibration-2026-10-27/source_integrity_checks.json)将Windows原始SHA与LF规范化SHA分列；相对effective_frozen，除两份明确登记的诊断审计文件外，事前列入身份的科学源码/协议均保持。原始Windows CRLF不同于HPC LF，不将换行差异误报为算法修改。
