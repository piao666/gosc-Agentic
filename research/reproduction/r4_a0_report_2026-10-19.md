# Research Task Report — R4-A0 bounded pilot (2026-10-19)

- **Research Question / Hypothesis**: 按预登记执行两场景三方案十seed，能否保持参数、配对、负结果、原始输出和实际成本可追溯？本轮是流程/成本pilot，不验证新方法或宣称正式性能优势。
- **已核验前人工作**: [CODE] 原GOSC HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f；冻结方案来自已核对TableXIII。严格复现轨保留search37/rescue38候选口径；本轮不重新选择候选。
- **实际阅读源码**: AGENTS、总说明书/README当前研究状态、R4协议/JSON、run_episode/Config/result、现有hpc_runs/hpc_reproduce与上轮纸码审计。
- **本轮新增或修改**: scripts/r4_pilot.py（独立子进程、超时/中断、追加原始记录）；tests_ext/test_r4_pilot_executor.py；scripts/r4_pilot_audit.py（独立原始记录核验）；任务日志/结果报告/执行状态与进度指针。原gosc/experiments/tests/results/LICENSE不改。
- **实际运行**: 全部计算在HPC n1项目.venv Python3.11.15；第一轮8执行器测试、修正后9测试；一次前置导入失败（0条科学mission）；一次60条成功pilot；一次独立原始数据审计。精确命令、source/commit/lock/配置与资源见各run。

## 运行身份与证据

| Run ID | 实际状态 | 含义 |
|---|---|---|
| hpc-r4-a0-executor-tests-20261019 | completed，8 passed | 合成进程故障/超时/清理/范围测试；没有科学仿真 |
| hpc-r4-a0-pilot-20261019 | failed，exit1 | 正式绝对路径入口缺少仓库sys.path，import gosc失败；worker目录、events、episodes均未创建，0mission启动 |
| hpc-r4-a0-executor-tests-v2-20261019 | completed，9 passed in1.80s | 增加从无关cwd、移除PYTHONPATH后启动绝对CLI的集成测试；保留原失败证据 |
| hpc-r4-a0-pilot-retry1-20261019 | completed，exit0 | 同一计划/seed/参数的60条真实mission，前序失败引用写入context |
| hpc-r4-a0-audit-20261019 | completed，verified | 独立核对60键、全部Config、20组三方案共同世界、均值、60次启动/终止、原文件哈希 |

[RUN] 冻结计划SHA256 `313e55d9a9d30218b4a6088e74299d130727f4546908bd2c53a4edd015aad455`，原r4_plan_v1.json保持不变。seeds9000–9009，search-W100/rescue-W100，每场景gosc/冻结periodic/genie各10条；workers最大2，每worker数值库线程1。配置不是根据pilot结果调整的。

## 原始结果与完成状态

[RUN] **60/60执行成功，0程序失败、0超时、0中断**。20个setting×seed块均有3个方案、共同初始世界指纹；CSV/JSONL无重复/漏项。每条完整Config、result（含curve/trajectory/victims）、stdout/stderr、命令与进程/CPU/RSS均保存。

| 场景 | 方案 | N | 主要终点均值 | UL channel uses均值 | 找全人数的mission | 救全8人的mission |
|---|---|---|---|---|---|---|
| Search-W100 | GOSC | 10 | completion_time=70.2 slots | 12226.1 | 10/10 | 不适用 |
| Search-W100 | periodic sem_raf,k4 | 10 | 75.4 slots | 14393.2 | 10/10 | 不适用 |
| Search-W100 | Genie参考 | 10 | 71.7 slots | 0 | 10/10 | 不适用 |
| Rescue-W100 | GOSC | 10 | saved_fraction=98.75% | 3824.1 | 10/10 | 9/10 |
| Rescue-W100 | periodic sem_ras,k2,theta1 | 10 | 85.00% | 8372.0 | 7/10 | 1/10 |
| Rescue-W100 | Genie参考 | 10 | 96.25% | 0 | 10/10 | 7/10 |

未救全或未找全是原模拟器的科学结果，仍算进程正常完成，未删掉或重跑这些seed。Genie仅是理想通信参考，不能把它当作任务最优上界。

## 探索性配对统计（非正式性能主结论）

[RUN] 固定分析seed0、4000次配对bootstrap；每setting N=10。原始数值/区间见pilot_summary.json：

- Search：GOSC−periodic时间差−5.2 slots，95%CI[−30.0,22.3025]；periodic/GOSC的UL均值ratio1.1773，[0.9641,1.4092]。区间跨0/1，不能说时间/资源优势已被确认。两方案均值均达冻结作者target76.1875slots。
- Rescue：saved_fraction差0.1375（13.75个百分点），95%CI[0.0875,0.20]；UL ratio2.1893，[1.4118,3.0889]。GOSC均值达冻结target0.858375，periodic均值0.85未达。不能只引用ratio而省略这一条件，也不能由N10推广至原100seed/其他场景/新算法。
- 本轮没有候选调优、训练、置信度校准或live/cache-LLM执行。以原run_episode的UL symbols和base dl_symbols记录成本，不冒充完整现实UL+DL控制开销账本。

## 实测成本与扩大阶段的边界

- Pilot登记总墙钟20.1103s，其中mission调度段19.5953s（均不含本地同步时间）。60个worker进程CPU总计34.1957s，包括导入；worker进程平均墙钟0.6099s、median0.4237s、p95 1.5548s。
- 最大单worker RSS56588KiB，约55.3MiB；不是整个容器同时峰值。最大并发2；不使用GPU，GPU峰值未测量/null。当前配额2cores/24GiB。
- 同一两场景/三方案混合若等比例放大到1200条，调度段线性估算391.9s（约6.5min），这只是条件外推；原A1的方案构成及K10/clustered/W50/SNR−5尚未测量，不据此承诺六场景完整运行时长，也不包含grid搜索/LLM成本。
- 下一计算建议是对其余4个冻结场景各GOSC/periodic进行有界成本探测，再固定A1完整任务预算。不得将本轮完成60条等同完成原R4全部关卡。

## 验收与剩余范围

- **测试与结果**: 修正后9项测试通过；60个真实mission执行完成且独立原始记录审计通过；原文件前后哈希不变，完整产物已回传并有receipt。
- **失败/负面证据**: 首次导入错误保留；修正sys.path并增加绝对入口测试后，以新run ID在验证前序0mission的条件下重试。没有隐藏失败记录、换seed或覆盖先前输出。部分救援任务未救全以及探索性CI跨零/目标未达均保留。
- **与原GOSC差异**: 无算法变化；新增的是可追溯的有界执行/验证管理。不能把本轮pilot记为本课题新方法的实验优势。
- **公平性与泄露检查**: 同seed环境、相同冻结Config差分、无调参；9000–9009只作管理pilot，不进入作者校准/eval/fresh集合的训练或选择。
- **可否进入下一阶段**: R4-A0流程验收Go。A1完整100seed×6场景、候选敏感性B、估值frontier C、R5真实LLM与P2问题审查仍待推进；P1整体验收未完成。
- **用户需要批准的下一步**: 本轮已授权的60条pilot与必要执行器验证完成；未自动启动完整campaign、新模型或训练，未push代码。

## 证据路径

成功pilot目录：`research/sync/runs/hpc-r4-a0-pilot-retry1-20261019/outputs/`，其中episodes.jsonl、jobs.json、metrics.csv、worker_logs.jsonl、events.jsonl、mission_status.json、pilot_summary.json、execution_context.json、environment.json、input_integrity.json齐全。

独立审计：`research/sync/runs/hpc-r4-a0-audit-20261019/outputs/pilot_audit.json`。参数/状态历史：原r4_plan_v1.json与当前r4_a0_execution_2026-10-19.json；最终两端核验见本任务verification.json。执行完成与回传完成分别以status与receipts为准。
