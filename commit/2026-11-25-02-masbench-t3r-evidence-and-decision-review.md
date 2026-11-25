# 2026-11-25 / 02：T3-R原始证据、失败归因与研究决策审阅归档

- 日期与时区：2026-11-25，Asia/Shanghai。
- 用户授权：在T3-R交付后，用户要求“提交一次girhub，我在远端审阅”；据此授权一次普通提交并正常推送当前研究分支，不授权任何新模型/实验/训练。
- 分支：research/progress-audit-2026-10-19。
- base HEAD：bda3027e17883c1c41dd4ed6d1dd431f0a0657ba；提交前GitHub同分支引用一致。
- 历史T3执行：b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0 + source snapshot 20261125T034132Z；本次归档不改该身份。MASBench固定c0301a650db95958924bb080192c09fef39389a5。
- 不回填本说明自己的提交哈希；以包含本说明的Git历史和远端引用核验。

## 1. 提交内容

归档四份规定交付：[A轨迹诊断](../research/reports/masbench_t3_trace_diagnosis_2026-11-25.md)、[B失败归因](../research/reports/masbench_t3_failure_attribution_review_2026-11-25.md)、[C静态修订关卡](../research/protocols/masbench_t3_revision_gate_review_v1.md)、[D研究决策](../research/reports/masbench_t3_research_decision_2026-11-25.md)。同时归档[完整审计附件入口](../research/logs/masbench-t3r-2026-11-25/README.md)：任务Brief/日志、684文件索引、16episode逐轮索引、验证摘要、四个离线登记的非私有元数据/派生输出及确切脚本版本/回执/交付哈希。

更新根README、research/README、next_steps和提交索引，仅作当前审阅入口。新增限定路径的gitattributes -text规则，保持本轮证据/报告与其SHA合同逐字节一致；不影响旧运行的字节规则。原D报告及delivery_manifest中的未提交/未推送仍是审计收尾时的事实，不因本次归档改写。

不纳入684份HDD正文、controlled_read_aid.private.json、完整私有视图/模型请求/响应、source patch/untracked历史源码包、模型/私人论文/凭据；两份用户未跟踪任务文档及.workbuddy/原样留本地。

## 2. 主要尝试

[CODE]+[RUN] T3-R先核原始文件与执行snapshot，再用独立stdlib工具从原始字节恢复请求/响应、parser、memory、局部板、CRC/分片/账本与评分。随后逐家族审阅H1–H5支持/反证/不可识别，最后仅设计一个公平终答候选。没有重跑16episode，没有替换主提示族或按旧结果挑题。

本次归档仅做Git、轻量文件/SHA/隐私/大小检查和入口维护；不重新执行四次HPC审计或模型测试。初次无网络权限的ls-remote失败，获准网络环境下复核成功；初版凭据正则误命中task-request中的sk-子串，补token边界后无匹配，未改证据原件。

## 3. 结果

[RUN/归档既有T3-R] 684/684原件可读、字节与SHA通过，16983131bytes，无异常；16episode、49任务+2合成旧请求、18卸载栅栏对账；51份计数/渲染/运行窗口绑定核对，与旧评分/wire/next-request无差异。四离线登记：hpc-masbench-t3r-{inventory,traces,context,bindings}-20261125，均exit0；合计runner4.969794s、child CPU4.685329s、最大RSS81256KiB（含管理子进程口径），GPU峰值未测，无模型调用。

[RUN/负结果] base四对F1差0；protocol正差混合有效回答率差，四题EM均0；早答、8次No-A2A空响应、错误比较/局部板及实体漂移均保留。四家族是开发审阅范围，无新增独立N/总体CI/显著性。

[RUN/本次管理] 原delivery_manifest列52项SHA全部匹配；16份既有归档小摘要与provenance匹配；凭据边界扫描无实际匹配，类型索引中的transcript仅“list N”元信息。暂存blob/工作文件SHA、暂存白名单与git diff --cached --check按归档日志核验。未运行pytest/新的HPC计算，避免把管理归档写成实验验收。

首个暂存空白检查exit2，涉及8份保留CRLF的审计JSON行尾CR；不改原件。仅对本轮两附件目录声明whitespace=cr-at-eol以识别其实际行尾，再复核真正尾随空格；原检查摘要保存在归档管理目录，未将失败记录删去。

## 4. 当前进展

T3-R证据Go、失败机制识别Partial、当前模型—任务协作前提Partial。C只是静态Conditional Go，字面Prompt、数据分配和完整可执行预算尚未冻结；真实运行NOT AUTHORIZED。T3科学No-Go、G1/GP-ID No-Go均保留；T4、正式校准/封存test、训练与正向论文收益主张继续阻断。没有确定性投递/评分缺陷证据，不修改历史分数或核心源码。

## 5. 下一步安排

用户在远端审阅四报告及附件，优先裁决C候选的公平终答合同、D1分量代价与预算缺项。后续最小实现/无模型合同须另行授权，真实模型运行和服务配置再单独批准；此次提交推送不放行任何科研计算。推送后核对远端HEAD与本地一致并停止，不创建额外提交补写自身哈希。

## 本次提交验证

- 管理操作与范围记录：[归档Brief](../research/logs/git-publish-t3r-2026-11-25/task_brief.md)、[归档日志](../research/logs/git-publish-t3r-2026-11-25/task_log.md)。
- 普通git add指定路径、git diff --cached --check、暂存/文件SHA、忽略/隐私/大文件检查；完整命令及证据见日志。
- 未运行新测试、仿真、推理或训练，无新模型tokens/无线uses；历史四次HPC审计不重新登记。
- 所有原结果、缓存、许可证与历史Git提交保留；无force push、rebase或main合并。
