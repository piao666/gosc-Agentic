# GOSC 项目进度核查与硕士论文实施说明书对照

核查日期：2026-10-19（Asia/Shanghai）。远端工作仓库：https://github.com/piao666/gosc-Agentic 。核查基准：`main@876fc523b113b3b65e19f0b730f1573ccc2ee17f`；原作者整合基线：`387b49389385b51c275dc5a22ec1672087edda1d`。

## 后续 HPC 执行增量（2026-10-19）

[RUN] 已在 HPC 建立 Python 3.11.15 项目环境；R1 85/85 通过（33.64s）；R2 三原脚本生成 17 PDF、18 TeX，三个 summary 与历史基线在 1e-10 内一致；R3 GOSC seed3000 实际完成 113 slots、found=8、false=0、uplink symbols=19051。所有正式输出已回传，原文件哈希不变。

更新后的事实见 `research/reproduction/repro_report.md`、`research/sync/project_status.json` 与各 run。本报告以下保留首次盘点时快照，其中“R1新目录未运行、R2/R3未运行”已被上述新证据更新；R4/R5/R6、P0纸码映射与P2关卡仍未完成，不宣称 P1 整体验收或新方法成立。

## 1. 首次盘点结论（HPC 执行前快照）

**[CODE] 已完成的可核验研究准备主要是 Windows 环境整理及历史 R1 测试验证；P0 盘点仍缺部分正式交付，P1 正式复现尚未完成，P2 只有部分文献基础，P3–P5 未找到对应实现、实验或稿件产物。** 不能将仓库自带的作者结果、85 项单元/回归测试，记作本课题已完成独立复现或已提出有效新算法。

- [CODE] 10 月 12 日的完整日志记录：85 collected、85 passed in 41.84s；pip check、模块导入及内存 Agg 绘图检查通过。证据位于 `research/logs/environment-2026-10-12/`。这是历史运行证据，本轮没有重新执行测试。
- [CODE] 与原作者基线比较，最新提交没有改动 `gosc/`、`experiments/` 或原测试；新增工作主要是依赖锁定、Windows 引导脚本、研究治理文件与日志。
- [RUN] 本轮只读扫描 `E:\Papers\99-附件\论文原文`：42 个 PDF、42 个不同预期 ID，无编号缺失或重复；42 个首页均可提取文本并记录文件 SHA-256。不能据此宣称全文完整性、发表状态或精读全部完成。
- [RUN] 扫描论文笔记目录只发现 B01、B02、B03、B04、C02 五篇既有笔记；本轮未重新评价笔记深度，不推断用户没有在其他位置阅读。
- [HYPOTHESIS] 下一步最有价值的工作是补齐 P0 的论文—代码—图表映射与复现协议，然后依序推进 R2、R3；目前不具备宣称 Work 1 创新有效的实验依据。

## 2. 最近提交：主分支总共 4 次

以下日期按北京时间；顺序从新到旧。已同时查看提交信息和文件差异。

| 提交 | 日期 | 实际变更 | 对本课题进度的意义 |
|---|---|---|---|
| [876fc52](https://github.com/piao666/gosc-Agentic/commit/876fc523b113b3b65e19f0b730f1573ccc2ee17f) | 2026-10-12 14:27 | 新增 AGENTS、总说明书、锁定依赖、PowerShell 环境脚本及 12 个 research 文件；README 增加工作副本说明；删除两个生成的 summary JSON | 用户研究工作副本初始化与环境验证，未开发新算法 |
| [387b493](https://github.com/piao666/gosc-Agentic/commit/387b49389385b51c275dc5a22ec1672087edda1d) | 2026-09-30 16:03 | 合并 gosc_ext 到 gosc/realistic.py，扩展实验迁入 experiments、tests_ext 迁入 tests；结果合并到 results；缓存整理 | 原作者基线整合，不能记为本课题新增研究成果 |
| [9440859](https://github.com/piao666/gosc-Agentic/commit/9440859d376d6e343e673f3c1d6478fdc0c3ff95) | 2026-09-30 15:59 | 生成图表目录由 manuscript/figures 统一为 figures；调整忽略项、README、绘图脚本路径 | 原作者输出组织调整 |
| [8a66e70](https://github.com/piao666/gosc-Agentic/commit/8a66e701af5600ac660ce28fe4d2acc8b6c9dbf6) | 2026-09-30 15:56（提交时间） | 初次公开模拟器、实验、原始 mission 结果与 LLM cache | 原作者工作的来源和可复现输入 |

[CODE] 最新提交的大量删除行主要来自 `results/summary_realistic.json` 和 `summary_revision.json`，不是删除原始 mission 数据或算法。历史日志称本地备份在忽略目录 `.local/`；新克隆不会带来该私有备份或旧 `.venv/`。原 summary 仍可在基线 Git 历史查看，后续重建必须隔离输出。

## 3. research 原有 12 个文件逐项核查

| 路径（research/ 下） | 核查结果 |
|---|---|
| logs/2026-10-12_environment_task_brief.md | 环境验证任务的范围、授权、验收与停止条件；提及先前 P0，但未附完整 P0 产物 |
| logs/task_log_2026-10-12.md | 环境任务报告；明确未完成 fresh campaign、完整图表、live LLM |
| reproduction/windows_environment.md | Python 3.12.10、UTF-8/Agg、依赖锁定、Windows 操作及结果保护边界；R2–R5 明确未运行 |
| logs/environment-2026-10-12/environment_manifest.json | 历史机器、依赖、命令与状态；base commit=387b493、当时 dirty=true；reproduction_stage=R1 only |
| logs/environment-2026-10-12/validation_commands.json | pip check、import smoke、pytest collection、pytest 的历史命令、退出码、时间 |
| logs/environment-2026-10-12/pytest-collection.log | 实际收集 85 项，含三个 fake-transport LLM 测试 |
| logs/environment-2026-10-12/pytest.log | 85 passed in 41.84s |
| logs/environment-2026-10-12/pip-check.log | No broken requirements found |
| logs/environment-2026-10-12/import-smoke.log | 导入和内存 Agg 绘图成功 |
| logs/environment-2026-10-12/hardware.json | 旧环境记录：i7-11700F、约 16 GB RAM、GT 730 2 GB；本轮未重新测硬件 |
| logs/environment-2026-10-12/baseline-input-sha256.json | 78 个受保护源码、测试、结果、缓存输入的 SHA-256 |
| logs/environment-2026-10-12/publication_audit.json | 当时发布前扫描与保护文件核验；不是研究实验或性能验证 |

上述内容全为环境/传输和治理证据。核查时 research 中没有 literature、ideas、writing、protocols 的既有成果。不能因文件未提交就断言旧电脑或旧聊天从未完成过相关工作。

## 4. 与说明书阶段 P0–P5 的对照

| 阶段 | 说明书要求 | 目前证据与缺口 | 状态 |
|---|---|---|---|
| P0 本地盘点 | Git/环境、42 篇索引、公式—代码—实验对应 | 有历史环境 manifest；本轮补充 42 篇文件/首页/哈希索引。原定 00_inventory.md、GOSC_paper_code_map.md 未在基准 HEAD 找到；论文元数据仍需完整核验 | 部分完成 |
| P1 原生复现 | 测试、保存数据重分析、单 seed fresh、paired seeds、独立校准/评估、cached/live LLM | 历史 R1 有完整通过日志；R2–R6 未见合格的新复现档案。新目录依赖与测试尚未复核 | 已完成环境/测试子阶段，正式复现待推进 |
| P2 问题审查 | 关键文献、Gap Matrix、2–3 个可证伪 RQ、拒稿自查 | 说明书已提出 RQ/H1–H3；Papers 有 5 篇旧笔记及只涵盖这 5 篇的旧矩阵。研究仓库未见 RQ_v1、更新矩阵和 reviewer_objections | 部分文献基础，未达到阶段验收 |
| P3 最小改进 | 独立 M0→M1 估值器、固定 scheduler、先小规模再独立测试 | 未见本课题扩展代码、训练标签、实验配置或初步曲线；原 GOSC 的 ToM/TV 不能算新 M0/M1 | 未见实施证据 |
| P4 完整实验 | 成本匹配、多 seed、CI、消融、跨任务/模型/信道、失败案例 | results 中已有数据来源于原作者；未见本课题新实验、配对统计或新方法开销核算 | 未见实施证据 |
| P5 写作/投稿评估 | 系统模型、实验协议、结果/方法稿件、引用库和复现清单 | 总说明书是计划；四个 writing 起步文档、研究初稿及引用库未在基准 HEAD 找到 | 未见实施证据 |

### 复现 R0–R6 的细分

| 关卡 | 状态 |
|---|---|
| R0 基线/环境盘点 | 历史 manifest 存在；本轮完成仓库下载与路径核验，环境、标签详情见本轮 manifest；完整纸码映射未完成 |
| R1 单元/回归测试 | 2026-10-12 历史 85/85 通过；2026-10-19 新目录未运行测试 |
| R2 保存数据重绘 | 未见完整图表、数值/CI 与原论文逐项核对报告；历史生成过 summary 不等于此关通过 |
| R3 单 mission fresh | 历史任务明示未运行；测试中的仿真不替代单独复现记录 |
| R4 多 seed 比较 | 未见本课题独立执行及 paired、成本匹配、CI 档案 |
| R5 cached/live LLM | 原作者缓存存在；本课题未见 replay/live 完整评估；fake transport 仅测试客户端逻辑 |
| R6 关键表图逐一对应 | 未见完整差异表及覆盖清单 |

不使用主观百分比衡量完成率。说明书的“第几周”是滚动估计，缺少实际启动/投入记录，不能按日历直接认定延期。

## 5. 本地论文库核验

[RUN] 实际根目录为 `E:\Papers`，原文目录为 `99-附件\论文原文`。扫描结果 A=11、B=11、C=5、D=15，无缺失、无重复，42 个首页可读。详见 `research/literature/literature_inventory_2026-10-19.csv`。索引仅保存路径、标识、首页核验状态、哈希及笔记链接，不复制或上传私人 PDF。

[PAPER] 发现两处显著题名差异（均以本地 PDF 第 1 页为依据）：

| ID | 说明书/文件名 | PDF 实际首页标题 | 标识与处理 |
|---|---|---|---|
| C05 | Extend the Safety Horizon for Intelligent Transportation Systems through Semantic-Aware Cooperative Perception | HMS-SCP: Task-Oriented Multi-Scale Semantic Communication for V2X Cooperative Perception | arXiv:2608.14603v2；编号一致、标题不同，保留版本/命名差异，不能静默当作完全一致 |
| D15 | Semantic Communication and Control Co-Design for Multi-Objective Correlated Dynamics | Semantic Communication and Control Co-Design for Multi-Objective Distinct Systems | arXiv:2410.02303v2；编号一致、标题不同，后续引用按实际版本核验 |

[CODE] 旧笔记与整理报告记录于 2026-08-20，范围仅 C02/B01/B03/B02/B04，旧 Gap Matrix 是 partial。它不能证明 A/D 核心先例已精读，也不宜直接作为当前新颖性结论。

说明书本身还有阅读清单口径差异：§4.1 启动十篇含 B04、A03，而 §8 P2 优先十篇换成 D08、D10。应先统一阶段验收阅读集合；目前分别能找到 3/10、2/10 篇既有笔记，这仅为文件存在统计，不是阅读深度评分。

## 6. 新研究与已有 GOSC 的边界

[CODE] 已读取基准版本的关键源码：

- `gosc/voi.py:29` TeamModel；`:105` evidence_voi、`:122` intent_voi、`:136` joint_voi：已有接收队友行为近似和信息价值，不可把“receiver-aware”本身作为新颖性。
- `gosc/schemes.py:266` lagrangian_select、`:311` GOSC、`:363` evidence_voi、`:407` build_groups：已有 ToM、TV、bits、AoI 价值规则和预算/传输率选择。
- `gosc/realistic.py:43` _estimate、`:84` build_groups、`:369` phase_communicate、`:403` _uplink_gosc、`:429` _uplink_gosc_price：已有估值误差、包头、共享上行及中央/价格协调路径；未来替换价值函数必须检查与 schemes.py 的平行路径。
- `gosc/channel.py:27` fbl_error、`:60` success_prob：已有 Rayleigh/outage/FBL 与 CSI 条件，单纯增加无线关键词不能算新贡献。
- `gosc/llm_agent.py:55` choose、`:115` _candidates、`:142` plan：LLM 选择受限候选标签；缓存未命中会走 transport；失败可以回退 planner。运行脚本是否阻止混入 fallback 仍需逐实验检查。
- `gosc/simulator.py:200` run、`:214` phase_decide、`:260` phase_communicate：基础时序入口；本轮未运行。

说明书的科学主线仍应是：[HYPOTHESIS] 在可观测接收端 runtime 状态下，低成本估值能否在相同 radio/model/seed 条件下改善实际任务收益，且扣除估值与同步开销后仍有效。Work 2/3 依赖 Work 1 的实证门槛，目前均不能记为已启动的成果。

## 7. 建议的下一步顺序

1. 补齐 P0：核验题名差异、文献元数据和优先阅读集合；建立 `GOSC_paper_code_map.md`，将关键公式/表图与函数、命令、结果文件对应。
2. 完成新目录环境复核：旧 `.venv` 不随 Git 克隆；先检查现有依赖，再决定是否需要安装；重跑 R1 时另存日志，保留历史证据。
3. 写明 R2 复现协议后，在独立输出目录重分析作者数据；注明 analysis reproduction，核对数值及 CI，优先保留 ToM 对比简单价值函数的负面结果。
4. 通过前置关卡后执行 R3 fresh 单 mission，再确定 R4 的小规模 paired seeds 和独立校准/评估方案。
5. 与 P1 并行更新 P2 的 GOSC/BANDMAS/JTCM/ToM2C 等先例对照；把 H1–H3 变成可测反证标准，再考虑 M0。

以上为后续建议，不表示本轮执行过新实验。长时实验、模型下载/live LLM、付费调用或方向变更按 AGENTS 与用户后续任务范围决定。

## 8. Research Task Report

- **Research Question / Hypothesis**：核查实施说明书与仓库/本地文献证据是否一致；当前停在环境与部分盘点阶段的判断得到支持。
- **已核验前人工作**：[CODE] 原作者基线和 README、关键价值/调度/链路源码；[PAPER] 42 个 PDF 首页/标识，重点记录 C05/D15 题名差异。未宣称全文精读。
- **实际阅读源码**：AGENTS、总说明书、README、research 全部 12 个文件、voi/schemes/realistic/channel/llm_agent/simulator、Windows 脚本与提交差异。
- **本轮新增或修改**：进度报告、审计 manifest、证据索引、任务 brief、论文索引、工作路径配置；活跃说明中的旧路径调整到用户指定值。具体 Git 状态见 `research/logs/progress-2026-10-19/local_verification.json`。
- **实际运行**：Git 克隆/只读核查；PDF 首页提取与哈希；文件和 JSON/CSV 一致性检查。没有实验 seeds/configs/models。
- **测试与结果**：历史 85/85 有档案；本轮算法测试、R2–R6 未运行。文档/路径/索引的核验见 manifest。
- **失败/负面证据**：首次默认 Git 下载停滞，停止本轮进程后改 HTTP/1.1 重试；两处 PDF 题名差异；多个计划交付物未在基准 HEAD 找到；旧环境不能视为已在新目录重建。
- **与原 GOSC 的差异**：本轮没有修改算法、测试、原始 results/cache 或 LICENSE。
- **公平性与泄露检查**：本轮无训练、调参、评估；没有使用 eval seed 学习，没有上传私人 PDF。
- **成本**：Git 网络传输、轻量 CPU PDF/文本扫描；无模型下载或真实 LLM/API 调用，CPU/GPU 峰值与助手 token 未测量。
- **可否进入下一阶段**：Go for P0 补齐及 R2 协议准备；P3 新算法开发证据不足。
- **用户需要批准的下一步**：本轮交付不依赖额外批准；后续研究任务由用户确定范围。

## 9. 工作路径与应用会话状态

[RUN] 仓库已完整克隆至 `E:\gosc`，origin 为指定 GitHub 地址；当前研究分支 `research/progress-audit-2026-10-19`，本轮改动未提交、未推送。`AGENTS.md`、README、总说明书和 Windows 使用说明已更新代码/论文根目录；结构化配置见 `research/workspace_paths.json`。78 个受保护文件的原始字节哈希与历史清单一致；审计器最初错误地把 CRLF 转为 LF，修正后通过，未改动受保护文件。

[RUN] 应用已识别现有 Gosc 项目指向 `E:\gosc` 且为 Git 仓库。两次移动聊天调用均返回成功，但复查仍显示当前聊天 `projectId=null`、`cwd=E:\Papers`，因此应用层移动/默认目录切换未能确认。本轮代码命令显式使用 `E:\gosc`。若要变更应用当前聊天的持久工作目录，需要通过应用侧栏完成文件夹/聊天归属操作；仓库里的路径配置不会改写应用会话 cwd。

## 后续纸码与图表审计更新（2026-10-19）

[RUN] 已完成本地D01 v1全编号映射：5式/5图/13表/Algorithm1。HPC审计9数值表405单元，原8表一致，表VI5格通过原table-only helper补齐后一致；25默认字段与6冻结点一致。37/38候选口径、图2minor标签显示差异、Genie定义与bootstrap次数均在审计报告显式记录。当前P0纸码映射已具备；R4协议已定但未执行，P1整体与P2关卡未完成。见 research/logs/GOSC_paper_code_map.md、research/reproduction/figure_table_audit_2026-10-19.md、research/protocols/r4_protocol_v1.md。

## 后续R4-A0实际执行更新（2026-10-19）

[RUN] 两场景×三方案×10seeds（9000–9009）共60条真实mission已完成，9项执行器测试及独立原始记录审计通过；首次0mission导入失败保留。主运行墙钟20.11s，最大并发2、每worker线程1。Search时间均值GOSC70.2/periodic75.4slots；Rescue saved均值98.75%/85.00%，periodic未达到原冻结目标。仅N10 pilot，不升级为正式优势或完整P1验收。完整证据、失败修复与成本外推边界见research/reproduction/r4_a0_report_2026-10-19.md；A1/B/C和训练未启动。


## 四场景成本探测完成（2026-10-19）

[RUN] search-K10、search-clustered、rescue-W50、rescue-snr-5各GOSC/冻结periodic、seeds9010–9012共24条完成，17项测试/独立审计通过。六场景1200条A1预计575.8s，建议硬上限1860s、单条120s、并发2，每worker线程1；预算为小样本外推，不含可选Genie/B/C/LLM/训练。下一计算地点为HPC；完整A1待范围确认后准备执行器，未自动启动。报告：research/reproduction/r4_cost_probe_report_2026-10-19.md；预算：research/protocols/r4_a1_budget_proposal_2026-10-19.json。P1整体仍未验收。


## 完整R4-A1执行更新（2026-10-19）

[RUN] 已执行六场景两方案seeds3000–3099共1200条、600配对；28项测试及独立统计/数据审计通过。登记墙钟574.586676s，0程序失败/超时/中断。1200条主指标/上行symbols逐seed与作者保存值一致；不宣称全部轨迹历史比对或新方法贡献。periodic Search-W100/K10均值略未达冻结目标；所有search时间差CI及rescue-snr-5获救差CI跨0，负结果保留。报告research/reproduction/r4_a1_report_2026-10-19.md，实际状态research/protocols/r4_a1_execution_2026-10-19.json。B/C、独立校准与R5LLM/P2关卡仍待推进，完整P1未验收，未启动训练。
