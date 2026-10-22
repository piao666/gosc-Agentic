# Research Task Report

**结论：已确认吞吐量调度存在浮点敏感的离散选择；作者保存的 83-slot 轨迹仍未复现。R4 未通过，TeamModel 接收端诊断未运行。**

- **Research Question / Hypothesis**：[HYPOTHESIS] 追溯 `gosc_bits/W100/eta0/seed0` 的生成环境、源码和数值轨迹；用户已批准。本轮不开发新估值器。
- **已核验前人工作**：[PAPER] 沿用前轮 D01（arXiv:2609.39477v1）第 8 页表 VI 等核验；本轮无新增论文事实。[CODE] 单 seed 参考来自原版 `results/rev_frontier.json`，不是论文中的单 seed 表格。
- **实际阅读源码**：[CODE] 原版 `387b49389385b51c275dc5a22ec1672087edda1d`，工作起点 `0f10fe7cbfb67d7c18102413483667d4c16d2977`，启动 clean。读取 `run_revision.py:experiments/_job`、`schemes.py:lagrangian_select/GOSC`、`realistic.py:RealisticGOSC`、`channel.py`、`simulator.py`、`environment.py`、`agent.py`、`belief.py`、`config.py`、`test_realistic.py` 与既有历史 blob 证据。未获得作者生成时的环境 manifest 或未公开源码。
- **本轮新增或修改**：三个工具 `experiments_ext/diagnose_arithmetic.py`、`audit_arithmetic_trace.py`、`finalize_mismatch.py`，本目录、brief/日志及总报告索引；原始模块、实验、测试、结果、缓存、lock、LICENSE、Obsidian 均未改。
- **实际运行**：[RUN] 14 个纯 Planner mission，均为上述配置与 seed0；Windows/Linux、NumPy 1.x/2.x、base/realistic、标量算术与 Linux SIMD 探针。22 条实际调用及失败见 `command_ledger.json`。Docker 使用已有镜像，关闭网络、限制 1 CPU/1GB、原源码只读挂载；Linux wheel 离线安装到隔离目录。
- **测试与结果**：[RUN] 现有完整 suite **93 passed in 45.32s**；pip check、主环境 lock 的16包、76受保护文件哈希通过；Linux archive 的14个 gosc 源文件与 checkout 相同。新增工具由实际运行/回放断言/AST验证，没有虚构新增单元测试。14个输出均未匹配作者保存记录。只有1个独立任务 seed，不估计 CI，不把环境变体当独立样本。
- **失败/负面证据**：兼容矩阵未恢复作者结果；API镜像缺 NumPy，未运行实验；一次 pip download 同时指定两个排他版本被拒绝，分开下载成功。历史失败和本轮全部输出均保留。
- **与原 GOSC 的差异**：仅研究工具；power-math/scalar-math 是进程内数值干预，不能标为原版复现或改进算法。离线枚举不接入在线调度。
- **公平性与泄露检查**：无训练/调参/任务或 seed 划分变更；无 receiver oracle 运行；未放宽验收；未发送消息或公开发布。数值敏感性不证明 TeamModel 缺陷，不证明或推翻总体统计结论。
- **成本**：[RUN] 14次 sim.run 墙钟合计约3.791s，tests45.32s；安装/容器启动/网络等待/分析另计，总wall/CPU峰值未测。保留3个wheel共51,048,682字节，UV另有缓存下载，实际网络量未测。主 .venv 不变；零GPU/模型下载/付费API/LLM调用，token未计量。
- **可否进入下一阶段**：**No-Go**。历史结果具体来源未闭环，5200-run R4未恢复，1200-run receiver诊断未运行。
- **用户需要批准的下一步**：优先获取作者 Python/NumPy构建、CPU/SIMD、OS、源码/配置与seed0轨迹；现有作者询问草稿未发送。如转为固定环境的统计复现，先批准新的R4验收协议，保留原精确验收失败。

## 兼容矩阵

作者行来自[CODE]保存JSON，其他为[RUN]。均为seed0；单位slots / uplink data channel uses / payload bits；完整14行见 `compatibility_matrix.csv`。

| 环境/路径 | completion_time | symbols | bits |
|---|---:|---:|---:|
| 作者保存JSON | 83 | 31011 | 23468 |
| Windows Python3.12.10 / NumPy2.5.3 | 76 | 29596 | 22109 |
| Windows Python3.12.10 / NumPy2.4.6 | 76 | 29596 | 22109 |
| Windows Python3.12.10 / NumPy1.26.4 | 76 | 29596 | 22109 |
| Linux Python3.11.17 / NumPy2.4.6 | 76 | 29565 | 22201 |
| Linux Python3.14.8 / NumPy2.4.6 | 76 | 29565 | 22201 |
| Linux Python3.11.17 / NumPy1.24.4或1.26.4 | 72 | 29896 | 22228 |
| Linux NumPy1.26.4，禁用AVX512F/AVX2/FMA3 | 76 | 29596 | 22109 |
| Linux NumPy2.4.6，scalar-math干预 | 76 | 29596 | 22109 |

[RUN] Windows/Linux 的 realistic 各自与base相同；Windows两个标量干预未改变结果；Linux power-math与原版相同。所有mission都完成且found=8，不等于匹配参考。

## 首次离散分歧与同输入反事实

[RUN] Windows NumPy2.5.3与Linux NumPy2.4.6的trace，最早候选值差异在索引2；首次消息选择差异在索引243，即 **t=40, agent=3**。当时调度输入的位置、SNR、预算、价格及所有候选消息结构相同，只有一个候选值不同：

```text
INTENT rate=1, bits=symbols=18
Windows: 6.191039765244135
Linux:   6.191039765244134
差值: -8.881784197001252e-16 = -1 ULP
```

[CODE] `schemes.py:266–305` 先二分再按每组最大value/symbol排序补齐，使用严格比较。该状态二分最终都选空。Windows两组密度相等，稳定排序保留INTENT在前；Linux INTENT密度低一ULP，EVID在前。实数模型下，这两个rate1选项的bits=symbols，因此理论密度同为P(success)。

[RUN] Windows选择INTENT（rate .25，72symbols/18bits），剩余28symbols容不下EVID；Linux选择EVID（rate1，99symbols/99bits）。在同一Windows输入中**只替换上述一个值**，原版lagrangian_select便重现Linux选择，局部数值因果关系得到验证。

[RUN] 固定候选集合离线枚举80种组合，最优目标约34.05072；Windows贪心约14.70867，Linux在该状态达到枚举最优。单位是该吞吐量规则的**单次期望有效bit目标**，不是task quality、任务收益或论文贡献。单样本不能证明稳定且有代表性的性能缺陷。

## 未解决问题与建议

[CODE] 可用历史中关键核心blob自初始公开版本未变（前轮source-history-comparison证据）；生成脚本使用核对过的run_episode与配置。两条仿真路径不能解释保存的83slots。

[RUN] 已证明环境/浮点实现足以改变轨迹，但没有作者逐时隙trace，不能把本轮首个分歧认作相对于作者轨迹的首个分歧。[HYPOTHESIS] 作者结果可能来自另一数学库/CPU路径，或未记录的生成配置/源码，尚无法区分。停止逐版本/逐参数搜索，避免拟合最终数值。

建议先索取provenance；发送作者询问仍需明确授权。若批准统计复现，先冻结环境、全部paired seeds、指标/CI及实际等价界限，报告全部差异；不能事后选择容差或把原R4改写为通过。新关卡通过后，再做shared/oracle与独立receiver因子诊断。

完整证据：`E:\gosc-agentic-teams\.local\reproduction\2026-10-15-mismatch-v2\`，v1未覆盖。工具执行版本已保存且SHA256验证；完成manifest均exclusive-create。
