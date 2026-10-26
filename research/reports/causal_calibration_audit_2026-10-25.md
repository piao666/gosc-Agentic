# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 修订后的GP-v2付费pose，在已冻结的任务、信道、强简单候选及通信/CPU实际账本约束下，是否有可进入正式验证的净收益？[RUN] 答案为当前协议 **No-Go**；下面的结论来自12个新校准world，不是252个独立样本。
- **已核验前人工作**：[PAPER] 本轮沿用既有`research/logs/GOSC_paper_code_map.md`，没有新增论文阅读或作者原文主张核验。作者原校准/cache生成链及部分历史数值差异仍是P1缺口。新Planner服务校准不填补这些缺口，也不证明真实LLM收益。
- **实际阅读源码**：[CODE] Git基线`47389eba9c6e2838139df3aa47863ab88634e97a`，dirty实验源码身份以原冻结SHA为准。`repro_causal_service.py`的make/missions/analyse；`audit_causal_service.py`的独立逐事件/CI/N复算；`audit_causal_frontier.py`的前沿、消融和停止条件核对。另核对`causal_paid_simulation.py::select`及`gosc/schemes.py::lagrangian_select`的age缩放/price关系，原gosc源码未改。
- **本轮新增或修改**：[CODE] 10月24日新增`causal_budget_amendment_2026-10-24.json`、`accept_causal_budget.py`与核验凭据，原blocked文件不改；10月25日执行独立账本/前沿审计，补充本报告、续接任务日志和最新状态入口。审计v2只澄清“不付费基线成本支持”与“付费消融支持”的范围、将成本“差值”措辞更正为“比值”，保留首版输出和相同统计。没有修改冻结方法/price/world/数据。
- **实际运行**：[RUN] `hpc-causal-independent-calibration-20261024`，21候选×12world=252任务，seed23000000–23000011、max_steps400、单任务60s/整轮批准1200s，447.369435s完成，exit0；全部252任务在400slot内完成。10月25日3个登记分析run通过（账本、前沿v1、措辞澄清v2），无重跑仿真。完整展开命令见本任务`actual_commands.json`及每run manifest。
- **测试与结果**：[RUN] 本轮没有重跑pytest；此前190不同合同/回归通过是10月24日证据。当前950,281条原始事件的UL/DL/共享CPU账本、重试下界/重播上限、world与候选矩阵、选参/探索性CI/六端点功效N独立复算通过；前沿与停止判定独立核对通过。不是外部独立研究组复现或额外N。
- **失败/负面证据**：[RUN] 原预算480s门槛的blocked记录保留。用户明确批准预算修订后，实际耗时小于1200s；不能倒推原预算关卡本应通过。校准无软件异常/任务超时，但科学No-Go：无联合实际成本支持、探索性增益区间跨0、规划N21907超200上限。age-only也给pose施加强简单对照压力，不能事后换主方法或加样本救结果。原自动审批服务用量错误中断了上次日志读取/审计，HPC独立运行正常结束，本轮审批恢复后续接，未绕过审批。
- **与原GOSC的差异**：[CODE] GP-v2是本项目的原生语义wire+付费UL/DL/共享CPU/2slot反馈下界/有界盲目重播模型，独立命名；保留原Planner与lagrangian_select，但不是作者旧wire精确复现。与GP-v1还使用不同新world；两版均值差异不能归因于单独服务修订。
- **公平性与泄露检查**：[RUN/CODE] 原21候选、price/周期/filter、CRN、world和方法源码SHA全部不变。原214个world指纹冻结、12新校准world执行；预留test24000000–24000199仍0次任务执行。所有候选初始world与首slot感知潜在场哈希相同；后续配对潜在场机制见冻结源码/既有合同，不把不同闭环轨迹写成每次接收事件相同。信息估值只读实际收到且有效的本地摘要。N/端点/停止规则不因结果改变。
- **成本**：[RUN] 校准单worker/数值线程1，HPC n1配额2CPU/24GiB，Python3.11.15；446.010013用户CPU秒+0.612064系统CPU秒，峰RSS66608KiB；runner指标包含Git管理子进程，非模型独占。账本审计6.652592s/峰RSS51944KiB；前沿v1 3.226462s/88344KiB，v2 2.072158s/88012KiB。0GPU/0新LLM/0新token调用/0训练。固定估值.001s、编解码.001s是场景假设，逻辑CPU预留与实测process/wall分报；不声称硬件部署净收益。
- **可否进入下一阶段**：当前GP-v2正式验证/扩N/训练 **No-Go**。本轮有界校准、独立审计和负结果交付可验收；没有可执行test N或正式test预算。规划21907仅是方差/功效近似的不可行值，不是已批准样本量。
- **用户需要批准的下一步**：本轮交付无需新批准。建议先静态审查“摘要是否能以更低成本传递”及“age缩放是否主要表现为动态价格”，提出新的可证伪协议后再决定是否研究；不得直接再扫参数/扩N/训练。Git提交/推送本轮未执行，也不由本轮校准授权自动推出。

## 核心结果

[RUN] 事前规则分别选择10个简单候选中的M0star、3个public price及3个pose price；最小平均截断完成时间，按UL+DL、case_id破同分。选中：periodic k8/eps0、public price1e-4、pose price1e-4。每项12world均完成。

| 选中方案 | 平均完成时间（slots） | 平均UL+DL channel uses | 平均逻辑CPU预留（s） | 平均实测mission process（s） |
|---|---:|---:|---:|---:|
| periodic k8/eps0 | 153.1667 | 37,255.92 | 1.1521 | 0.3248 |
| public-ToM price1e-4 | 152.8333 | 19,830.25 | 0.9312 | 4.8536 |
| paid-pose price1e-4 | 144.5000 | 59,857.75 | 3.2417 | 4.0948 |

| pose相对对照 | 平均提前slots（95%探索性CI） | 通信成本比（pose/control） | 逻辑CPU成本比 | 事前联合支持 |
|---|---:|---:|---:|---|
| periodic k8/eps0 | 8.6667 [-33.7521, 56.0000] | 1.606664 | 2.813743 | 未达到 |
| selected public-ToM | 8.3333 [-15.7500, 33.6687] | 3.018507 | 3.481296 | 未达到 |

这些CI使用同一校准数据选择配置及估计，不是选择校正后的确认性显著性检验。完整资源CI/均值/分位数在原`decision.json`和前沿审计JSON；不将均值更快写成科学成功。

CPU口径必须区分：pose的实测mission process为4.0948s，低于selected public的4.8536s、高于periodic的0.3248s；不能说所有CPU测量口径均增加。预设CPU关卡使用共享服务队列的逻辑预留秒（而非process_time），其固定场景参数不等于硬件实测。通信实际使用本身已不满足主要成本支持，即使不引用CPU关卡也不能从当前数据声称成本匹配的任务净收益。

## 成本前沿与消融

[RUN] 已绘制有限网格的真实观测点，不插值或外推成本支持。3个pose price对全部`arm=public`的不付费候选，通信与CPU均值比同时在[.95,1.05]内的配对点共 **0对**；这不包括paid-ignore/age/shuffle消融，不能宣称所有消融都无成本支持。

[RUN] 固定price1e-5的pose对照如下；任务gain=control完成时间-pose完成时间，成本是pose/control比。每行N=12，全部为探索性。

| 控制方案 | 平均gain slots（95%探索性CI） | 通信比 | 逻辑CPU比 | 联合成本支持 |
|---|---:|---:|---:|---|
| public | 1.8333 [-26.2500, 30.0833] | 2.203760 | 3.692677 | 无 |
| paid-ignore | 1.8333 [-26.2500, 30.0833] | 1.017547 | 1.048634 | 有 |
| age-only | -6.6667 [-28.7500, 12.8354] | 1.242500 | 1.078149 | 无 |
| shuffle | 4.5000 [-12.2500, 19.5833] | 0.943017 | 1.003335 | 无 |

paid-ignore说明“发送并计费”与“使用信息估值”可分开；该对照成本接近，但gain区间跨0，不支持此小样本下的信息净收益成立，也不证明信息绝对无效。闭环轨迹及消息事件可随策略变化，不能将此差值当纯信息因果效应。

[RUN] 事前age price1e-4候选的观测均值T129.5833、通信47,462.42、逻辑CPU2.80275，在本批样本三项均优于选中pose；这是更简单机制的压力，不改主比较/选择规则或转称新主方法已成功。[CODE/HYPOTHESIS] age将同一次决策所有候选价值乘正因子f，在声明目标`sum(value)-price*symbols`中代数等价于原价值搭配price/f；它可能通过动态价格抑制消息发挥作用。实际调度器含数值搜索/破同分，因此不由此声称所有有限精度轨迹精确等价，更不能直接将age结果归因于摘要信息。后续需另立协议识别，当前不运行。

## 功效与停止

[RUN] 事前六端点=2主比较×任务/通信/CPU，Bonferroni alpha .05/6，endpoint power .9666667；20000配对bootstrap用于探索性区间及保守SD规划。最小任务改善3slots、设计改善6slots；资源非劣比1.05、设计比1。主要规划值：

| 对照 | N任务 | N通信 | N逻辑CPU |
|---|---:|---:|---:|
| periodic k8/eps0 | 21,907 | 2,782 | 2,709 |
| selected public-ToM | 6,337 | 621 | 967 |

最大规划N21,907超过事前上限200；同时两主点不满足联合实际成本支持。因此不冻结可执行test N/预算，不执行预留test，不自动扩N。N=12的正态/boot规划近似不是保证功效的证明。旧GP-v1 No-Go也保留，两版不合并为N24证据。

## 原始证据与命令

HPC运行根目录`/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs/`，本地镜像为`E:/gosc/research/sync/runs/`：

1. `hpc-causal-budget-amendment-20261024/outputs/approved_budget.json`：原blocked/frozen/probe审计与用户批准核验，原frozen SHA `4acd18b105ecd2ca9fd41e0f7bc5213eb87728586970c846416547ea2bb5a0ee`，原blocked SHA `219ecd0c0a2fa732e8b57e997620cf798a08eca98e316f06920ccef83c6a7fb0`。
2. `hpc-causal-independent-calibration-20261024/outputs/`：`results.json`、`decision.json`、252份逐任务JSON和252份events JSONL；95万事件不是独立N。
3. `hpc-causal-calibration-ledger-audit-20261025/outputs/audit.json`：账本/选参/CI/N复算通过。
4. `hpc-causal-frontier-ablation-audit-20261025/outputs/`：首版前沿审计成功记录保留。
5. `hpc-causal-frontier-ablation-audit-v2-20261025/outputs/`：最终`frontier_audit.json`、`fair_comparison.md`、`discrete_frontier.png`和SVG；只修正支持对象/比值措辞，主要数值未改。
6. `hpc-causal-frontier-figure-20261025/outputs/`：读取已审计JSON重新绘制，避免中间面板选中点标签重叠及大数刻度拥挤；保留审计原图，不改变任何观测点。独立`figure_provenance.json`关联原审计SHA。

当前校准实际命令为登记入口后执行：`env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout 1200 {python} scripts/repro_causal_service.py --mode calibrate --frozen research/sync/runs/hpc-causal-world-freeze-20261024/outputs/frozen.json --budget research/sync/runs/hpc-causal-budget-amendment-20261024/outputs/approved_budget.json`。审计对应`audit_causal_service.py`及`audit_causal_frontier.py`，各120s上限；精确展开argv、注册config、seed、Git/source_sync和资源身份均保存于原manifest及任务`actual_commands.json`。

两端交付SHA及完整回传状态最终记录在`research/logs/causal-calibration-audit-2026-10-25/delivery.json`。历史10月24日“预算Pending/校准0次”报告保留当时事实，本报告与最新入口覆盖其当前状态；本轮尚未Git提交/推送。

[RUN] 最终receipt `research/sync/receipts/20261025T133502Z-8fa9fc.json`确认all_outputs_mirrored=true，覆盖全部校准/预算/两版审计及最终科研图。完整252任务与事件首次回传采用显式512MiB上限（新增169,195,728bytes），后续两个100MiB内补拉也均完成；HPC原件保留。最终图在HPC重绘2.101523s/峰RSS83872KiB，已本地目视核对3面板、图例、选中点标签与刻度可读，数据点未改。两版前沿JSON的summary/ablations/frontier/支持列表/选参/No-Go与规划N逐字段相同，轻量文件核验见任务日志；统计均在HPC执行。
