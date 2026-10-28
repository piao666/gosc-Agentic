# 证据索引 — 2026-10-26

- [CODE] 本地基线253a14b19c4410a4606a40c98b8ba24791c7ee43，研究分支research/progress-audit-2026-10-19，启动工作区干净。新增源码身份看file_manifest.json的本地原始字节SHA；未HPC同步，无远端规范化SHA。
- [CODE] 本轮实现/合同/协议/写作：[报告](../../reports/information_identifiability_implementation_2026-10-26.md)、[brief](task_brief.md)、[协议](../../protocols/information_identifiability_v1.md)。合同是待执行代码，不是测试通过证据。
- [RUN，本地管理失败] hpc_preflight.txt：升级权限的合法SSH只读preflight超时/退出255，未取得远端环境信息；非升级尝试的denybin返回在actual_commands.json另列。用户明确当前无法连接，先完成实现。
- [RUN，本地管理] actual_commands.json、static_checks.json：只读Git/文件/轻量JSON与SHA核验。不是pytest、编译、统计或仿真。
- [RUN，旧HPC，非本轮] ../../reports/causal_calibration_audit_2026-10-25.md：21候选/12独立world/252任务、原No-Go；../../reports/summary_age_mechanism_review_2026-10-25.md：旧数据分析/18合同/1536合成选择器比较。均不计作本轮新样本或新通过。
- [PAPER，旧核验] ../../logs/GOSC_paper_code_map.md 与 ../../literature/reading_notes/A02.md、D02.md；本轮未新增PDF原文或出版状态核验。
- [HYPOTHESIS] 付费时间戳/位置超出native信息的任务净收益尚未建立；新独立校准/world/N/预算未制定可执行版本，旧预留test继续封存。
- file_manifest.json不包含自身SHA，不写入Git自身提交哈希或未来run身份；未来执行事实另存HPC登记run与receipt，不能回填本次未运行状态。
