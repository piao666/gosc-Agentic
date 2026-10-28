# Research Task Brief — BF-selector-v1实施与有界验收

- 用户授权：按审阅后规格实施并验收；不扩N、不运行收益校准/正式test/训练。工作树沿用前次连续任务，先核对前次delivery与review verification，不覆盖旧修改。
- [HYPOTHESIS] 独立selector在原调用可行时保留对象/顺序，仅对预算失败进行有界端点修复；新GP-ID显式入口统一接入，旧GOSC/realistic/GP-v1/v2/GP-ID源码和默认保护。
- 前序：[RUN] 原156任务70,302decision内7次bits/AoI选包超预算，初始上界不可行；科学No-Go、严格审计失败保持。工程修复不是语义收益创新。
- 修改：新增extensions/budget_feasible_selector.py、extensions/budget_feasible_information.py，新增runner/独立审计/合同与协议/报告。旧在线/统计/审计文件不修改。
- 验收设计：HPC完整回归；按原文件顺序扫描旧目录，固定选择全部7违规和每个非periodic方案首8/末8个不同可行目录（最多192），仅目录重选、N0。另复用旧成本world27000000–1做13方案×观察开关×24slot共52短合同fixture，非效果样本。独立检查预算/组/成员/版本/提交wire/typed账本，观察开关结果和随机流不变。
- 成本硬界：完整合同240s，prepare90s、目录回归180s、52短fixture120s、独立审计120s；单worker/数值线程1，每个run outputs上限64MiB，最低磁盘256MiB。先prepare冻结输入SHA/源SHA/样本，再执行；失败保留/停止，不自动扩大预算或重跑矩阵。本地只编辑/Git/轻量哈希/同步，计算均登记HPC。
- 可证伪反例：原可行选择变化、返回预算/组/成员违规、无限扩张/溢出被吞、scale/price版本错误、只修部分方案、实际提交不等于已验证选择、观察改变策略/随机流、额外CPU计时丢失。
- 关卡：合同与独立审计通过仅表示支持域工程Go；原收益No-Go不变。保存真实命令/环境/源码/seed/原始输出/失败/两端receipt；本轮不Git提交/push。
