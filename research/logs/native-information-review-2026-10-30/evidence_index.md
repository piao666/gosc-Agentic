# Native-Information 静态审查证据索引

基线014b85dfc472c45d8ea5f15e83e0c1ed8e938daf。下列源码行范围是本轮只读定位；本轮无源码修改/测试/科研计算。[CODE]指实现事实，[HYPOTHESIS/推导]指新定义与条件分析；两者不冒充运行证据。

| 断言 | 来源 | 证据与限制 |
|---|---|---|
| 工作规则/研究边界 | [AGENTS](../../../AGENTS.md)全文；[说明书](../../../硕士论文研究与实施说明书.md)全文，特别§6/§9 | 完整分段阅读；§6仍是候选而非贡献成立 |
| 上轮候选及未观测缺口 | [10/29报告](../../reports/research_decision_existing_information_2026-10-29.md)全文 | 原样保留；本轮精化而非回写其科学状态 |
| GP-ID负结果/辅助7预算失败 | [校准报告](../../reports/information_calibration_results_2026-10-27.md)全文 | [RUN]既有HPC、N12/156、0/5；本文未重算 |
| BF工程支持域Go、收益N0 | [BF报告](../../reports/budget_selector_acceptance_2026-10-27.md)全文 | [RUN]既有485测试与有界合同；旧失败保持 |
| sigmoid与单Obs增量 | [belief.py](../../../gosc/belief.py) 8–9、17–44 | [CODE] tanh稳定sigmoid；sensor.apply按window/正检测累加，非统计标签 |
| 自己private与FIFO不同 | [simulator.py](../../../gosc/simulator.py) 214–258；[schemes.py](../../../gosc/schemes.py) 341–361 | [CODE] 感知先入pending_llr，filter再保留到FIFO/queued_llr |
| 原TV与G0同类 | [schemes.py](../../../gosc/schemes.py) 363–384 | [CODE] 同Lc/mask/D时公式同类，原wire尚不支持tv mode |
| ToM已有task/intent/geometry | [voi.py](../../../gosc/voi.py) 29–146全文 | [CODE] 非oracle本地共享belief近似；不是未来任务标签 |
| native局部Lc初始化/更新 | [native_paid_adapter.py](../../../extensions/native_paid_adapter.py) 34–44、65–84 | [CODE] self.local[i]只由本地解码task写入；edge更新57–63单列 |
| ACK/own回传两种次序与重复 | 同文件96–140；[paid_receiver_service.py](../../../extensions/paid_receiver_service.py) 108–124、145–201 | [CODE/条件推导] outstanding守卫+ACK移除提供入口不相交前提；需未来本地身份合同，不称已运行 |
| 局部位置/时间戳/intent来源 | 同native文件74–82；[receiver_pose_interface.py](../../../extensions/receiver_pose_interface.py) 31–49、84–105 | [CODE] 启动公开位置/已收到EVID；paid cache不允许作输入；intent map未存TTL元数据 |
| FIFO最长prefix/实际wire/P_s | [native_task_wire.py](../../../extensions/native_task_wire.py) 21–67、69–106 | [CODE] 一EVID组、每rate只最长前缀、raw value乘一次P_s |
| CSIT合法边界 | [native_paid_adapter.py](../../../extensions/native_paid_adapter.py) 96–110；[channel.py](../../../gosc/channel.py) 53–77 | [CODE] known由csit开关决定，不读随机场 |
| BF支持域/失败/后端边界 | [budget_feasible_selector.py](../../../extensions/budget_feasible_selector.py) 26–152；[budget_feasible_information.py](../../../extensions/budget_feasible_information.py) 17–44、67–105 | [CODE] 成员/组/硬预算、64扩张40二分有界；新值需版本化 |
| Native-Age与price对照 | [information_identifiability.py](../../../extensions/information_identifiability.py) 25–75、115–127、243–279 | [CODE/推导] 全组共同f理想等价price/f；EVID-only不等价全局price |
| CPU .001s为模型 | [causal_paid_service.py](../../../extensions/causal_paid_service.py) 14–25、57–68；[paid_receiver_service.py](../../../extensions/paid_receiver_service.py) 74–87 | [CODE] 预留/队列非全估值硬件实测；不由本规格改动 |
| 原生强Periodic不是BF/同候选 | [wire_periodic.py](../../../extensions/wire_periodic.py) 12–61 | [CODE] 按剩余预算admit、周期INTENT/EVID；须放独立参照层 |
| 共享/realistic平行路径 | [realistic.py](../../../gosc/realistic.py) 84–182（本轮阅读）、403–481（沿既有纸码映射定位） | [CODE] 独立构造，v1不接入，不声称覆盖；403–481未在本轮全文重读 |
| 原生接收测试现有范围 | [test_native_paid_adapter.py](../../../tests_ext/test_native_paid_adapter.py) 全文，特别63–74 | [CODE] 现有重复task/own pending测试定义；本轮未运行且不代替新admission身份合同 |
| 事件CRN与seed不可给估值器 | [paired_paid_simulation.py](../../../extensions/paired_paid_simulation.py) 全文 | [CODE] field用于物理层，不属于G1输入 |
| 完整支持配置 | [config.py](../../../gosc/config.py) 全文；native wire71–75 | [CODE] Config默认price1e-5与GP-ID固定诊断1e-4不能混用 |
| 论文既有机制 | [纸码映射](../GOSC_paper_code_map.md) Eq.(4)/Eq.(5) | [PAPER]沿用既有p5/Appendix p12核验，本轮未新读PDF，不查新颖性优先权 |
| 权重有界/同prefix退化/相对选择与停止规则 | [规格](../../protocols/native_information_value_spec_v1.md) §4/§7/§8 | [HYPOTHESIS/代数推导] 无新数值实验；不能作实际任务效应 |

完整阅读的文件以reading_manifest.json的full_read标注；辅助材料只读相关段则明确partial。该manifest保存字节SHA/行数/读取范围，是本地管理记录，不是HPC同步manifest或运行状态。
