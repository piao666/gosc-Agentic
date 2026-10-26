# Research Task Brief — GP-v2 approved calibration, 2026-10-24

- 科学问题：[HYPOTHESIS] 原已冻结GP-v2服务/候选下，paid pose能否超过校准选出的强简单基线和public ToM，并满足通信/CPU成本支持与功效可行性门槛？只执行独立校准，不对正式test做选择。
- 授权：用户本轮明确答复“批准1200秒校准预算，按原候选和world继续”。原预算blocked和旧科学No-Go保持历史事实；只追加预算修订，不改旧冻结配置、world、源码/price/比较族。
- 起点：[CODE] HEAD47389eba9c6e2838139df3aa47863ab88634e97a。现有dirty均为上一轮授权实现/报告/回传元数据；不reset/checkout/clean，不覆盖这些成果。冻结源见hpc-causal-world-freeze-20261024/outputs/frozen.json。
- 前人成果：[RUN] 190不同合同/回归已通过；42短probe和31,280事件独立审计通过，投影895.5021709203719s。不是本轮重跑合同；本轮没有新增论文阅读。[PAPER] 既有纸码映射沿用，不新增作者主张。
- 本轮文件：新增独立budget amendment JSON与核验脚本；追加独立审计/报告、任务日志及当前状态入口。实验源和原冻结JSON不改；预算接受产物写入唯一HPC run outputs。
- 实验：21候选 × 12新calibration world（23000000–23000011）=252任务；max_steps400；每任务60s；2倍安全系数投影门槛1080s、整轮hard timeout1200s。注册command明确有效预算修订路径；保持原seed/config/源码hash。单worker/数值线程1、现有2CPU/24GiB内；0GPU/0新LLM/0训练/0正式test。
- 验收：审批凭据/原frozen/probe哈希核对；252逐任务原结果及事件完整；独立复算UL/DL/CPU、RTO/重播上限、选择规则、95%探索性CI、6端点功效N/停止条件、离散成本前沿及消融汇总。失败/超时保留，不自动重开预算或扩N。
- 可能反例：任务无增益、成本更高、前沿无支持、方差/功效N不可行、服务仅减少浪费但未增加价值。校准中挑选配置导致选择偏差，CI是探索性，不能宣称确认性显著。
- 原作者复现缺口：作者原校准/cache链/历史数值差异仍分别Pending；本轮Planner服务实验不填补这些缺口，也不证明真实LLM收益。

## 后续验收（2026-10-25追加，不改原计划）

[RUN] 原校准在10月24日447.369435s内完成252任务、原分析No-Go。10月25日续接独立账本/CI/N、前沿/消融/停止条件审计通过，950,281事件核对；规划N21907>200、无主比较联合成本支持，正式test/扩N/训练0次。完整报告research/reports/causal_calibration_audit_2026-10-25.md；回传与交付凭据在该日续接任务目录。不把自动审批服务用量错误写成仿真失败。
