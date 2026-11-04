# 决策报告证据索引

源码基线：014b85dfc472c45d8ea5f15e83e0c1ed8e938daf。行范围为本轮阅读定位，本文不改变这些文件。

| 报告断言 | 类型 | 来源/定位 | 限制 |
|---|---|---|---|
| 156任务/独立N12、0/5主要比较、成本比与CI | [RUN] 既有HPC | [校准报告](../../reports/information_calibration_results_2026-10-27.md)；[analysis副本](../../artifacts/gp-id-bf-20261027/gp_id_calibration_analysis.json)的primary、secondary、cases；副本SHA见provenance.json | 固定工作点、探索性CI；本文未重算 |
| 共同native/paid时间戳下位置gain0/1；native门槛与购买对照 | [RUN] | 同analysis的secondary/native_threshold、purchase_under_native、position_under_native、position_under_paid_age | 次要比较，不是正式位置等价或因果分解 |
| bits/AoI7违规、历史blocked | [RUN] | [诊断审计副本](../../artifacts/gp-id-bf-20261027/gp_id_calibration_diagnostic_audit.json)；校准报告 | 不抹去主要比较；不声称全部工程通过 |
| BF485测试/7修复/192兼容/52fixture、收益N0 | [RUN] | [BF报告](../../reports/budget_selector_acceptance_2026-10-27.md)及白名单bf_selector_acceptance.json | 既有合同，未重新执行 |
| 旧GP-v1价值改变漏斗与反馈/重播 | [RUN] | [10/23诊断](../../reports/sync_cost_value_review_2026-10-23.md)§1–5 | 不作为GP-ID漏斗/费用构成 |
| GP-v2摘要UL及直接费用识别界 | [RUN] | [10/25审查](../../reports/summary_age_mechanism_review_2026-10-25.md)费用及CPU章节 | 识别界非CI；固定账本删费非闭环效果 |
| 免费特权0/6 | [RUN] | [特权诊断](../../reports/receiver_headroom_pilot_2026-10-22.md)主要结果 | 非最优策略/全信息上界 |
| ToM已有距离/意图/避让，非oracle共享belief近似与单步效用 | [CODE] | [voi.py](../../../gosc/voi.py) TeamModel，29–146，尤其30–58、65–80、88–120 | 不是未来真实任务效用 |
| source filter、负值截断、AoI/TV、候选前缀 | [CODE] | [schemes.py](../../../gosc/schemes.py) 341–384、407–469；[realistic.py](../../../gosc/realistic.py) 84–151、369–481 | 平行路径已阅读；不在本轮修改 |
| 同wire CONF/INTENT/EVID、每率最长前缀与成功率 | [CODE] | [native_task_wire.py](../../../extensions/native_task_wire.py) 21–67、69–106 | 无tv模式，不假装已支持/运行 |
| 本地视图/记录/ACK、edge与peer接收差别、CSIT边界 | [CODE] | [native_paid_adapter.py](../../../extensions/native_paid_adapter.py) 34–84、96–140；[paid_receiver_service.py](../../../extensions/paid_receiver_service.py) 108–124 | 全局服务账本不能直接作为发送者输入 |
| native时间戳与付费pose投影 | [CODE] | [receiver_pose_interface.py](../../../extensions/receiver_pose_interface.py) 31–105 | 新位置不新增私有belief；有TTL/时序限制 |
| GP-ID共同factor及日志字段 | [CODE] | [information_identifiability.py](../../../extensions/information_identifiability.py) 25–75、115–127、223–279 | 未记录完整本地Lc/declared/intent快照 |
| GP-v2反馈下界/估值CPU/有界盲目重播 | [CODE] | [causal_paid_service.py](../../../extensions/causal_paid_service.py) 14–101；[causal_paid_simulation.py](../../../extensions/causal_paid_simulation.py) 12–63 | 下界非RTT上界；已有实现不能当待修复事项 |
| BF作为共同版本后端 | [CODE] | [budget_feasible_information.py](../../../extensions/budget_feasible_information.py) 17–26、58–122 | 工程Go不等于新收益 |
| 固定13case/price/filter/periodic、Planner服务 | [CODE] | [repro_information_identifiability.py](../../../scripts/repro_information_identifiability.py) 48–63；[repro_information_calibration.py](../../../scripts/repro_information_calibration.py) 85–109；[冻结协议](../../protocols/information_calibration_v1.json) | .02过滤机制对比与periodic eps0分开解释 |
| GOSC既有任务效用/调度机制 | [PAPER] 沿用既有核验 | [纸码映射](../GOSC_paper_code_map.md)：D01 Eq.(4),p5/Appendix p12；Eq.(5),p5 | 本轮未重读PDF或查外网，不是新颖性审查 |
| 研究目标与M0次序 | [CODE] 研究说明 | [总说明书](../../../硕士论文研究与实施说明书.md) §6.1–6.7（344–440）、§9.1 | G1仅候选；不改RQ/数据集 |
| G0/G1、条件期望、阶段门槛 | [HYPOTHESIS] | [本轮报告](../../reports/research_decision_existing_information_2026-10-29.md)§4–6 | 未实现、未测；无新参数/N/预算冻结 |
