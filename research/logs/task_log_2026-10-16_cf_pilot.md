# 2026-10-16 — Receiver-CF v1 pilot完成

用户批准具体执行器/8missions/128branches/2workers/15min方案。启动37cf326clean；新增隔离hooks/runner/frozen分析/13项契约，执行前commit48404fd5e68c2f7671845ed10ccd2868423edfbe，未改原核心。执行前完整126测试通过57.39s（含13，不相加）；CLI/写入/源码hash gate均审查。

[RUN] Config()、5000–5007开发world、t8/24、每点SHA选择一个原生已选E/I、R4。8missions成功，16slots中2空（5002/5007的t24），14点、112branches、56paired repetitions，不补点、不换seed。pilot wall70.756868s、workerCPU132.96875s；max worker peak39,145,472bytes。实际N最多8独立mission，不是112。无timeout/error，3次false declaration全部保留。

[RUN] DeltaT=failure−success：整体+1.09375，95%探索cluster CI[−2.5,5.265625]；EVID−1.017857[−4.732143,2.703516]，INTENT+2.7[−3.083333,9.291667]。ToM-rho E+.483[-.440,1]、I+.4[-1,1]，不支持稳定失配或优越结论；正/零/负点5/1/8。12/13个非零点MC SE≥|均值|，R4标签精度不足，不直接开发估值器。

[RUN] 16现场tape/direct state匹配，所有当前UL预算≤100、配对非干预packet/draw一致、features白名单、当前尝试cost一致；76上游hash、旧23receiver归档及其raw未变。原R4严格失败/整体统计未定仍保留。whole-state pickle/全部原始结果只留.local；未联网/下载/调用LLM/推送/修改Obsidian。

产物：[完整报告](../reproduction/2026-10-16-cf-pilot/report.md)、[逐点表](../reproduction/2026-10-16-cf-pilot/per_point.csv)、[统计](../reproduction/2026-10-16-cf-pilot/statistics.json)、图、manifest/hash索引/命令；原始`.local/reproduction/2026-10-16-cf-pilot-v1/`。后加plot/review为描述性辅助，实跑并验证；不冒充在执行前126测试内。

Go：离线执行器/标签采集。Pending：MC精度和机制归因；No-Go：稳定可修复缺陷/创新/部署收益主张。建议仅审定固定14checkpoint的R4→32精度批次（新增784branches，预估8.3min/2workers、建议15min cap）；未批准/未运行。详见next_stage_plan.md。本轮结束停止，不自动增加R/换任务/开发模型；下次先读本日志和报告，保持全部负证据。
