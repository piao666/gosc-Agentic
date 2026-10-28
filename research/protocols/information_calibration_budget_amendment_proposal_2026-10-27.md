# 新校准预算修订提案 — 尚待用户批准

状态：**pending_user_approval**。原1200s/256MiB协议及budget_gate_failed保留，不回写其门槛。156校准任务目前0次，原GP-v2科学No-Go未改变。

## 已完成且独立核验的事实

[RUN] 新执行/分析/审计合同379通过。14个world和源码/配置已在任何新任务结果前冻结；只有预算world28100000–28100001执行了13方案×96slot=26个fixture，校准28000000–28000011仍未运行。

[RUN] 预算fixture完整序列化、全目录重选及无损gzip均计入case耗时。原预算run37.103030s退出1，原因是预设资源门槛，不是任务/仿真异常；独立审计2.090139s退出0，26组gzip双哈希/UL/DL/CPU/censor/决策/重选和预算公式核对通过，得到status=blocked。

- 2倍端到端wall投影：**1940.102682秒**，超过原1080s投影门槛。
- 2倍压缩产物投影（含campaign余量）：**279,485,872 bytes**，超过原268,435,456bytes上限。
- 文件系统可用bytes约38.8TB，仅是filesystem free，未测用户quota，不据此宣称无限配额。

## 请求批准的唯一范围变化

| 项 | 原值 | 提议新值 |
|---|---:|---:|
| 单次156任务校准的进程硬上限 | 1200s | **2400s** |
| 校准前投影放行门槛 | 1080s | **2160s** |
| 校准产物硬上限 | 256MiB | **384MiB（402,653,184bytes）** |
| 最低filesystem free | 640MiB | **896MiB（939,524,096bytes）** |

分析与独立统计/账本审计仍各120s，单CPU worker/数值线程1，不用GPU/LLM/付费API；同步和回传单列。若默认100MiB回传不足，在384MiB产物范围内显式512MiB分批/上限拉取，所有原件留HPC。投影不是实际耗时或保证，外层timeout和实际产物cap仍约束运行。

## 科学内容与旧证据保护

- **不变**：13方案、12个原已冻结但未运行校准world、400slot、price1e-4、服务/信道/Planner/估值、统计种子/端点/CI/停止规则。没有扩旧N、换任务/参数、减少日志或新增模型。
- 原frozen、预算失败与独立blocked证明均按原SHA保留；新修订单独绑定这些SHA。无损记录，不删除失败或超时任务。
- 采用新独立管理入口产生派生effective_frozen，不修改原runner/分析/审计、原配置或原frozen。派生仅四个资源字段，记录父frozen/预算/审计/新批准文件SHA；全部原在线源码与统计文件仍须逐字节一致，新入口及其合同源码另记SHA。
- 新管理入口必须先通过HPC合同，且只接受真实用户批准的status=approved/user_authorized=true文件。pending候选不能执行。批准后仍复核磁盘和投影，原14world不重新生成或替换，不计新N。

批准只覆盖这次156任务探索校准及配套分析/审计/回传；不包括正式test、自动扩N、训练、公共发布或Git提交。若修订仍不满足实际硬上限，保留记录并停止，不自动再次抬高预算。

证据：`hpc-information-calibration-budget-20261027/outputs/{results.json,budget.json}`、`hpc-information-calibration-budget-audit-20261027/outputs/audit.json`、`hpc-information-calibration-freeze-20261027/outputs/frozen.json`。具体SHA见同名pending JSON候选。
