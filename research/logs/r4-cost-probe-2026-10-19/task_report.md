# Research Task Report - R4 remaining-setting cost probes (2026-10-19)

- **Research Question / Hypothesis**: 四个尚未测量场景的耗时/资源量级如何，完整六场景100seed预算应设多少？本轮只测成本，不作性能推断。
- **已核验前人工作**: [CODE] 原validate_headline.SETTINGS与results/rev_validation.json的冻结点；前轮已完成纸码/表XIII核对。本轮未重新搜索候选或重读论文。
- **实际阅读源码**: AGENTS、总说明书、README、R4协议/预登记、前轮报告与issues、Config、原validate_headline、r4_pilot与hpc_runs/hpc_reproduce。
- **本轮新增或修改**: scripts/r4_cost_probe.py、tests_ext/test_r4_cost_probe.py；冻结成本探测计划、预算提案、执行状态、任务日志和进度文档。复用原有已验证worker与超时执行器；原gosc/experiments/tests/results/LICENSE、既有A0协议及输出保持不变。
- **实际运行**: 全部计算在HPC n1 .venv Python3.11.15，UID8301880；2cores/24GiB，最大并发2，每worker数值线程1，无GPU工作。四场景×两方案×seeds9010–9012，共24条原始run_episode；单条120s、整批600s。

## 实测成本 [RUN]

| 场景 | GOSC平均worker墙钟(s/mission) | 冻结periodic平均worker墙钟(s/mission) | 每方案N |
|---|---:|---:|---:|
| search-K10 | 2.3852 | 0.4207 | 3 |
| search-clustered | 0.5381 | 0.3219 | 3 |
| rescue-W50 | 1.3331 | 0.4288 | 3 |
| rescue-snr-5 | 1.9785 | 0.4105 | 3 |

[RUN] 24/24执行完成，0程序失败、0超时、0中断；形成12组共同初始世界的两方案配对。登记总墙钟12.8199s，mission调度段12.3639s，不含本地同步。worker墙钟包括Python启动/导入，不是仿真slot数。此次最大单worker RSS56188KiB；前轮A0与本轮合并最大56588KiB。它们不是整个容器并行峰值，未测GPU峰值。

## 完整A1预算提案 [HYPOTHESIS]

[RUN→HYPOTHESIS] 采用前轮两W100场景的每arm N10，以及本轮其余四场景每arm N3。每个setting/arm都按未来100条等权计价；不能将本轮24条简单乘50，也不能用混合样本量加权。原始成本/公式由HPC计算并独立审计。

| 项目 | 提案 |
|---|---|
| 范围 | 六场景×GOSC/冻结periodic×100seeds=1200missions |
| seeds | 3000–3099，原作者冻结fresh复现；不用于训练/选参 |
| CPU并发 | 2workers，每worker数值线程1 |
| 预计调度墙钟 | 575.8s，约9.6min |
| 预计worker CPU总计 | 1024.7core-seconds，约17.1core-min |
| 用每组已观测最慢worker外推的墙钟 | 760.9s（仍非上界） |
| 建议整批硬上限 | 1860s=31min；单条120s |
| 原始episodes输出 | 估计12387143bytes（约12.4MB十进制）；原始数据预算37161430bytes（约37.2MB），不包含源码归档/其他日志 |
| RAM/GPU | 保留24GiB容器配额；GPU不需要 |

公式：sum(12组平均worker墙钟×100)/2×调度系数1.071039。系数取本轮与A0实测的较大值且不低于1。建议硬上限=max(均值外推×3,各组观测最大值外推)+120s，再向上取整到分钟。该缓冲是预设工程规则，不是统计置信上界。

不包含额外600条Genie、B候选搜索、C估值frontier、独立校准、LLM、训练、同步和审计时间。N3以及共享宿主争用限制外推可靠性；没有据成本挑选seed/方案或改论文目标。

## 测试、审计和负结果

- **测试与结果**: [RUN] hpc-r4-cost-tests-20261019：17passed，pytest2.04s；覆盖先前9项执行器测试和新增8项范围/冻结来源/预算权重/绝对CLI测试。
- **独立审计**: [RUN] hpc-r4-cost-audit-20261019：24唯一记录/12配对、全部Config与冻结点、24次启动/终止且最大并发2、12组成本均值和1200条等权预算、产物/原输入哈希均通过；审计新增仿真0条。
- **失败/负面证据**: 本轮程序失败0。所有未救全/未找全及误报等正常科学结果完整保留在原始result，不删除或重跑；本轮不从N3作任务性能或显著性结论。前轮A0首次0mission导入失败记录继续保留，未覆盖。
- **与原GOSC差异**: 无算法变化；新增有界成本探测与预算管理。
- **公平性与泄露检查**: 管理seeds9010–9012执行前无重复登记；不同于A0、作者校准/选择/fresh及预留新方法test。沿用冻结参数，无调参/训练/缓存LLM/liveLLM。
- **成本**: 见上表及每run manifest；助手token未计量，无外部模型/API成本。
- **可否进入下一阶段**: 成本探测Go；A1预算可审阅。P1整体验收与P2研究问题关卡仍未完成。
- **用户需要批准的下一步**: 当前四场景成本探测和预算工作已完成；1200条A1、新模型、LLM及训练未启动。本任务没有实现或暗中调用完整A1入口。

## 证据与精确命令

- 冻结计划：research/protocols/r4_cost_probe_v1.json，SHA256 `b97c7d042f077080e2ff392ba21a1dfaa2021c6faa1a7aa3304d0baa29ceb857`；保持制定时planned状态，实际完成状态单列于r4_cost_probe_execution_2026-10-19.json。
- 原始记录：research/sync/runs/hpc-r4-cost-probe-20261019/outputs/episodes.jsonl，附jobs/events/worker_logs/mission_status/environment/lock/input_integrity。
- HPC预算：同目录cost_probe_summary.json、cost_groups.csv、a1_budget.json；可审阅提案research/protocols/r4_a1_budget_proposal_2026-10-19.json。
- 审计：research/sync/runs/hpc-r4-cost-audit-20261019/outputs/cost_probe_audit.json。
- 精确命令：research/logs/r4-cost-probe-2026-10-19/experiment_manifest.json及对应run/manifest.json；测试JUnit、stdout/stderr、源码快照均留存。
- 最终两端运行文件/receipt哈希核验见本任务verification.json；源码上行另有同步manifest，运行完成与输出回传完成分开记录。
