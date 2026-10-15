# Research Task Brief — blocked throughput provenance

- **授权与范围**：用户批准追溯最小失败样本的生成环境、历史源码及数值轨迹；原因解释或解决后才恢复 R4。仅本地 Planner，小规模 CPU 诊断，不发布/联系作者，不下载模型。
- **科学问题**：[HYPOTHESIS] `gosc_bits/W100/eta0/seed0` 的 saved/fresh 差异是否来自生成时配置/代码路径，或数值运算引起的离散调度分歧？不能据此宣称 TeamModel 缺陷。
- **已有证据**：[RUN] v1 留存 1399 条 R4 结果，1398 条匹配，一条不匹配；作者保存 83/31011/23468，本机 76/29596/22109（slots/uses/bits）。默认 GOSC 单 mission 匹配；完整 93 tests 通过。原记录全部保留。
- **基准**：[CODE] 工作 HEAD `0f10fe7cbfb67d7c18102413483667d4c16d2977`；原版 `387b49389385b51c275dc5a22ec1672087edda1d`；启动 git status clean。
- **计划文件**：仅 `experiments_ext/` 的诊断工具、`tests_ext/` 必要验证、`research/logs/` 和 `research/reproduction/` 新证据；原始模块/结果/缓存不改。
- **验证顺序**：审查现有 456 步轨迹及生成脚本；比较 base/realistic；检查数学等价的 success-probability 运算及选择边界；若得到可解释分歧，保存首个分歧状态、算术证据和全部负结果，再判断能否恢复原定 R4。
- **成本**：优先现有环境，预计 10–30 个数秒级 mission 和静态分析，单进程为主，数分钟 CPU；若确有必要恢复已批准 R4，沿用最多 4 workers。零付费 API、零 GPU、零模型下载。未测 CPU 峰值不填造数。
- **反例/停止条件**：若所有合理等价运算均不能解释差异，或需缺失的作者环境/轨迹，不继续用参数搜索拟合目标；记录未解决根因。不得放宽 v1 的 1e-9 验收，或把局部一致冒称全部 R4 通过。
- **验收**：可重复的因果/兼容性证据（首个调度分歧及其传播），或明确的缺失证据清单；不可变新目录 `.local/reproduction/2026-10-15-mismatch-v2/`；保护哈希核验；研究报告和下一步 Go/No-Go。

## 有依据的兼容矩阵补充（在观察这些配置结果之前记录）

[RUN] 本机已缓存 Linux 镜像中有 Python 3.11.17 / NumPy 2.4.6；Windows 缓存也有 2.4.6。跨平台首个离散差异出现在 t=40, agent=3，原源码的同密度贪心排序受一 ULP 影响。但 Linux 2.4.6 仍不匹配作者结果。

[HYPOTHESIS] 原 requirements 只限定 `numpy>=1.24`，需检验 1.x 与 2.x 边界。只增加 Linux 1.24.4（最低主次版本的末次修订）、Linux/Windows 1.26.4（1.x 最后版本）；不逐版本搜索、不调参拟合作者目标。预计 3 个 wheel 共约 50 MB，隔离在 .local，主 .venv 与 lock 不变；不下载镜像/模型，不调用 API。此为已授权环境追溯的兼容探针，不能替换冻结的 R4 环境。
