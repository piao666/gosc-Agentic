> 2026-10-22实证状态见[更新检查表](reviewer_objections_2026-10-22.md)。以下为旧风险快照，cached/live和有界诊断的未执行描述已由新证据更新。

# 审稿拒稿自查 — 2026-10-20

这是主动寻找否定证据的检查表，不是录用保证。当前没有新方法结果；“待验证”不得改成“已解决”。原文锚点见13篇reading_notes，候选协议见RQ_v1.md，复验run状态独立登记。

| 可能的核心拒稿理由 | 现有证据/风险 | 最小补证或修正 | 失败时的结论边界 | 当前 |
|---|---|---|---|---|
| 只是重述receiver-aware/ToM | GOSC Eq.4、ToM2C Sec3.3、D04 RBE已有 | 明确新增信息/机制，和同容量无摘要/既有ToM比较 | 不能宣称首次receiver-aware | 已收缩主张，性能待验 |
| 反事实标签并不新 | D02 III-A/B直接提出，BANDMAS Eq6已有RCE | 区分闭环到达条件下的效用与固定两上下文标签；成本与因果识别协议 | 仅实现已有建议可能不足成论文 | 新颖性未成立 |
| 只是offline/online包装 | iCoTASC查表、BANDMAS metadata/shrinkage已有 | 强M0线性/查表，matched容量/训练预算 | 不优于M0则放弃复杂模型 | 未运行 |
| 原估值已足够，根本无headroom | GOSC bits/AoI多数CI跨0；反事实914点低排序/joint负结果 | privileged诊断、阈值错选/零值分层，先M0 | 无headroom则终止新估值路线 | 已纳入反证门槛 |
| 免费读取receiver隐藏信息 | private pending/state/最新intent不可默认可见 | feature ledger、只读成功送达摘要、缺失/age mask、oracle独立 | 只有oracle有效不可称可部署 | 协议写定，未实现 |
| 摘要只是重复已有common belief/intent | GOSC原本共享这些字段 | 增量信息与shuffle/去摘要实验 | 摘要无信息增益则不成立 | 未验证 |
| counterfactual随机流失配 | 原diagnose_value同seed重设不保证分支消费相同 | clone状态，事件索引外生随机流；匹配校验和branch日志 | 未匹配不能解释成干预效用 | 原脚本保留，新协议待实现 |
| 标签/世界/测试泄漏 | 一mission有多决策；A1与fresh重复3000–3099 | mission分组split、排除已用轨迹、seed+world fingerprint注册 | 泄漏实验无效，不能靠重命名seed修正 | 风险已登记 |
| 新方法改了scheduler/encoder/Agent，无法归因 | GOSC双调度路径；A01/AgentComm联合改变多模块 | 首轮固定候选、编码、调度、channel/模型，只换value | 多模块收益不能归因receiver估值 | 尚无新实现 |
| 同price/W不是同成本 | value单位不同；额外DL/ACK/摘要 | actual cost-matched frontier，UL/DL/控制/摘要全计，失败保留 | 成本抹平收益则拒绝效率主张 | 原C matched已运行，新方法未运行 |
| 任务质量被相似度或自评替代 | DeepSC BLEU/BERT非闭环reward；AgentComm TableIII Complete可yes但SR82 | 外部任务真值、失败/截断明确；judge作辅助且计费 | 自评完成不支持任务成功 | 指标合同完成 |
| importance/utility被不当当作可加真实收益 | GOSC局部代理；B10可加拟合非全局真实utility | 原任务rollout结果与joint/interaction诊断，不滥用最优性 | 只可声称代理问题/经验结果 | 尚无新定理 |
| 统计伪重复/挑seed/多重比较 | slot不是独立N；15值比较校正后阳性消失 | 配对mission bootstrap、全run和有效bootstrap数、多重校正 | CI跨0非等价、无显著不写优越 | 原C分析完成，后续待做 |
| 历史复现差异被藏掉 | selection22、frontier479/where364；主完成时间228/146 | 覆盖键审计、36诊断mission、版本与trace记录；原结果不改 | 当前环境可复现≠匹配作者全部历史数据 | 未完全解释，持续保留 |
| 把缺失校准冒充复现完成 | 上游1000–1079只有声明，用户确认无其他源 | 单列资料缺口，公开0–99选参单独命名 | 不称独立校准忠实复现通过 | 上游材料缺口 |
| cached replay冒充真实LLM评估 | Ollama安装smoke不等于完整任务 | 禁HTTP replay；live空新缓存、模型digest/options、attempt/tokens/latency和失败 | 无真实调用不标live成功；不回退planner冒充 | full cached/live未执行 |
| 缓存污染/模型快照不同 | 同名模型digest可能与作者历史不同 | cache key覆盖model/prompt/labels，记录实际digest/上下文/seed及路径隔离 | 不宣称恢复原作者同一模型随机过程 | 当前本地3模型已就绪 |
| 算法鲁棒/泛化过度 | 两网格任务、5选1LLM；surveys非系统实现 | 原任务内边界→经批准的新任务/model迁移，负对照 | 限定simulator与模型，不宣称真实6G部署 | 泛化未验证 |
| 理论借用不满足条件 | D10 Markov/ACK/稳态；GOSC单slot背包条件 | 逐假设映射，缺失条件仅经验前沿 | 不宣称任务全局最优/凸前沿定理 | 未提出新理论 |
| 单位/系统边界不一致 | token、byte、RB、channel use、float向量不同 | 分别报告，明确PHY映射、header、算力和time边界 | 不跨论文直接算节省倍数 | 对照合同完成 |
| 文献证据不完整 | 42篇中13篇本轮重点阅读；其余官方repo/出版页未全核验 | 后续近邻检索/代码审查，新增更强先例则更新矩阵 | 不使用“首次/SOTA已证明” | 文献路线未穷尽 |

## 当前拒稿风险判定

[HYPOTHESIS] 风险最高的是“思想与D02/BANDMAS/GOSC高度重叠”以及“原GOSC负结果意味着更精确估值不带来净任务收益”。目前只能提交研究问题与可执行验证设计，不能写成方法论文的已证实贡献。若M0或oracle headroom不支持，就以负结果/复现审计收缩方向，而非追加大模型、额外task或删失败点。

Go/No-Go：完成本轮P2文档；继续原P1复验；新方法训练No-Go。没有对外投稿、发布、付费API或新方法训练。
