# R4 多 seed 复现预登记协议 v1

最新执行状态（2026-10-19）：A1已完成1200条、600配对，28测试和独立审计通过，主指标/UL逐seed匹配作者记录；见 `r4_a1_execution_2026-10-19.json` 和 `../reproduction/r4_a1_report_2026-10-19.md`。下文较早的A1未执行描述仅表示当时预登记/历史状态。B/C与训练未执行。

执行更新（2026-10-19）：**R4-A0已实际完成60条mission**；9项执行器测试和独立数据审计通过。当前状态见 `r4_a0_execution_2026-10-19.json`，报告见 `../reproduction/r4_a0_report_2026-10-19.md`。四个补充场景的24条成本探测及独立审计也已完成；A1预算提案见 `r4_a1_budget_proposal_2026-10-19.json`，预计575.8s、建议上限1860s。A1/B/C未执行。

下方保留预登记设计及其制定时状态；原 `r4_plan_v1.json` 不改写。

制定：2026-10-19；**状态：planned / 未执行**。本轮仅完成协议与保存数据预检，不将它记作新多seed结果。现有环境/R1/R2/R3证据与论文审计见 research/reproduction/，完整计划参数为 r4_plan_v1.json。

## 目标与两条复现轨道

[HYPOTHESIS] 在不改原算法/参数/任务/无线模型的情况下，重新执行已冻结工作点，检查 GOSC 与最强已选 periodic 的任务/资源结果能否复现。随后才比较 ToM/TV/bits/AoI 的成本匹配 frontier。不是验证新方法提升，不训练任何模型。

- **A：严格保存数据口径**。TableIV已冻结的六组GOSC/periodic点，原始搜索候选37、救援38；保留论文与代码的候选差异。执行后写“复现已发布冻结点”，不能说已独立重新搜索了38候选全族。
- **B：38候选覆盖敏感性**。给搜索场景补上unfiltered rate-aware k=16；这是预先命名的候选覆盖扩展，不覆盖A结果，也不追溯修改作者结果。先在选择集0–99重新比较候选，冻结后再用3000–3099评估；不能根据fresh结果挑A或B中较好的一条报告。
- **C：估值器公平比较**。固定representation/filter/scheduler/channel与配对seeds，以同radio-cost budget比较ToM、belief divergence、throughput、AoI，不用相同eta强行当作公平。C依赖A的执行/资源核验，不在本轮启动。

## 先执行的有界 pilot（A0）

预留管理seed **9000–9009**（未在本项目已登记run中使用；执行前再核对ledger，不能据此保证项目外全球未用）。仅用于流程/成本核验，不调参、不做主要显著性结论。固定2场景×3arms×10seeds=**60条mission**：

| 场景 | Config覆盖 | GOSC | 冻结periodic | 第三个arm |
|---|---|---|---|---|
| search-W100 | 默认search，K6、W100、SNR5、400slot | eta=1e-5 | sem_raf，k=4，filter_eps=0.02 | genie，仅理想通信参考 |
| rescue-W100 | task=rescue，deadline_min=60，deadline_max=180，其余默认 | eta=1e-4 | sem_ras，k=2，filter_eps=1.0 | genie，仅理想通信参考 |

全部调用原 `gosc.run_episode`，使用同一seed的世界/传感/信道/规划RNG分流。保存每条完整Config和原始result，不能只保留均值。Genie是额外上下文，不用于对fresh数据重新设目标；目标沿用作者冻结参考。救援主终点是saved_fraction，不能拿“找全人”的completed冒充全部救援成功。

资源：HPC项目 .venv Python3.11.15，workers<=2，BLAS/OMP<=2，当前cgroup 24GiB；不需要GPU或模型。单mission预算120s、campaign上限20min；60条预计约1–15min，依据当前唯一实测默认GOSC约1.04s/条，其他scheme/救援耗时尚未实测，须以pilot修正。超限保留全部任务状态与输出，补齐同seed比较组后再汇总，不删除失败seed。

pilot验收：60条计划记录都有 completed/failed/interrupted/timeout；零重复key；每个场景3arms有相同seed集合；Config、模型/缓存、代码/依赖锁、资源、命令和逐seed输出可追溯；输入哈希不变；产物回传验证。任务未完成、未达deadline及误报按原结果保留，不能把这些正常科学结果一律当执行器崩溃。只有程序异常/结构损坏才判执行失败。N=10不作为发表性能主结果。

## 严格完整阶段 A1（尚未执行）

冻结点：

| 场景 | GOSC eta | periodic | k | theta/filter |
|---|---|---|---|---|
| search-W100 | 1e-5 | sem_raf | 4 | 0.02 |
| search-K10 | 3e-4 | sem_ras | 4 | 0.05 |
| search-clustered | 3e-5 | sem_ras | 4 | 0.2 |
| rescue-W100 | 1e-4 | sem_ras | 2 | 1.0 |
| rescue-W50 | 1e-4 | sem_ras | 2 | 1.0 |
| rescue-snr-5 | 1e-4 | sem_ras | 2 | 1.0 |

复现fresh划分 **3000–3099**，六场景×两比较方案=1200条；若逐条重跑genie上下文再加600条，总计1800。此前单任务seed3000已见过，作者保存数据也已公开，因此这是已知配置的独立重新执行，不宣称新的未见测试集。不得用这批seed训练或选择新模型。新的方法开发须另立训练/验证/test划分与冻结协议；可先预留4000–4099但在新RQ审定前不使用。

依据pilot测量估算完整运行成本。粗估CPU任务为1–4小时量级（并非测量承诺），不把8核M1 README时长直接当2核容器时长。启动前列出实际job数量、预估墙钟/CPU与输出体积，按实际授权范围执行；当前任务仅预登记，不自动启动A1/B/C。

## 参数选择与公平比较

1. 校准 seeds1000–1079保留作者语义；本轮没有重跑校准搜索，也没有证据证明每个历史校准步骤已独立复现。
2. 作者evaluation 0–99用于候选选择，fresh3000–3099用于冻结后验证。Pilot9000–9009不参与选price/k/theta；也不以pilot效果重新定义任务。
3. A1直接使用表XIII已冻结点，并记录历史来源；B重新枚举时必须存选择集每个candidate每个seed，而非只留winner。B中38=5 unfiltered+5 filtered+28 suppressing。
4. C的search price网格按原源码不同单位固定：ToM `[0,3e-6,1e-5,3e-5,1e-4,3e-4,1e-3]`；TV `[0,1e-4,3e-4,1e-3,3e-3,1e-2,3e-2]`；bits `[0,0.1,0.3,1,2,3,4]`；AoI `[0,0.003,0.01,0.03,0.1,0.3,1]`。先以同seed得到frontier，预设预算5k/10k/20k仅在共同覆盖区比较，超范围标n/a，不外推。
5. 每agent W相同只说明上限相同，不表示每mission实际资源相同。A/B比较共同task target下的cost；C比较共同cost下的task，分开报告。
6. 原普通run_episode仅用于无额外H的TableIV复现；完整总成本/共享上行另用run_realistic并包含ULdata/request与DLbroadcast/HARQ/grant/price，不能把其指标与普通dl_symbols混拼成同口径。

## 统计与报告预设

- 原始每seed：完成/时限、completion_time、saved_fraction/lost（救援）、found、false_declarations、bits、symbols、dl_symbols；真实runtime、配置/commit/dirty与输入/lock哈希；失败/超时也保留。
- A主表按论文方向：outcome_diff=GOSC−periodic（search负更好、rescue正更好）；资源ratio=mean(periodic symbols)/mean(GOSC symbols)，不是逐seed ratio的均值。分别报告target margin、两方案是否达标与CI；任何方案未达标时，不只凭ratio>1宣称效率优势。
- 配对seed bootstrap主结果4000次、固定分析RNGseed0，95%percentile CI；均值±CI按作者脚本的1.96*sd/sqrt(n)另列，不能混用两者。N、cap400slot和失败率明确报告，CI跨0不等于等效。
- C matched-budget沿用原log-cost lower-envelope插值与**10000**次配对bootstrap，记录有效resample数及不可插值比例。简值15项比较保留Bonferroni。任何新增主要比较家族须预先列数量，额外同时区间/多重校正单列，不改原论文复现栏。
- 不根据结果提前停止收集、挑seed或选择最好setting。若中断先标partial，补齐再报告；保留所有负结果与差异原因。

## 执行入口与保护

所有计算经 `scripts/hpc_runs.py launch/run`，每个phase独立run_id。输出只能进入当次run/outputs，内部每mission含完整key；源码上行不能覆盖HPC运行事实。回传后检查receipt，超出100MiB上限的产物显式记录。

当前 **r4_preflight.py仅检查保存候选和seed元数据，绝不执行mission**。本协议的pilot执行器尚未编写/验证，不能把该预检命令当作R4仿真命令。执行器应按r4_plan_v1.json展开60个任务，限制workers/超时并保存逐seed原始记录后再启动；不得直接调用原 `validate_headline.main()` 的硬编码Pool(8)或写回results。现有run_revision默认workers6、其他入口Pool4/8也不能原样用于当前2核配额。

## 当前关卡

R1、R2保存数据重建及论文印刷表审计（含显式显示/候选差异）、R3已具备证据。A0协议明确；A0/A1/B/C均未执行。P1整体仍未完成，R5 cached/live LLM与完整独立校准仍缺；P2研究问题/文献审查尚未过关，不启动M0/M1训练。
