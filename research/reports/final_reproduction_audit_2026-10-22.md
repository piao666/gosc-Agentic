# 完整续跑回传、总审计与缓存差异结案报告（2026-10-22）

## 1. 当前结论与验收边界

[RUN] 已完成登记产物回传与总审计、作者缓存覆盖诊断、新缓存回放验证，以及缺失LLM表格补齐。科学复验仍是 **部分通过 / 存在材料和历史一致性缺口**，不能标为“全部复现通过”，不能据此启动新方法训练或声称创新成立。

[RUN] 原续跑队列于北京时间2026-10-20 11:36启动、2026-10-21 09:58结束。六个此前执行阶段加本轮剩余17阶段，共23阶段；22个正常退出，作者缓存回放阶段失败。父队列退出0表示完成可用程序并登记缺口，不能替代各阶段科学验收。本轮没有重写旧失败、原作者结果或缓存。

[CODE] 当前HEAD为876fc523b113b3b65e19f0b730f1573ccc2ee17f；作者上游基准387b49389385b51c275dc5a22ec1672087edda1d。源码保护检查及审计均未发现gosc/experiments/tests/results/LICENSE的tracked修改。现有用户与此前任务的未提交研究文件保留，没有commit/push/reset/checkout/clean。

## 2. 回传与完整性证据

[RUN] 主队列及其相关登记文件首先完成624文件回传，回执为 `research/sync/receipts/20261022T025244Z-ordered-6f7572.json`，SHA-256为83e576f116d4b704043ee761f55d049e5f4fec95dea7bf478e2a01b69ce1c468。该批新增下载274,438,512 bytes；此前已下载文件复核哈希后复用。不是只下载summary。

[RUN] HPC总审计独立核验23个子阶段的403个登记产物（458,192,989 bytes），父队列产物与冻结前缀状态/索引另查，未发现缺失、哈希变化或保护输入变化。后续完整pull涵盖所有登记run与新增审计、补表输出，最终文件数/回执/两端哈希见 [delivery.json](../logs/final-audit-2026-10-22/delivery.json)。运行状态与回传完整性分开判定。

[RUN] 本轮新生成的三个LLM响应缓存原先位于被源码同步排除的.local目录，现已复制为 `hpc-cache-gap-probe-20261022/outputs/new_live_cache_snapshot/`，逐文件校验并纳入run artifact清单及回传。作者公开缓存原件未改，模型权重与私人PDF不在产物回传范围内。

## 3. 本轮真实执行与成本

[RUN] 全部分析/回放在HPC执行：UID8301880，项目Python3.11.15，2CPU配额、24GiB RAM；数值线程1，不超过2并发。本轮未下载依赖或模型，未调用Ollama/收费API，未训练。

| 登记run | 工作 | 退出 | 墙钟 |
|---|---|---|---|
| hpc-post-campaign-audit-20261022 | 全阶段产物/LLM传输审计＋两类只读缓存回放 | 0 | 238.37 s |
| hpc-cache-gap-probe-20261022 | 三个已有NumPy环境×五种排序模式；新缓存快照 | 0 | 6.70 s |
| hpc-final-coverage-audit-20261022 | 初版逐任务/覆盖审计 | 0，但压缩参考路径识别不足，已被v2替代 | 6.91 s |
| hpc-final-coverage-audit-v2-20261022 | 含.gz参考的最终独立覆盖与账本审计 | 0 | 16.14 s |
| hpc-live-llm-tables-20261022 | 原生统计函数补两张LLM表、组装完整图表集 | 0 | 2.90 s |

[RUN] 缓存审计包含1140次原有mission配置的回放尝试：作者缓存570次、本轮新缓存570次；750次完成，390次在缺key处中止。另有15次首失败任务的受限诊断变体，均在首缺key处中止。它们使用原有配置/seed，不计作新的独立样本，不是重新运行整个多seed主实验。除这些明确登记的回放外，没有新增仿真/推理；覆盖审计和补表只分析已有输出。

[RUN] 没有为纯文档变化追加单元测试；上述独立审计直接执行了哈希、身份/覆盖、原始账本、缓存不可变性和回放指标校验。未将旧测试次数改写为本轮通过次数。

## 4. 独立账本与比较覆盖复核

[RUN] 最终审计从原始pool结果和worker事件流核对234,420条job记录：索引完整且唯一、start/terminal与结果PID一致、全部完成、每pool并发不超过2。这里包含仿真和诊断job，**不是234,420个独立mission**；跨阶段重复seed/配置不能累加独立N。

[RUN] 使用当前显式身份比较器重新计算38份产物比较。浮点数采用比较器原定rel/abs tolerance 1e-10；“0差异”仅指该口径覆盖的保存指标，不代表逐时隙轨迹或所有未保存字段相同。结构化summary比较与逐记录指标比较分开；没有原参考的派生产物不列为通过。

[RUN] 旧选参报告有两项共同key为0却写matching_common_keys，原记录保留，新结论另存：
- rev_genie_ref：重新覆盖300/300，保存指标0差异。
- 选参轨道rev_rescue：共同3300条、18差异，实际额外9900、参考未覆盖4200；不能说整份7500参考已匹配。独立revision-rest轨道完整7500条的结果另列，不能混为同一配置全集。
- 本轮覆盖审计v1遗漏.gz参考路径，对noise/overhead/shared标记缺参考；v2已识别压缩原件并重新比较，v1保留，不作为最终验收依据。

[RUN] 重点结果：

| 项目 | 执行量/覆盖 | 科学核对结果 |
|---|---|---|
| 参数选择 | 26,700次；267候选配置 | 26,100条有保存参考，22条主要/通信指标差异；12个冻结点一致；不是原1000–1079校准流程 |
| 已选点fresh | 1,200次 | 保存验证产物匹配；periodic在search-W100与K10略未达冻结目标，不能称全部达标 |
| C frontier | 6,800共同记录 | 479条差异 |
| C where | 5,000共同记录 | 364条差异 |
| C belief divergence | 1,400共同记录 | 0差异 |
| noise | 23,400共同记录 | 40条差异；作者另575条未覆盖 |
| overhead | 82,600共同记录 | 168条差异 |
| shared | 18,400共同记录 | 完整覆盖、0差异 |
| radio fresh | 10,000次 | noise验证summary匹配；shared/overhead验证summary有差异 |
| main sweeps | 12,500次pool任务 | default83/900差异；agents、SNR、budget、Pareto保存指标匹配 |
| revision rest | 42,100次pool任务 | ablation326/1000、rescue489/7500、filtered_periodic2/3500、suppress_periodic4/19600差异；private、Genie参考、downlink、FBL、rate-aware匹配 |
| joint | 1,800共同记录 | 完整覆盖、0差异 |
| scheduler / theory | 各60个job | 对应结构化产物匹配 |
| value fidelity | 300个job，914条可配对观测 | 780条观测差异；不是780个失败mission |
| fidelity analysis | 已执行 | 派生分析产物存在差异 |
| 38候选敏感性 | 增补3个search候选×100seed=300次 | 复用原候选数据重新选择；fresh再执行1200次，冻结点与主轨一致；不当作独立新N |
| Genie fresh | 600次，六设置 | 完成；Genie是理想通信参考，不是任务最优上界 |

[RUN] 完整38项身份、覆盖、差异字段分布见 `hpc-final-coverage-audit-v2-20261022/outputs/recomputed_comparison_inventory.json`。未对差异进行四舍五入抹平、删seed或偷偷挑选替代点。

## 5. 真实LLM审计与任务/资源结果

[RUN] 570条任务由180条Planner对照与390条含LLM任务构成；后者分Qwen2.5-3B 180条、Llama3.2-3B 150条、Qwen2.5-7B 60条。三个模型的真实HTTP调用共28,300次，另1429次新运行内部缓存命中。服务返回格式错误0、HTTP失败0、Planner fallback计数0。这里没有把Planner对照冒称LLM任务，也没有把缓存命中算新推理。

[RUN] 服务端记录输入tokens10,560,037、输出tokens272,404。token统计按实际HTTP attempt，不能凭cache hit反推未记录token；时延含服务加载等成本，不是纯GPU kernel耗时。没有GPU峰值显存、实际线缆字节或能耗测量，不能伪造补齐。

| 模型 | 实际HTTP次数 | 输入tokens | 输出tokens | 平均延迟s | p95延迟s |
|---|---:|---:|---:|---:|---:|
| qwen2.5:3b | 13116 | 5040721 | 126406 | 1.422 | 1.725 |
| llama3.2:3b | 10411 | 3685494 | 93699 | 0.689 | 0.738 |
| qwen2.5:7b | 4773 | 1833822 | 52299 | 1.862 | 2.727 |

[RUN] 570条任务与作者保存记录有412条至少一个核对字段不同，其中390条含LLM任务全部有差异，另外22条来自Planner/gosc_bits；后者不能归因模型随机性。原生质量/通信/配对统计、每组seed列表分别见 `llm_mission_groups.json` 和新补表的 `llm_native_statistics.json`。

[RUN] 使用原生extended分析、共同seed配对的结果如下。dT=periodic完成时间−GOSC完成时间，正值表示GOSC更快；区间沿用原脚本的未做多重比较校正95%bootstrap，不重新挑选统计口径：

| 队伍 | 配对N | dT slots [95%CI] | periodic/GOSC平均UL uses比 |
|---|---|---|---|
| Planner | 50 | -3.68 [-14.12, 7.00] | 2.98 |
| Qwen2.5-3B混合 | 50 | -10.00 [-24.58, 2.88] | 2.82 |
| Llama3.2-3B混合 | 50 | +20.42 [7.54, 33.70] | 3.64 |
| Qwen2.5-7B混合 | 30 | -9.33 [-29.97, 11.27] | 2.92 |

[RUN] 本轮可见通信量降低，但Qwen两组任务时间区间跨零，不能声称所有模型都稳定改善任务效果；Llama的单一运行/量化build结果也不等于跨模型通用结论。相同eta或表中资源比不等于等资源预算，Genie也不承担真实无线开销。LLM推理token/时延应与任务资源一起披露。

## 6. 缓存缺口与差异归因

[RUN] 三个作者公开缓存共27,732条键/响应；本轮检查未发现无效行、重复key或冲突响应。正式失败运行使用的隔离副本与项目原件SHA-256一致，故不是本地漏复制某个缓存文件。初次缓存阶段在index3停止，原失败日志完整保留。

[RUN] 逐mission只读覆盖诊断：180条Planner对照完成，390条含LLM任务全部缺key；缺失的首次key合并后130个。任务遇缺key立即停止，没有用HTTP、近似prompt匹配或Planner结果补全。作者cache只保存hash→choice，缺少原prompt文本、模型/依赖生成环境与完整逐时隙trace，不能从hash反演作者原始输入。

[RUN] 对第一条失败任务mixed/sem/seed0，在NumPy2.4.6、1.26.4、2.2.6中分别采用default/stable/quicksort/heapsort/mergesort，共15个诊断变体。排序确实改变部分首prompt/hash，但15个均未命中；不能称“换一个NumPy版本就修好了”。排序变体只用于诊断，不作为正式复现成功或修改基线的依据。

[CODE] 本地Git历史表明初始公开提交至最新上游的llm_agent.py与run_llm.py未改；缓存则追加了Llama和7B记录，Qwen3B文件未变。这不提供发布前缓存生成过程，也不排除发布前prompt/配置变化。因此本轮只能判定 **已公开缓存不覆盖当前已核验环境生成的首prompt键，原因未完全闭环**，不能进一步断言缓存整体损坏、作者造假或与平台无关。

[RUN] 相对地，本轮真实推理生成的新缓存在同一冻结环境中可离线回放570/570；预设任务/通信/LLM指标0差异，HTTP调用0，缓存原件不变。这确认本轮输出可重放，但不等于恢复作者响应，也不是再次采样模型。两个缓存轨道保留不同身份与哈希。

[HYPOTHESIS] 数值/候选排序、发布前提示/参数、依赖与模型build均可能影响历史生成链。已定位frontier/where第243次调度的1ULP敏感性只解释局部机制，不能自动解释本轮全部差异。无作者相应环境和trace时不继续盲目换版本或将大规模重跑当成原因证明。[前轮调查](upstream_gap_investigation_2026-10-20.md) 的限定仍适用。

## 7. 最终图表补齐与限制

[RUN] 原final-replot虽正常退出，仅产生17PDF/16TeX：cached失败后其隔离results中没有llm_mixed.jsonl，plot.llm_table返回None，plot_realistic.main捕获FileNotFound并skip llm。退出0不能证明论文所有表已生成。

[RUN] 已使用原版 `experiments.plot.llm_table` 和 `experiments.plot_realistic.llm`，只重定向输入/输出路径，对已核验的真实推理结果生成两张缺表。新完整集合位于 `hpc-live-llm-tables-20261022/outputs/figures/`，含17PDF/18TeX；LLM宏合并入复制的numbers.tex，摘要另存summaries。原17PDF逐字节复制，原figure目录和原作者结果不变；新表明确来自本轮推理，不能冒称作者表格数值。

[RUN] 原17PDF/16TeX的内容清单中未检测到n/e或nan占位；unsupported budget的“--”不自动算错误。此次审计没有进行逐图目视/版面验收，HPC未找到pdftoppm/pdfinfo/gs/mutool；不把文件存在或哈希检查写成视觉质量验收。新表为TeX片段，并非新编译的完整论文PDF。

## 8. 本轮产物、命令与版本

[CODE] 新增管理/分析脚本：
- scripts/repro_post_audit.py：不可变产物、传输、模型分组、两类只读cache回放。
- scripts/repro_cache_probe.py：15个受限诊断、新缓存快照。
- scripts/repro_coverage_audit.py：独立原始job/event账本与.gz参考覆盖比较；v2运行是最终版本。
- scripts/repro_llm_tables.py：原生LLM统计、表格与完整图表集补齐。

[RUN] 实际命令类别：只读git status/rev-parse/remote/diff/log；scripts/sync_hpc.py正常清单同步；scripts/hpc_runs.py run登记上述五条分析；scripts/hpc_runs.py pull --max-bytes 1073741824完整回传。每条实际展开命令、Python路径、源码sync ID/SHA、环境、时间、退出码和输出哈希，以run manifest/status/artifacts为准。

[RUN] 最新保护检查、产物回执与报告哈希索引见本轮日志目录；Open-Questions、AGENTS最新进度入口及project_status/next_steps已更新，历史快照与旧失败保留。本报告不替代原始run，后续需要读取精确数据时回到其manifest与outputs。

## 9. 下一步与关卡

1. 已结束的主队列不再后台运行；报告及所有新增登记产物完成两端核验后收尾。
2. P1标记“可用程序已执行，精确历史一致性/作者缓存/原校准过程仍有缺口”。已匹配部分可引用，未知部分单列；不将执行成功、缓存可重放或1ULP局部证据合并写成整个P1通过。
3. 缓存若要恢复作者轨道，需要能覆盖这些首prompt的原缓存/生成prompt与环境、模型build/参数及trace。用户已说明作者仓库为唯一材料来源，不重复索要未有文件，不通过新响应填入作者缓存。
4. 本轮不启动新方法训练。进入新的研究试验前，应基于可复现子集冻结独立校准/估值成本/强简单基线与拒绝条件；现有RQ和Gap Matrix仍是假设资产。
