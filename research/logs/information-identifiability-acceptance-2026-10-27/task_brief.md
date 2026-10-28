# Research Task Brief — 2026-10-27 GP-ID-v1 HPC验收续接

- 授权与范围：用户在上一轮已授权按优先级实施；因HPC不可达先交付实现，现明确“HPC已可以连接”。本轮续接合同→prepare→最多52个24slot成本fixture→独立审计及回传，不启动独立收益校准、正式test、扩旧样本、训练、GPU/LLM/付费API或Git提交/push。
- [CODE] 基线253a14b19c4410a4606a40c98b8ba24791c7ee43；现有dirty为上轮GP-ID-v1实现/文档，先按其file_manifest核验，保留不reset/checkout/clean/覆盖用户修改。沿用当前研究分支和E:/gosc固定同步入口。
- [HYPOTHESIS] 本轮验证信息权限、观察开关不改变科学结果、原GP-v2短fixture、typed UL/DL/CPU/censor账本及同候选目录数值重选；不回答任务净收益是否成立。
- [RUN，前序] 原GP-v2校准及科学No-Go、上轮SSH失败保持；上轮全部新增测试与探测未运行。原作者校准/cache/历史差异独立单列。
- 修改范围：新验收日志/报告/状态导航；仅在真实失败定位后修复GP-ID独立实现/合同/审计入口。原GOSC与冻结GP-v2保护。旧失败run/协议/报告不回写。
- 前置：只读SSH核对UID/路径/Python/资源/活动任务/Git/origin及同步manifest。HEAD有差异时先证明祖先关系、核验前次同步文件、备份远端管理状态后审慎快进引用/索引，不覆盖工作树；原始数据/远端独有文件保留。相同HEAD/origin并SHA同步通过后才计算。
- 设计与预算：沿用information_identifiability_v1.json；合同240s、prepare60s、probe120s、独立审计60s；单worker/数值线程1，无安装/下载/模型调用。失败先定位且停止下游，新runID保留失败。少量定位回归限120s，不改变科学方法/工作点/候选/world/样本。
- 验收：全合同真实通过，成功JUnit/源码SHA资格、候选probe世界查重冻结、完整52fixture/观察对、同目录重选、独立事件账本/决策核验、两端receipt与文件SHA。任何未执行或未完整回传项明确Pending。
- 反例与限制：观察等价仅限实际合同范围；短probe不是效果N或校准功效资料；闭环arm差分不是单消息直接因果效应；逻辑CPU模型与实际process/wall分报。合同通过也不撤销原No-Go。
- 计划顺序：preflight与源码身份 → 同步 → 合同（必要时定位修复）→ prepare → probe → 独立审计 → 回传/报告/下一阶段设计建议。后续收益试验需另立具体可审阅协议/预算，不自动执行。
