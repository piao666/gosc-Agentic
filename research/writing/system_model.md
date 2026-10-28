# 系统模型与信息可见边界

> 2026-10-27后续工程补充：[BF-selector-v1验收](../reports/budget_selector_acceptance_2026-10-27.md)完成485测试及有界目录/服务合同；新显式GP-ID-BF-v1验证预算、组唯一性、真实成员及提交wire，旧默认未改。原校准违规仍保留，不能回填其模型为可行；新版支持域工程Go不等于任务收益或全浮点/全mission保证。

> 最新2026-10-27：[独立校准/诊断审计](../reports/information_calibration_results_2026-10-27.md)已在12新world执行156任务，typed实际UL/DL/CPU及右边界守恒核完。选包层另有bits6/AoI1次>100-symbol违规，物理服务可行不能替代决策预算合同；整体验收blocked_selection_budget。原selector/服务未改，不能把当前模型写成所有输入均严格预算可行。

> 2026-10-27执行补充：[343合同/52短fixture/独立审计](../reports/information_identifiability_acceptance_2026-10-27.md)已在有限范围验收；模型参数仍是场景假设，尚无部署或任务净收益结论。下文“未验收”为10月26日起草状态。

2026-10-26；状态：GP-ID-v1写作骨架与可审阅模型。实现未HPC验收；物理部署参数未校准。

## 任务、链路与时钟

[CODE] 继承原Planner search任务、CONF/INTENT/EVID候选与lagrangian_select；原`gosc/schemes.py`、`gosc/realistic.py`平行路径不修改。新增入口`extensions/information_identifiability.py::InformationSimulation`继承GP-v2付费服务适配，不是作者旧wire精确复现。当前仅exact/H0、非oracle、正交UL、有限grid/mission、无LLM/救援/共享上行。

| 符号 | 含义 | 可见性/单位 |
|---|---|---|
| i,j,t | 决策发送端、peer接收端、slot | 本地身份与时钟 |
| I_i(t) | sender实际本地信息集 | 本地任务状态+已送达的native/摘要 |
| tau^N_ij | 本地native EVID位置的生成时刻 | 可回退的接收快照ledger，不取全局max |
| tau^S_ij,r_ij,e_ij | 已收到摘要的生成/接收/失效slot | 来自实际解码的cache |
| a_ij(t) | t−有效时间戳，截为非负 | slot；不读peer最新私有内存 |
| V_igo | GOSC候选组g选项o的原代理价值 | 不是未来真实任务收益 |
| f_i(t) | 1/(1+平均peer age) | 无量纲，按本地可见数据 |
| p,U,D | 基础price、实际UL/DL使用 | price依价值尺度；U/D为channel uses |
| C_logic,C_process,T_wall | 逻辑CPU预留、实测进程时间、实测墙钟 | 秒；不能互相替代 |

初始peer位置是既有仿真初始化设定。后续不允许免费查询peer最新位置、未来ACK、reward、全局hidden belief或test标签。native-only决策函数不读取paid cache。

[CODE] eligible摘要需：非self、peer存在、native ledger位置与当前本地view一致、生成早于实际接收、received<=t<=TTL、生成时刻严格新于native。位置只进入估值副本，不直接改Planner或Agent内存。时间戳资格在投影前的本地view上判断，防止用投影结果反过来拒绝同一摘要。

slot时序：本地感知/规划 → 估值工作预留共享CPU → 选包并预约编码/摘要生成 → 当slot服务tick处理先前到达与就绪CPU、UL、ACK/快照与有界重播、有限DL服务 → 更新实际局部接收 → 下一slot规划。当前反馈无排队下界2slot，不是可预知的RTT上界；mission末未服务、在途、待解码均右截断。

## 选择器与动态价格

对预算内的候选选择x，代理目标为sum(x V)−p sum(x uses)。age把同次全部V乘f；在理想最优集合上：

`argmax [f sum(xV) − p sum(x uses)] = argmax [sum(xV) − (p/f) sum(x uses)]`。

这不改变同次V的相对排序，不等价于消息特异的任务效用估计。实际选择器的浮点二分/贪心/破同分需要单独检查；当前合成目录证据不能推为所有闭环逐位相等。GP-ID-v1同时实现scale和显式price形式作为诊断。

## 成本边界

[CODE] 原生语义wire、envelope和CRC均由实际字节编码进入UL；DL对task/task_ack/summary_ack/summary_snapshot有限服务，失败仍收费；task/summary共用反馈/CPU/重播规则。逻辑每次估值和编解码.001s是场景参数，不是硬件实测。摘要只占任务之后剩余UL容量。

日志额外记DL enqueue/served/censor、UL每次尝试、CPU admission/complete、成功到达与decoded。它不消耗模型中的无线/CPU配额，实际运行process/wall包含日志，因此须报告观察开关成本。日志不作为任何调度输入。

## 因果量与统计量不可混淆

[HYPOTHESIS] 固定同一决策前状态，替换factor/估值可识别当时选择机制；没有分支未来任务rollout时不能称真实消息效用。策略层面的配对任务差分含后续行动/候选/排队变化，不是单条消息直接效应，几个arm差分不能相加成纯成本因果分解。

若未来收集deliver/drop标签，须克隆完全相同prestate，事件索引外生随机场匹配、禁止标签进入在线策略、mission分组独立划分，另立预算与协议；本轮未实现/运行标签采集。
