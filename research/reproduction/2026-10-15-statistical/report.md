# Research Task Report

**结论：5200次全新仿真完成；100/104项达到实际等价，4项证据不足，整体R4-S1仍为Pending。原shared/oracle已重现；新的receiver因子诊断未运行。**

- **Research Question / Hypothesis**：[HYPOTHESIS] 在固定Windows环境中，原始算法的任务/资源均值能否在修订协议的界限内重现，并支持继续receiver诊断？用户已批准统计复现。旧严格R4失败保留。
- **已核验前人工作**：[PAPER] 沿用D01 arXiv:2609.39477v1，p.8 Table VI与p.11私有信息对照等既有核验。本轮数字均来自新运行或保存JSON；没有新增文献/发表状态/创新性主张。
- **实际阅读源码**：[CODE] 原版387b493；冻结统计工具/协议dfd9475，receiver门控25c280b。核对`run_revision.experiments`、`validate_headline.select`、`plot_revision._interp_T/matched`、`campaign._job/r4_jobs`、`receiver_oracle`及统计代码。核心算法未改。
- **本轮新增或修改**：统计runner/同时区间/向量化前沿/绘图、统计和门控测试、协议/brief、未发送作者询问草稿、本目录证据和日志。新receiver runner已实现但未运行。所有原结果/缓存/源代码/Obsidian未覆盖。
- **实际运行**：[RUN] `statistical_reproduction prepare/run/analyze --run-id 2026-10-15-statistical-v1`；run使用4workers。frontier3400、原private600、冻结headline1200，共5200，全部重新执行、无复用。Planner，evaluation0–99、validation3000–3099；原配置及冻结操作点保持不变。
- **测试与结果**：[RUN] 完整99项通过（132.50s）；恒定小数方差保护补充后最终统计7项通过（0.72s）；receiver拒绝门控2项通过（0.12s）。没有把这些写成单次108项或102项全套测试。5200均成功，5000匹配已有参考字段，200有差异；104项的同时区间：100 equivalent、4 inconclusive、0 incompatible。全部N=100，20000次paired bootstrap；近似family95%，临界值q=3.14322。
- **失败/负面证据**：整体关卡未通过；4个区间越过预定5%边界。原joint oracle三个设置的任务收益CI均跨零，未确证稳定收益。导出脚本直接从.local运行时因PYTHONPATH缺失失败，设置仓库路径后成功；不是仿真或统计失败。原图长标签裁切、初版局部图图例遮挡已修复，旧图保留，新v2图已目视核验。
- **与原 GOSC 的差异**：新增采集/统计工具，原估值器/调度器/信道未改；没有新方法性能或论文贡献。修改的是明确披露的统计验收规则；原精确验收失败仍失败。
- **公平性与泄露检查**：未训练/调参/重新挑点/删除不利seed；共同seed按mission重采样，两个seed面板独立抽样。此前见过1399条旧记录和seed0探针，本协议是披露后的修订，不能冒称完全盲法预注册。固定eta oracle未计价，不能当等成本方法比较；前沿为插值，不能当每mission预算完全匹配。原calibration过程、LLM cached/live均未重新运行。
- **成本**：[RUN] 仿真墙钟1455.827s（24.26min），4workers，每worker1数值线程；raw JSONL为8,912,773字节。测试/准备/分析/绘图另计。没有GPU、模型下载、依赖变更、付费API或LLM调用。CPU/RAM峰值、真实序列化字节、独立packet-success计数与估值器分项耗时未测，不伪造；各组bits/UL/DL/latency见group_statistics.json。
- **可否进入下一阶段**：按冻结协议为 **Pending/No-Go**；receiver数据目录未创建。100/104不能改写成“整体通过”，4项不确定不能写成“明确不一致”或“没有差异”。
- **用户需要批准的下一步**：建议审阅`receiver_scope_proposal.md`：只在保存字段已精确复现的ToM路径上做限定因果诊断，throughput问题继续隔离保留；这是新的准入范围，未经确认不执行。作者询问草稿仍未发送。

## 1. 4项不确定结果

差值定义fresh−author；区间为104项同时95%区间，单位均为作者均值的百分比。所有点估计在±5%内，但区间没有完全进入界限。

| Throughput操作点 | 指标 | 参考均值 | fresh均值 | 差异% | 同时区间% |
|---|---|---:|---:|---:|---|
| eta0.0 | completion slots | 68.72 | 71.26 | +3.70 | [-3.76, +11.15] |
| eta0.0 | UL uses | 26605.88 | 27098.70 | +1.85 | [-1.97, +5.67] |
| eta0.1 | completion slots | 69.58 | 71.07 | +2.14 | [-4.00, +8.29] |
| eta0.3 | completion slots | 70.48 | 71.12 | +0.91 | [-5.68, +7.49] |

精确差异集中于bits eta0/0.1/0.3（73/68/56条）与AoI eta0/0.003（2/1条），共200条、800个字段差异。只有77条completion_time不同；不能把所有字段变化都说成任务结果变化。原private600条、headline1200条保存字段全部匹配；headline参考仅含task与symbols，不能声称历史完整curve或所有未保存字段已匹配。

每点现有历史参考只有100个seed。重复执行这100个seed或增加bootstrap次数不能当作更多独立样本；扩展配对N需要相应新增作者参考或另设跨环境独立研究，不能把新增ours单边seed直接混入当前配对检验。

尾部例子：bits eta0.3 seed51：99→217slots；eta0 seed45：51→156；eta0.1 seed87：188→111。正负变化均保留。它们说明平均值相近仍可伴随较大轨迹分歧；没有作者逐时隙trace，不能断言这些特定尾部变化全由某一次一ULP变化造成。后者仍是[HYPOTHESIS]。全量数据保留，`tail_examples.csv`只作诊断示例。

## 2. 原shared/joint-oracle对照已经fresh重现

每设置100个paired seeds。收益定义shared−oracle完成时间，正值表示oracle更快；下列为未校正95%CI，Bonferroni3同时口径另见JSON。

这些CI使用本轮冻结的20000次bootstrap和统计seed20261015；它们不必与作者不同重采样口径的显示区间逐字一致。逐seed保存指标一致与CI字面一致是两件事。

| 设置 | shared均值 | oracle均值 | 收益slots [95%CI] | oracle额外UL uses |
|---|---:|---:|---|---:|
| default | 72.89 | 69.77 | +3.12 [-4.38, 10.51] | +498.96 |
| W50 | 78.41 | 73.46 | +4.95 [-2.76, 12.64] | +627.83 |
| snr-5 | 97.66 | 105.03 | -7.37 [-18.29, 3.47] | +112.03 |

三个任务CI均跨零，方向也不一致。**没有证据支持joint oracle在三设置稳定改善任务质量**；也不能由此证明receiver状态没有价值。W50的额外UL uses之Bonferroni3区间约[4.23,1267.96]，访问私有信息不自动带来净成本收益。该oracle是原作者联合开放私有证据和位置的特权分析，不等于新2×2拆分因子实验。

## 3. 冻结验证与前沿的边界

六设置的原GOSC/periodic保存task与symbols逐seed均匹配。periodic/GOSC的UL均值比及95%CI：search-W100 1.188[1.109,1.274]；K10 5.915[5.570,6.278]；clustered 1.280[1.144,1.431]；rescue-W100 1.778[1.632,1.933]；W50 2.599[2.429,2.778]；snr-5 8.524[7.869,9.205]。这些是原方法结果的重现，不是我们的改进。

periodic的search-W100均值76.22略高于target76.1875，K10为57.84高于57.775；原保存数据也如此。不得将它们写成严格满足全部目标。六组任务效果CI和资源比均另存于`supplemental_contrasts.json`。

W100的5000/10000/20000uses插值前沿已重建；AoI/throughput对ToM的有效预算比较CI均跨零，不能由本轮声称复杂ToM稳定优于这些简单规则。若某规则范围不覆盖预算则标记不可比较，不外推；例如10k AoI有效bootstrap为19769/20000，其余无效样本明确计数。不能偷偷删除后宣称全部重采样有效。

## 4. 证据与重建

- `experiment_manifest.json`：环境、commit、split、命令、哈希、运行成本、Pending状态。
- `agreement.csv/json`：全部104项和区间、分类、N、归一化界限。
- `group_statistics.json`：52组全部可用标量指标的均值、分位数及描述性区间。
- `discrepancy_groups.csv`、`tail_examples.csv`：差异归属与尾部示例；全量逐字段差异在raw根的`r4-statistical/exact_discrepancies.csv`。
- `supplemental_contrasts.json`、`frontier_statistics.json`：原对照、前沿及有效重采样数。
- `unresolved_intervals_v2.png/pdf`、`agreement_reviewed_v2.png`：已目视检查，无原图裁切/图例遮挡。
- 完整raw/log/config/source：`E:\gosc-agentic-teams\.local\reproduction\2026-10-15-statistical-v1\`；原v1与mismatch-v2未覆盖。

原始文件76项复核无改变；没有对外发布/联系作者。工作结束停止，等待新的范围确认。
