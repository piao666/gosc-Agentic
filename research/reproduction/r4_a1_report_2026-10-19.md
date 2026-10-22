# Research Task Report — complete frozen A1 reproduction (2026-10-19)

- **Research Question / Hypothesis**: 六场景冻结GOSC/periodic点能否在作者已知fresh seeds3000–3099重新得到主指标与上行symbols，并保留任务目标、置信区间及全部负结果？本轮验证复现，不验证新方法创新。
- **已核验前人工作**: [CODE] 原HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f，Config/run_episode、validate_headline.SETTINGS及results/rev_validation.json；既有纸码/表XIII审计保留，本轮无重新搜索/校准。
- **实际阅读源码**: AGENTS、总说明书/README、A0/成本报告与issues、原完整协议/预算、r4_pilot/worker、hpc_runs/hpc_reproduce、Config与原冻结配置。
- **本轮新增或修改**: scripts/r4_a1.py、tests_ext/test_r4_a1.py；独立冻结执行方案、执行状态、任务报告与进度。复用原worker/子进程超时管理；原算法/基线测试/results/cache/LICENSE不改。
- **实际运行**: 用户于2026-10-19明确要求启动完整实验。全部计算在HPC n1项目.venv Python3.11.15，六场景×GOSC/冻结periodic×100seeds=1200missions。最大并发2，每worker数值线程1；单条120s、整批1860s。无GPU、模型下载、LLM/API或训练。SSH之外独立进程启动，实际启动PID与命令见launch_receipt.json，run状态以HPC为准。

## 验收结果 [RUN]

**1200/1200条执行完成，600组两方案共同初始世界配对；0程序失败、0超时、0中断。28项测试通过，独立原始数据/统计审计通过。**

**1200条记录的主指标及上行symbols逐seed与作者保存数据一致，差异0条。**该比对限于原保存的主指标和UL数量，不声称作者未保存的所有轨迹/bit/内部状态都做过逐项历史比对。完整本次result/curve/trajectories/victims、Config与日志均已保留。

## 六场景主要结果

每方案N=100；search主终点为completion_time（slot，越小越好），rescue为saved_fraction（越大越好）。UL为普通run_episode的channel uses，不含完整现实控制开销；均值达标是相对作者已冻结目标，不是置信下界判定。

| 场景 | GOSC主指标均值 | periodic主指标均值 | GOSC UL均值 | periodic UL均值 | GOSC/periodic均值达标 |
|---|---:|---:|---:|---:|---|
| search-W100 | 70.93 slots | 76.22 slots | 11825.18 | 14042.70 | 是/否 |
| search-K10 | 54.94 slots | 57.84 slots | 2443.19 | 14450.64 | 是/否 |
| search-clustered | 57.83 slots | 55.09 slots | 6123.42 | 7840.16 | 是/是 |
| rescue-W100 | 93.625% | 90.000% | 4140.28 | 7359.89 | 是/是 |
| rescue-W50 | 95.125% | 87.875% | 3058.80 | 7950.70 | 是/是 |
| rescue-snr-5 | 89.250% | 89.000% | 5151.42 | 43912.61 | 是/是 |

## 配对置信区间与负结果

固定分析RNG0、4000次配对bootstrap，95%percentile区间；六场景为pointwise区间，未作familywise多重比较校正。另存作者口径均值±1.96sd/sqrt(N)，不与配对bootstrap混用。资源ratio是mean(periodic UL)/mean(GOSC UL)，不是逐seed ratio的均值。

| 场景 | GOSC−periodic主指标差 [95%CI] | periodic/GOSC UL ratio [95%CI] |
|---|---|---|
| search-W100 | -5.290 [-14.820, 4.580] slots | 1.1875 [1.1062, 1.2705] |
| search-K10 | -2.900 [-9.071, 3.370] slots | 5.9147 [5.5653, 6.2855] |
| search-clustered | 2.740 [-4.970, 9.691] slots | 1.2804 [1.1446, 1.4311] |
| rescue-W100 | 3.625 [1.375, 6.000] 个百分点 | 1.7776 [1.6313, 1.9252] |
| rescue-W50 | 7.250 [4.625, 9.875] 个百分点 | 2.5993 [2.4248, 2.7744] |
| rescue-snr-5 | 0.250 [-2.625, 3.125] 个百分点 | 8.5244 [7.8882, 9.1880] |

- Search-W100 periodic=76.22slots，冻结目标76.1875；Search-K10 periodic=57.84，目标57.775，分别略超0.0325/0.065slots。它们本来就在作者fresh验证记录中未达标，本次如实复现；不能省略目标条件而只报1.19x/5.91x资源ratio。
- 三个search时间差区间均跨0；clustered均值GOSC反而慢2.74slots。Rescue-snr-5获救比例差区间也跨0。不能把这些结果写成各场景任务性能优势已确认或等效已证明。
- Rescue-W100与W50获救差分别3.625/7.25个百分点；区间见表。这些是原冻结方案的复现结果，不是本课题新方法贡献。
- 所有未找全、未救全、误报均保留。不能用located completed标志冒充救全8人。下表展示两类完成计数；未达到者并非程序失败。

| 场景 | 方案 | 找全人数missions | 救全8人missions |
|---|---|---:|---:|
| rescue-W100 | gosc | 78/100 | 60/100 |
| rescue-W100 | sem_ras | 65/100 | 44/100 |
| rescue-W50 | gosc | 81/100 | 66/100 |
| rescue-W50 | sem_ras | 57/100 | 41/100 |
| rescue-snr-5 | gosc | 63/100 | 38/100 |
| rescue-snr-5 | sem_ras | 69/100 | 45/100 |

## 实测开销与预算核对

[RUN] 运行登记总墙钟574.586676s（约9.58min），其中mission调度段573.812924s；二者均不含本地同步，远低于1860s上限。前轮预测575.824s接近此次测量，但不代表未来环境/任务可精确预测。

1200个完成worker的CPU总计1014.190037core-seconds，包含各worker解释器/导入；runner全子进程CPU还含Git和controller，不与该值混称。最大单worker ru_maxrss=141824KiB，约138.5MiB；不是整个容器并行峰值，也不代表排他模型显存。当前容器24GiB，最大并发2。无GPU工作，GPU峰值未测/null。源码/环境与完整逐条wall/CPU/RSS保存在run产物。

## 验证、边界与后续关卡

- **测试与结果**: [RUN] hpc-r4-a1-tests-20261019：28passed，pytest2.78s；覆盖原17项执行器/成本保护和新增11项A1范围、冻结配置、已披露R3重复限制、ratio口径、零分母和绝对CLI。
- **独立审计**: [RUN] hpc-r4-a1-audit-20261019：1200unique keys/config/result、600配对、1200次start/terminal且并发<=2、原输入哈希、12组均值、6场景bootstrap区间、CSV键与历史逐seed匹配均通过。审计新增仿真0条。
- **失败/负面证据**: 本轮程序失败0；上文目标未达/CI跨零/partial outcomes保留。此前A0零mission导入失败记录不覆盖。
- **与原GOSC的差异**: 无算法变化，仅新增可追溯执行/统计/审计。不能包装成新方法性能增益。
- **公平性与泄露检查**: 已知作者fresh3000–3099只用于冻结复现，不调参/训练；seed3000此前R3已见，本轮完整复现明确再运行且保留两份。并非新的未见测试集；管理pilot结果未用于选参数。资源为base UL和base dl_symbols，不能冒充realistic共享链路完整账本。
- **成本**: 无付费模型/API，助手token未计量；channel/bit/UL/DL与逐条进程成本均保存，未测GPU峰值。
- **可否进入下一阶段**: A1冻结点复现Go。完整P1仍缺B/C、独立校准和R5 cached/live LLM等既定关卡；P2研究问题/文献矩阵未通过，不启动新M0/M1训练。
- **用户需要批准的下一步**: 本轮授权的A1、必要验证、分析/审计与同步已完成；optional600Genie、B候选扩展、C估值frontier、LLM和新方法/训练未启动。下一步先分别审查其范围/成本并推进本地P2文献与RQ。未提交/推送代码。

## 证据与精确命令

- 冻结计划：research/protocols/r4_a1_plan_v1.json，SHA256 `eba3d5b79dabf7fe665e659b815af0a7c3acd615bb54fc83867e347d68f09a40`。原r4_plan_v1.json、cost_probe_v1与预算提案保留原字节；当前完成状态另列r4_a1_execution_2026-10-19.json。
- 测试：research/sync/runs/hpc-r4-a1-tests-20261019/outputs/pytest.xml及stdout/stderr。
- 原始逐条：research/sync/runs/hpc-r4-a1-full-20261019/outputs/episodes.jsonl；同目录jobs/plan/context、events、worker_logs、mission_status、execution_summary、environment/lock及input_integrity。
- 统计：research/sync/runs/hpc-r4-a1-analysis-20261019/outputs/a1_analysis.json、group_metrics.csv、mission_metrics.csv。
- 独立审计：research/sync/runs/hpc-r4-a1-audit-20261019/outputs/a1_audit.json。
- 实际命令：本任务experiment_manifest.json及各run/manifest.json，含完整source snapshot/变更补丁/untracked源码归档。启动证据launch_receipt.json。
- 输出回传与逐文件两端校验：本任务verification.json与research/sync/receipts/；源码最终上行另以.local/hpc-sync/latest_receipt.json核验，不把运行完成当成已全部回传。


[RUN] 本地管理核验曾因Windows默认GBK读取UTF-8元数据失败；改为显式UTF-8后逐文件两端核验通过。该问题没有触发仿真/统计重跑，HPC运行结果未改变。
