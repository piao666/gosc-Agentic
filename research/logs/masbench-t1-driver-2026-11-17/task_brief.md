# Research Task Brief — MASBench B1真实模型Driver集成及合成端到端验收

## 当前授权修订（优先于下方早期草案）

用户读取11-17审阅任务安排后明确“先完成T1-A代码与无模型合同，再具体预算另批T1-B；开始按顺序推进”。本轮**仅T1-A**：静态接线、新无网络fixture合同和独立审查；HPC合同≤240s/2CPU/2GiB RSS、产物16MiB，源码/管理快照另限100MiB。真实HTTP/chat/debug/unload、helper执行、服务修改、T2/T3、Git提交push均不执行。下文4次真实生成预算仅T1-B早期提案，**未获授权，不可用**。成功helper只核现存SHA/环境，不重建、不重跑旧14/36/6/4离线合同。

草稿静态审查先发现：租约未实施、barrier布尔可信、control journal单写者/容量、清理时身份复核、未完成outer guardian、CLI授权门和identity材料不足。本轮按失败关闭原则补齐，并新增合成拒绝/崩溃合同；旧通过源码不修改。

2026-11-17 Asia/Shanghai。用户明确T1完成和独立审查后才决定T2；T3四题另批，T4–T6不得并行启动。复用现有execution_safety、CampaignLedger、ControlledClient/run_controlled、LocalAgent/ContractTransport，独立新增live接线；不改旧fixture/算法语义。

问题：真实完整计数/运行时身份/ContextBinding、持久额度与不可重置deadline、超时/外层中断及卸载栅栏能否闭合？原生即时取消仍未验证；禁止改布尔值代替观测。

现有证据：base d5f5522；固定helper SHA e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5；既有离线合同和临时32768有限域部署已通过。当前默认已恢复1024。只重核现存版本、SHA、环境，不重建C++，不重跑旧离线合同充数。

修改：新增live_driver模块、合成验收入口、新保护合同和独立产物审查脚本、六关卡路线与报告。所有运行经HPC登记，本地仅编辑/Git/哈希/同步。

成本设计：新保护合同≤240s/2CPU/2GiB RSS/16MiB产物；随后T1合成live≤480s（新派发≤350s，余量清理）、模型只已有qwen2.5:7b、默认1024、无持久服务修改；最多4次合成生成（正常32、超时512、控制器中断512、恢复32，预留1088输出tokens不退款），debug≤4、卸载≤4、GET≤40、总产物≤16MiB，服务RAM/GPU监测各16GiB。无模型/依赖下载、真实题目/四题/算法/训练/提交push。授权范围为用户本次明确要求T1集成及合成端到端验收；超界即停。

设计：parent guardian持有服务lease和持久总预算，网络/计数工作交给可强制停止的自有进程组；实际客户端复用，不能把fake seccomp套在真实进程上。HTTP/生成/字节/清理请求先fsync预留。正常计数与usage不一致立即fence；未知usage不退款；超时/控制器崩溃记录真实信号及未知字段，guardian卸载并核ps空/原runner消失。恢复许可从持久barrier及原deadline/剩余额度推导，不擦除失败/uncertain，不新建账本洗额度。全局guardian自身被强杀后须recover-only先清理，未经核验绝不生成。

验收反例：helper/模板/模型/PID/context漂移，implicit truncation，未落盘先发送、恢复重置deadline/额度、清理失败还能派发、原进程仍在、日志预算失败后失联生成，均否决T1。独立审查从原始输入、WAL链、HTTP/信号/卸载与PID证据重算，不读取writer的passed布尔即宣布通过。
