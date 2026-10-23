# 2026-10-23 / 01：付费pose实现、独立校准与成本审查归档

- 日期与时区：2026-10-23，Asia/Shanghai。
- 目的与授权范围：用户要求“先提交一次git，再梳理当前已完成和待进一步验证任务”。本次只做本地提交，不push，不改远端分支；归档本会话连续工作，不创建新的实验结论。
- 分支：`research/progress-audit-2026-10-19`。
- 基线版本：`4ff4147654c07781d77a42acee3f31c0b8792f38`。
- 自身提交身份：由Git历史关联本说明，不在说明中回填自身哈希。

## 改动范围

1. R2/R3白名单交付：47份字节一致产物副本，含17公开模拟图PDF、18TeX、TableVI独立补件、summary与R3 Planner单mission；含来源/哈希manifest。不是新运行，不含私人论文。

   `.gitattributes`仅对该新增交付包禁用换行转换，避免Windows checkout的autocrlf破坏逐字节SHA；不对既有运行记录批量正规化。
2. 最小估值接口：送达pose cache、本地EVID时间ledger、双调度路径估值投影、单lane RTT合同；三bit桶未作为估值输入。
3. 付费闭环：GP-v1原生CONF/INTENT/EVID语义codec、实际帧长/prefix/率、UL/DL/CPU服务、局部接收与下一次规划、幂等/右截断；原gosc/experiments/tests/results/LICENSE不改。
4. 有限periodic候选与事件索引配对噪声；成本探测和12world×12候选独立校准、事前停止/功效规划、失败与负结果。
5. 同步成本与估值改变率只观察诊断及独立算术审计；保留两版观察、辅助同slot计数修正、最终原结果精确匹配证据。
6. 研究导航、协议、报告、HPC manifest/status/log/source snapshot/receipt与本次Git说明。原始outputs和pytest临时目录继续忽略，不强制加入Git。

## 实际验证与证据

### 本次本地管理检查（不冒充HPC科学计算）

- 已核对Git状态、基线、分支、远端和暂存区；没有活动自定义Git hooks，仅有sample文件，提交不会触发本地项目测试。
- 初始新增文件263份/40576335bytes，最大新增单文件1118776bytes；后续新增本次brief/审计/提交说明等管理文件。没有大模型、环境或私人PDF加入。
- 轻量文件/归档检查：273个候选文件、19个新增源码快照包、1654个成员、1891项内容检查；高置信度私钥/token/敏感路径候选0。不是绝对无敏感信息的保证。证据：[precommit_file_audit.json](../research/logs/git-checkpoint-2026-10-23/precommit_file_audit.json)。
- R2/R3包47文件逐字节SHA与原manifest和回传源输出一致，0差异；TableVI补件与初版n/e表分别保留。
- 实际执行Git状态/差异、忽略与文件大小检查、暂存区审阅及`git diff --cached --check`。不可变历史source_changes.patch/stdout等空白提示单列，不为了检查变绿改写旧证据；当前源码/文档单独检查。
- 暂存区逐blob再验47份交付SHA，0差异；被保护gosc/experiments/tests/results/LICENSE改动0，忽略的outputs/.env/.local等路径0。证据：[staged_audit.json](../research/logs/git-checkpoint-2026-10-23/staged_audit.json)。该记录是在加入自身记录文件前取得的277文件暂存快照，最终文件数以Git提交为准。
- 全量默认空白检查退出2：20文件/700提示，其中341来自字节保真的交付包manifest的CRLF，359来自19份历史source_changes.patch。使用`git -c core.whitespace=cr-at-eol diff --cached --check`确认CRLF仅为换行后仍有19份历史补丁/359提示；再排除research/sync/runs与research/logs，当前源码/文档检查退出0。不修改证据字节，不声称全量默认检查通过。
- 本次不重跑HPC测试/仿真/分析，不调用LLM，不下载、不训练；下列通过项全部是此前登记HPC结果。

### 此前HPC证据（本次未重跑）

- [RUN] 最小接口129项HPC测试与文件/哈希审计；paid字节服务修复后128项；原生GP-v1适配145项；见[接口报告](../research/reports/minimal_interface_delivery_2026-10-23.md)、[服务报告](../research/reports/paid_service_progress_2026-10-23.md)、[原生适配](../research/reports/native_adapter_progress_2026-10-23.md)。这些测试集合重叠，禁止相加成独立验收数量。
- [RUN] periodic/CRN最终156测试通过；24成本probe、144校准任务，独立N12，选中periodic k8/eps0。paid-pose相对该对照平均慢3.8333slots、总UL+DL成本比1.426004；相对public-ToM慢1.5slots、成本比1.357991。规划N15419超过事前200world上限，No-Go，无可执行test N/预算。见[校准报告](../research/reports/periodic_crn_calibration_2026-10-23.md)。
- [RUN] 成本/估值诊断最终51测试通过；最终24/24原结果完全匹配，两版主要统计一致；两版48条均是原12world重复，新独立N0。3927决策中96.49%投影改变、79.35%价值改变超过诊断容差、10.54%选包改变；直接摘要账本占额外资源83.28%。反馈实际2slot但RTO1，task历史重播占paid DL77.46%，DL排队p90仅1slot。见[审查报告](../research/reports/sync_cost_value_review_2026-10-23.md)。
- [RUN] 原复验主队列23阶段：22正常退出、作者cache回放失败；真实570任务含180Planner/390混合任务，新cache570/570在预设字段重现；原cache/校准生成链与历史数值一致性仍有缺口。旧证据已在基线提交，本次不重新计算或修改。

## 未完成项、负结果与限制

- 本地Git提交不等于GitHub已经有本次文件；用户本次未要求推送。原报告/运行delivery中的“未提交/未推送”属于当时快照，保留。
- 原P1精确历史一致性、作者cache生成链、原独立校准过程仍部分通过，不能说R1–R6全部科学通过。
- 新GP-v1不是作者bit公式/fragmentation的逐bit复现；只覆盖exact/H0正交Planner search，不推广到shared/rescue/LLM。
- 新方法只做到有界闭环校准和机制诊断，没有付费摘要任务净收益证据；正式验证、成本前沿/全部消融、部署CPU时钟/估值计算成本仍未完成。复杂训练No-Go。
- 失败run、负结果、v1辅助观察计数缺陷和修正都保留；不扩N救结果，不把观察事件当独立world，不把成本账本差异当任务退化因果分解。

## 后续事项

先统一task/summary反馈、CPU可见时钟和有界RTO合同；再审查真实计费的有界catchup/状态反馈，避免全历史盲目重播。所有对照使用同服务规则，不免费窥探receiver状态。变更后另行冻结配置/强对照、工作点、独立校准、N与预算，再决定是否运行正式验证；当前不自动开始。

本次提交完成后，在回复中按已完成、部分通过、待验证/No-Go梳理任务。Git提交结果由`git log -1`/提交后状态确认，不为说明自身哈希制造第二次提交。
