# AGENTS.md — GOSC 硕士论文科研与开发协作约束

> 本文件位于本地 **`E:\gosc\AGENTS.md`**，并同步至 HPC **`/home/u202520081000097/jupyterlab/Paper/gosc/AGENTS.md`**，适用于两端在该仓库工作的 Codex 及其他 AI 编码助手。它不仅是工程代码规范，更是**研究第一作者的科研行为规范**。你被要求像准备投稿且要承担全部科学责任的硕士研究生一样工作。作者身份、贡献与投稿决策仍由真实研究人员/导师决定；AI 不得自称真实署名作者或擅自对外提交。
>
> 研究总说明书：`硕士论文研究与实施说明书.md`（当前位于仓库根目录；若后续迁移，启动时先定位）。主方向：**LLM Multi-Agent → Receiver/Task-aware Semantic Value → Wireless Semantic Communication → Scheduling/Resource Allocation → Task Success**。

> 当前工作仓库：<https://github.com/piao666/gosc-Agentic>；代码根目录 `E:\gosc`，参考论文根目录 `E:\Papers`（用户于 2026-10-19 校正）。路径配置见 `research/workspace_paths.json`，最近进度审计见 `research/reports/progress_review_2026-10-19.md`。历史日志中的旧路径仅表示当时环境。

> 最新摘要信息/成本核查（2026-10-22）：23测试、96组有界条件通信回放及独立审计通过；实际编码CRC/ACK/快照、排队/重传/下行丢失/等待/TTL已核查。仍是原calibration轨迹的传输可达性审计，cache不进入任务策略，未测paid-summary任务收益。目标/位置主要刷新已有机制，三bit差异桶不能替代完整oracle。逐slot立即重试的成本不是最优同步成本；先审查RTT-aware/捎带及最简单估值接口，复杂训练保持No-Go。入口：research/reports/receiver_summary_information_cost_audit_2026-10-22.md。

> 最新顺序验收（2026-10-22）：逐图表和noise575范围清查完成；17native PDF与独立rescue展示版已目视。HPC接收端特权诊断1248校准+260验证、5项测试及独立审计完成，0/6主要比较达到预设联合门槛；复杂训练No-Go，不证明状态无价值。文献新增29份选段记录（连同旧13份共42篇有笔记，非全部通读），Gap Matrix/RQv2/拒稿自查已更新。最新入口：research/reports/acceptance_and_pilot_progress_2026-10-22.md。原校准/cache/历史差异仍单列。

> 最新总审计（2026-10-22）：主队列23阶段已评估，22正常退出、作者cache回放失败；所有登记产物已回传。P1精确历史一致性、作者cache生成链和原校准过程仍有缺口。真实LLM570条含180Planner对照与390混合任务；新cache570/570预设字段重现，不等于恢复作者cache。完整图表补齐为17PDF/18TeX。最新事实入口：[总审计报告](research/reports/final_reproduction_audit_2026-10-22.md)、research/sync/project_status.json、plans/next_steps.md；下文旧阶段状态是历史记录。新方法训练未开始。

## A. 启动协议（每次会话和每个开发任务）

GitHub归档（2026-10-26）：用户授权一次新提交并正常推送当前research/progress-audit-2026-10-19分支、保持工作区干净；说明commit/2026-10-26-01-causal-service-and-age-review.md，归档10月24–25日实现/协议/报告/运行元数据，并携带此前未推送47389eb祖先。实际提交/推送身份以包含本说明的Git历史与远端引用核对，不回填自身哈希；旧报告“未提交/未推送”保留当时含义。原始outputs仍忽略，原No-Go与新协议仅审阅候选不因版本归档改变；本次无新HPC计算。

最新成本/age机制审查（2026-10-25）：原252任务950281事件分析/独立复算、18合同及1536合成选择器比较完成，新mission/N0；原No-Go保持。选中pose精确摘要UL20516uses（34.27%全通信），直接摘要保守识别界41.90%–66.63%（不是CI/精确DL分类）。固定轨迹账本免去全部摘要UL仍39341.75uses，超periodic/public的1.05上限。age统一缩放所有候选值，理想目标等价动态p_eff=p*(1+mean_age)；native-age不买摘要对照未运行，历史factor/DL类型字段缺失。新协议仅审阅候选，不自动实施/扫参/扩N/训练。入口research/reports/summary_age_mechanism_review_2026-10-25.md；本轮未Git提交/push。

最新独立校准审计（2026-10-25）：用户明确批准1200s预算修订后，GP-v2原21候选×12新world共252任务在447.37s正常完成；950,281事件、CI/N/成本前沿/固定price消融独立复算通过，首版审计及措辞澄清v2保留。选中pose较periodic平均快8.6667slots，但通信比1.606664、逻辑CPU比2.813743；较public快8.3333slots，成本比3.018507/3.481296。无联合成本支持，规划N21907>200上限，当前协议No-Go。paid-ignore固定price有成本支持但gain区间跨0；不扩N、不事后换age为主方法、不运行正式test/训练。作者原校准/cache链/历史差异仍单列。最新入口research/reports/causal_calibration_audit_2026-10-25.md；本轮未Git提交或push。下方10月24日“预算Pending/校准0次”是此前状态。

最新因果服务验收（2026-10-24）：GP-v2统一task/summary解码反馈下界（当前2slot）与估值CPU队列，有界盲目catchup、paid-ignore/age/shuffle及21候选已实现。HPC187主回归+28补充合同（含重复，共190不同测试）、42短probe及31,280事件独立审计通过；两个旧GP-v1短fixture与归档源码全字段相等。214world事前冻结；校准投影895.50s超过480s门槛，252校准任务0次，预算Pending。1200s预算提案待用户明确批准，不回写旧blocked协议；正式test/训练未运行。新服务收益未知、旧GP-v1科学No-Go不撤销。入口research/reports/causal_service_progress_2026-10-24.md。本轮源码/报告尚未Git提交或push。

本地Git归档（2026-10-23）：用户授权一次本地提交，归档当日实现/报告/运行元数据及47份R2/R3白名单副本，说明commit/2026-10-23-01-paid-pose-calibration-and-cost-review.md。未push，不新增HPC计算；旧日志“未提交”保留当时含义。实际提交身份通过Git历史关联，不回填历史run或自身说明哈希。下一步研究关卡仍是反馈/CPU时钟及有界catchup，非扩N/训练。

最新同步成本/估值审查（2026-10-23）：最终51合同通过；v2观察24/24完整result精确匹配原校准，两版主要统计一致，辅助同slot重复计数已修正、旧记录保留。3927次估值中96.49%改变投影、79.35%改变超过诊断容差的候选价值、10.54%改变选包；直接摘要账本占额外资源83.28%，实际反馈2slot而RTO1slot，task盲目历史重播占paid DL77.46%。两版48条均是原12world重复，新独立N0。原No-Go维持，未改服务/price/原结果/样本；下一步先审查统一反馈/CPU时钟与有界catchup，非扩N/训练。入口：[sync_cost_value_review_2026-10-23.md](research/reports/sync_cost_value_review_2026-10-23.md)。

最新periodic/CRN校准（2026-10-23）：HPC156测试、24成本probe、144校准任务（独立N12）和独立产物审计完成并回传；两个合同失败run保留。选中periodic k8/eps0；paid-pose相对其平均多3.8333slots、UL+DL成本比1.426004，相对public-ToM多1.5slots、成本比1.357991。探索性结果触发预设No-Go，规划N15419>200上限；未冻结可执行test N/预算，预留test任务0次。不得扩N救结果或自动训练。入口：[periodic_crn_calibration_2026-10-23.md](research/reports/periodic_crn_calibration_2026-10-23.md)。下方是前序快照。

最新原生适配（2026-10-23）：GP-v1原生任务语义编码、实际帧长候选和局部接收短闭环通过HPC145测试，3份同世界4slot原始trace已保存；非作者旧wire精确复现，未运行收益campaign/训练。下一步强periodic基线、事件索引CRN，再预算化独立校准与新world/N/功效冻结。[报告](research/reports/native_adapter_progress_2026-10-23.md)。旧段落保留各阶段历史含义。

最新实现验收（2026-10-23）：R2/R3交付包47份SHA一致副本已准备、未Git提交/推送；最小pose/ledger/双路径估值与单lane RTT合同已实现，HPC129测试及独立文件审计通过。未运行paid任务效果或训练；下一步先完成统一UL/DL/CPU服务成本与对照/样本/预算冻结。报告：[minimal_interface_delivery_2026-10-23.md](research/reports/minimal_interface_delivery_2026-10-23.md)。下方“本轮只做静态”指上一任务快照。

当前统一入口（2026-10-23文档/静态审查）：[research/README.md](research/README.md)；[协议审阅稿](research/protocols/receiver_summary_minimal_protocol_v1.md)。科学证据仍截至2026-10-22，本轮未启动实验、训练或远端同步。review_candidate不是已冻结可执行预登记；旧状态段落保留历史含义。

1. 先读本文件、研究总说明书、`README.md`、最近一次 `research/logs/` 任务记录和待解决问题。
2. 执行/检查（仅只读）：`git status --short`、`git rev-parse HEAD`、`git remote -v`；本地源码根目录 `E:\gosc`，HPC 运行根目录 `/home/u202520081000097/jupyterlab/Paper/gosc`。测试/训练前使用 `ssh hpc` 核验远端身份、项目路径、Python 环境、资源配额和同步 manifest；按 E1 节强制在 HPC 执行。
3. 如果工作区存在用户未提交修改，**不要 reset/checkout/clean/覆盖/重命名**；先解释其意义并请求处理方案。
4. 先写“Research Task Brief”：本轮科学问题、前人成果、拟验证假设、修改文件、实验设计、预期成本、可能反例、验收标准。
5. 当前会话范围之外的任务（特别是新模型、全量多 seed、外部数据与投稿）必须先得到用户批准。
6. 任务结束必须输出：变更清单、实际执行的命令、通过/失败的测试、证据路径、剩余不确定性和下一步建议。

## B. 真理层级和证据标记（必须执行）

每份报告/稿件里的关键断言使用：

- `[PAPER]` 论文原文：PDF 的页码/节/式/表/图及准确文献元数据。
- `[CODE]` 原始或本地 git commit：具体文件、类/函数和行范围。
- `[RUN]` 实际执行：区分本地管理与 HPC 计算，记录 execution_host、命令、环境、commit、数据、seed、日志和输出路径。
- `[HYPOTHESIS]` 尚未验证的推断、计划、待检验创新点。

严禁将它们互相冒充。

- **禁止伪造**实验值、论文结论、显著性、用户环境/硬件、参考文献、作者 limitation、测试通过、未来会议截止或代码链接。
- 未找到写 `未找到/未核验`；没有跑写 `未运行`；跑失败写 `失败 + 证据`。
- 不得把我们推断的 limitation 写成原作者承认的 limitation。不得由一次查不到论文就声称“首次”。
- 不得使用未来 reward/全局隐藏状态/测试标签在线决定价值或调度。离线反事实标签可用，但须严格隔离并说明 oracle 设置。
- **所有负结果也需要记录**；不得在审稿前删掉失败 seed、不显著结果、不利对照。

## C. 学术目标优先于“完成代码”

在修改算法前，要能完整回答：

1. 原 GOSC 已经实现什么（ToM、AoI、Throughput、Belief divergence、消息/传输率选择、共享上行、LLM 缓存）？
2. 新方法与 GOSC/BANDMAS/JTCM/iCoTASC/ToM2C 哪个机制不同？
3. 为什么这个机制与 LLM Agent 任务结果存在因果/统计上可检验的联系？
4. 相同任务、模型、频道、随机种子、无线预算下，最强的简单 baseline 是什么？
5. 净增益是否超过估值器的推理成本/同步通信成本？
6. 什么实验结果会否定本方法？

仅当回答有依据时才实施算法。不能为了主张“方法先进”就不断增加模块。

## D. GOSC 原仓库保护规则

- **以本地实际 commit 为准**：线上 README 仅作参考，不保证与用户 E 盘一致。
- 优先建立新的研究分支，例如 `research/baseline-repro`、`research/value-estimator-v1`，并记录 base commit。基线实验需要能回到未修改的上游版本。
- 不得直接修改/覆盖上游 `results/` 数据、历史缓存、论文表图、`LICENSE`、历史 git 提交或基线测试来“匹配新结果”。
- 首选在 `extensions/`、`experiments_ext/`、`tests_ext/` 中新增代码，以最小接口修改接入 `gosc/voi.py`、`gosc/schemes.py`、`gosc/realistic.py`。
- 核心模块修改前必须对 `realistic.py` 与 `schemes.py` 的平行调度路径做映射，防止一处更新另一处仍是旧策略。
- 不可把原版 GOSC 替换成新策略后继续标为 `GOSC`。新算法要使用独立标识；baseline 与 ours 的运行输出隔离。
- 未审核 `--help`、文件写入行为和目标目录前，不运行长时间全量实验。
- 保留上游 MIT License、原作者版权与引用；新代码在学术论文中明确界定借用范围。开源代码使用许可不代表免引用。

## E. 对 Windows/本地数据的限制

- `E:\gosc`：本地源码/文档与同步；`E:\Papers`：用户个人论文知识库；HPC 的 `Paper/gosc`：项目测试、实验、推理和训练。
- Obsidian **默认只读**：允许定位 PDF、阅读、比对文献、生成指向 PDF 的引用和索引；未经明确要求不得移动/覆盖/重命名 PDF 或修改 Obsidian 的 `.obsidian/` 配置。
- 若收到“整理 Obsidian”的明确请求，先列文件变更预案、备份现有笔记再修改，保留 wikilink。
- 不上传本地 PDF、隐私文件、研究数据、密钥到公网服务；读取私有内容不意味着有公开权限。
- 不保存/输出 `.env`、API key、个人凭据或 Ollama 服务的敏感配置。提交前检查 `.gitignore`、git diff 和大文件。
- 依赖安装、模型下载、第三方代码执行、收费 API、长时 GPU/CPU 高占用任务先估算成本并征得用户同意。
- Windows PowerShell 与上游 Bash 命令不等价：shell 脚本须确认 Git Bash/WSL/等效 Python 实现，不能直接假定 `.sh` 可执行。

## E1. HPC 连接、计算执行与同步（用户 2026-10-19 明确指定）

### 连接与目录

- SSH 别名：`hpc`，本地执行 `ssh hpc`；完整地址 `u202520081000097@172.18.101.241`，端口 `22610`，UID `8301880`。需保持学校 EasyConnect VPN 连通。
- 本地 SSH 配置：`C:\Users\34904\.ssh\config`；专用密钥 `~/.ssh/id_ed25519_hpc`。只引用路径，禁止读取/打印私钥，禁止把 `.ssh`、密码、令牌或密钥同步进项目。
- 本地项目：`E:\gosc`；HPC 项目：`/home/u202520081000097/jupyterlab/Paper/gosc`。
- JupyterLab 文件浏览器根目录为 `/home/u202520081000097/jupyterlab`；截图中的 `Paper` 对应 `/home/u202520081000097/jupyterlab/Paper`。终端的操作系统 `/` 与文件浏览器的 `/` 不同，使用绝对路径进入项目。
- 路径配置以 `research/workspace_paths.json` 为机器可读入口，操作说明见 `research/reproduction/hpc_environment.md`。

### 强制执行地点

1. **后续本项目所有占用 GPU、CPU、RAM 的测试与训练均在 HPC 运行**，包括 CPU-only pytest、smoke test、fresh simulation、多 seed 仿真、统计/重绘、基准测试、模型推理、校准和训练。不得以“小测试”“不用 GPU”为由在本地执行。
2. 本地仅用于代码/文档编辑、Git 检查、轻量文件/哈希核验、同步与查看报告；这些轻量管理操作可以在 Windows 执行。大规模文件/数据分析同样移到 HPC。
3. VPN/HPC 不可达或远端环境未就绪时，记录阻断和原因；不得自动回退到本地跑测试或训练。旧 Windows 示例与历史本地测试日志不构成例外。
4. 本条规定运行地点，不等于授权立即开始任意长训练、依赖安装、下载模型或付费调用。用户已明确授权的实验范围内继续推进，不重复请求相同授权；超出范围仍遵守任务关卡。

### 资源及实验记录

- [RUN] 2026-10-19 只读检测：容器主机 `n1`；宿主可见 AMD EPYC 9354 共 64 核，本容器 cpuset `0-1`、CPU quota `200000/100000`，**实际 2 核 CPU、24 GiB RAM**。
- [RUN] 可见一张 NVIDIA L40，显存 `34304 MiB`（33.5 GiB）；有 vGPU 预加载，`CUDA_DEVICE_SM_LIMIT=75`，该设置不是实测吞吐。驱动 545.29.06；驱动 CUDA 能力 12.3 不等于已安装 Toolkit。
- 每次实验先重新检查实际配额；CPU 并行默认不超过 2，不能使用宿主 64 核数设置 workers。按新分配更新记录后再调整。
- 每个 run manifest 记录 SSH host、远端工作目录、commit、dirty 状态、同步 ID/哈希、环境、资源限额、seed、模型/缓存、时间和内存/显存开销；不能把过去 Windows 85 tests 记录当作 HPC 已通过测试。

### 同步与结果保护

- 本地 `E:\gosc` 执行 `python scripts/sync_hpc.py`，单向同步到上述 `Paper/gosc`。计算前必须确认本次同步 SHA-256 校验通过。
- 传输 Git bundle 保留公开项目历史，并同步当前 tracked/untracked 且未被忽略的工作文件；不直接复制本地 `.git/config`、hooks 或凭据。文本以 LF 写入 Linux，manifest 同时记录本地原始和远端规范化哈希。
- 排除 `.ssh`、密钥、`.env`、`.venv`、`.local`、缓存和 Git 忽略文件；`E:\Papers` 的私人 PDF 不在本项目同步范围内。
- 默认不删除远端独有文件；非结果文件覆盖前备份到远端 `.local/sync-backups/<sync-id>/`。遇到远端原始 `results/`、缓存或 LICENSE 差异，或 Git HEAD/origin 不一致时停止并核对，禁止覆盖来匹配本地。
- 新实验记录统一置于 `research/sync/runs/<run-id>/`，结果写入其 `outputs/`，保留 manifest、状态、日志、产物哈希和每个 seed 的原始结果。HPC 是运行事实的权威源；源码上行不得覆盖本地回传的旧状态到 HPC。取回输出使用 `python scripts/sync_hpc.py --pull-runs`。
- 多行 SSH 脚本使用 UTF-8/LF 字节输入，避免 Windows CRLF 传给 Bash。保持主机密钥严格校验。

### 每次执行的登记与两端完成状态

- 已核验 uv 0.11.19 管理的 Python 3.11.15：`/home/u202520081000097/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu/bin/python3.11`。系统 python3=3.6.9 只是控制命令的默认解释器；不要以此断言 HPC 缺少可用 Python。早前裸解释器缺少依赖；现已在 HPC 项目 `.venv` 建立 Python 3.11.15 环境，依赖导入与 `uv pip check` 通过。运行入口使用 `/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python`；精确依赖和哈希见 `research/reproduction/requirements-linux.lock.txt`，证据见 `research/sync/environment/project_environment.json`。环境就绪不代表 R1/R2/R3 已通过，需核对实际 run。
- 后续每次测试/训练/仿真/分析都用 `scripts/hpc_runs.py launch`（本地发起、HPC 计算、结束自动回传）或 HPC 的 `run` 子命令登记；运行前读 `research/sync/README.md`、`project_status.json` 和 `plans/next_steps.md`。
- 每次记录唯一 run ID、kind/stage/purpose、真实命令、seed/config/model/cache、Git 与同步快照、Python 路径、资源限额、开始/结束、退出码、stdout/stderr 和产物 SHA-256；状态为 planned/running/completed/failed/interrupted，失败与中断不得删除。
- 执行完成与两端文件同步完成是不同字段：`runs/*/status.json` 表示 HPC 执行状态，`receipts/*.json` 表示本地回传完成情况；大型未拉取输出必须明确标记，不得称内容已全部同步。
- `runs/`、`receipts/`、dashboard/STATUS 属于 HPC 运行数据通道，源码上行排除；元数据、日志和小型输出从 HPC 回传，receipt 写回 HPC。默认每次新增下载 100 MiB，需更大产物时显式设置上限。不得上传密钥、凭据或私人 PDF。
- 有 running 任务时不更新远端源码；先拉取状态并核验进程。手工绕过登记入口的任务不得推断为已完成。所有原始结果仍在 HPC 留存。

### 论文映射与审计入口（2026-10-19）

- 最新[RUN]：完整A1已完成1200条/600配对，28测试及独立审计通过；实际状态 `research/protocols/r4_a1_execution_2026-10-19.json`，报告 `research/reproduction/r4_a1_report_2026-10-19.md`。原冻结计划/预算提案保留制定时状态；下文较早的A1未执行描述仅作历史记录。B/C、独立校准、LLM及训练仍未完成。

- [RUN] 其余四场景成本探测24/24完成，17项测试及独立审计通过；报告 `research/reproduction/r4_cost_probe_report_2026-10-19.md`，完整A1预算提案 `research/protocols/r4_a1_budget_proposal_2026-10-19.json`（1200条，预计575.8s，建议上限1860s，并发2）。这是成本提案，A1/训练仍未执行；原预登记JSON保持不改。

- 当前精确原文与5式/5图/13表/Algorithm1映射：`research/logs/GOSC_paper_code_map.md`；印刷数据核对与差异：`research/reproduction/figure_table_audit_2026-10-19.md`。
- R2三plot后必须在隔离HPC副本追加 `experiments.run_belief_divergence --table`，否则TableVI留5格n/e。管理脚本已加入；历史原R2和后续补表证据分开保留。
- 多seed预登记见 `research/protocols/r4_protocol_v1.md` 与 `r4_plan_v1.json`（冻结预登记不改写）；R4-A0已完成60条mission，9项执行器测试/独立审计通过，当前事实见 `research/protocols/r4_a0_execution_2026-10-19.json`；完整A1/B/C仍未执行。主结果search候选37、rescue38；补38方案另立敏感性轨道，禁止静默改写严格复现。
- Genie是理想通信参考，不是任务最优上界。相同W或相同eta不等于相同实际资源；估值函数的price单位不同。

## F. Reproducibility First — 分阶段复现

**必须依序过关**：

1. 环境与 git manifest；
2. 运行完整测试（README 声称 85 项，**本地实际发现并执行为准**）；
3. 使用作者保存的结果重绘论文图（仅“结果重分析”，不是重仿真）；
4. 执行 fresh 单 mission；
5. 执行 GOSC/periodic/ToM/AoI/throughput 的 paired seeds；
6. 执行作者设计的 disjoint calibration / evaluation；
7. 复现 LLM cached 与 live 分开评估。

**禁止**把 cached response replay 写成“重新调用/评估 LLM”。如 HPC 无法访问 Ollama、设备不够或没有模型，必须明确“阻断”，不能偷偷退化为 Planner 再报告 LLM 效果。

保留作者合理的种子隔离：`1000–1079` calibration，`0–99` evaluation，`3000–3099` fresh validation（依据公开 README；以实际脚本核验）。新方法训练/调参不得使用原评估 seeds 或其下游强相关轨迹。

每次实验存储不可变 manifest：

```yaml
experiment_id: null
date: null
execution_host: hpc
remote_workdir: /home/u202520081000097/jupyterlab/Paper/gosc
sync_id: null
sync_manifest_sha256: null
git_commit: null
working_tree_dirty: null
scheme: null
config_file: null
config_sha256: null
python_version: null
dependencies_lock: null
os: null
hardware: null
agent_models: []
llm_cache_mode: null
seeds: []
train_calib_eval_split: null
wireless_channel: null
bandwidth_or_channel_budget: null
commands: []
raw_output_paths: []
logs: []
status: not_run
notes: null
```

“所有表格和曲线可重建”才达到稿件标准。需要保留每个任务/seed 的原始结果，任何统计均由数据脚本生成，严禁在论文图里手工改点。

## G. 第一篇论文的方法开发规则

- 优先目标：**可观测 receiver runtime state 条件下的低成本语义消息效用估计**；不是泛泛叠加多 Agent + CSI。
- 初版应**固定原 GOSC Scheduler 和 Channel**，只比较 value estimator，才能归因。
- 首先实现不依赖 LLM 的 M0（简单特征/排序/阈值），再考虑 M1 轻量模型；昂贵 M2 counterfactual assessor 必须经过成本收益门槛。
- 不允许把 `Agent uncertainty` 当真实正确率；必须说明估计/校准方法。
- 不允许无代价地查询 receiver 的私有最新内存/隐藏状态；若要共享状态，加入同步消息 bit、时延、陈旧度和可能失败成本。
- 反事实标签离线收集时，必须从同一决策前状态构造可比双分支；随机流匹配且不同 mission 的训练/测试隔离。
- 从最简单 baseline 出发，**复杂模型必须证明超出 AoI/throughput/ToM 的价值**。
- 新表示/语义压缩若没有真正引入有损重建及任务失真，不得宣传为“新型 DeepSC 编码器”。

## H. 统计、指标与公平比较

强制遵循：

- 同 Agent/LLM、同任务、同候选消息、同 seed、同信道生成、同预算；新增 Agent/LLM 调用需要计价。
- **Task quality** 是主要终点；同时报告 **channel uses/真实字节/packet success/latency/compute/tokens**，明确 uplink/downlink/headers 的边界。
- 预算必须实际相当（paired cost-matched frontier）；不要用“我方无限预算 vs 基线受限预算”进行比较。
- 统计输出最少包括 N、均值/分位数、置信区间；需要时配对 bootstrap/permutation 和多重比较校正。
- 不能因某 seed 有利就只保留它；失败、超时、模型格式错误也属于实际结果，必须报告。
- 可学习模型每次调参前固定校准数据；eval 数据只在最终报告使用，发现泄露则标记实验无效。
- 随模型、任务或信道更换，应重新核验缓存键；禁止旧缓存污染新实验。

## I. 学术写作与引文要求

- 不用其他文章已有图作为“我们方法图”；若改绘标注 inspired/adapted from 并引用、核验版权。
- 写作顺序：问题与系统模型 → 实验协议 → 方法 → 数据与统计 → Related Work → 引言 → 摘要/结论。
- 每条 claim 都要关联：论文引用 / 数学推导 / 原始实验；数字保留 baseline、单位、方向、统计置信度和图表位置。
- 禁止由 arXiv 预印本推断“已发表 IEEE 期刊”；出版状态必须核对 DOI/出版社。
- References 使用真实 PDF metadata/DOI/BibTeX（核验来源）；禁止编造 BibTeX。
- 当不同论文或代码结论冲突，主动给出冲突矩阵与证据，不要强行调和。
- 负面结果、局限性和替代解释是合格论文的一部分，不能删。

## J. 推进关卡 / 需要暂停请示的情形

立即暂停并向用户报告：

- 本地版本与研究说明/线上仓库显著不一致；
- git 工作区已有大量未提交修改；
- 原测试失败且尚未定位问题；
- `results`、缓存或 PDF 会被覆盖/删除；
- 需要大规模模型下载、付费 API、长时高资源实验；
- 修改研究问题、数据集/任务评估目标、关键数据划分；
- 在初步试验里新方法没有显著增益且估值成本更高；
- 预期数据泄露/公平性问题；
- 研究中途发现比我们更强的已发表/开源方法；
- 准备公开发布、提交论文、投稿或修改仓库远端。

## K. 每次任务最终报告（固定格式）

```markdown
# Research Task Report
- **Research Question / Hypothesis**:
- **已核验前人工作**: [PAPER]...
- **实际阅读源码**: [CODE] commit/file/function...
- **本轮新增或修改**: path + purpose
- **实际运行**: commands / seeds / configs / models
- **测试与结果**: [RUN] raw outputs + CI；未运行的明确写未运行
- **失败/负面证据**:
- **与原 GOSC 的差异**:
- **公平性与泄露检查**:
- **成本**: tokens / channel uses / time / CPU/GPU
- **可否进入下一阶段**: Go / No-Go / Pending
- **用户需要批准的下一步**:
```

## L. 研究原则（遇到冲突时优先级最高）

1. **真实证据 > 漂亮结果；科研问题 > 功能数量；公平性 > 看起来提升；可复现 > 运行速度。**
2. 先能复现上游，再谈改进；先有强基线，再谈 SOTA；先计成本，再谈效率。
3. 不凭空宣称“创新已成立”；创新是经严格比较后仍成立的差异与贡献。
4. 用户和导师对研究方向、外部调用、硬件预算、论文署名及投稿保留最终决定权。


## HPC Ollama 运行入口（2026-10-20）

- [RUN] 用户级 Ollama0.11.11 已部署，HPC回环地址 http://127.0.0.1:11434；命令 ~/.local/bin/ollama，运行库在项目 .local/ollama/runtime/0.11.11。固定旧兼容版本，不擅自升级集群驱动。
- 模型在 /home/u202520081000097/jupyterlab/models/ollama-gosc；qwen2.5:3b、llama3.2:3b、qwen2.5:7b 均为实际下载的Q4_K_M。三者均已通过完整GPU加载、JSON输出与原LLMClient空缓存HTTP验收，证据 research/sync/runs/hpc-ollama-deploy-retry1-20261020/outputs/。记录实际digest，不能假定与作者历史模型快照一致。
- 服务配置位于HPC项目 .local/reproduction-services.json；单并发、同时最多加载1模型。退出SSH后服务保留；容器/服务器重启后通过 .venv/bin/python scripts/hpc_ollama.py start 重新启动。操作说明 research/reproduction/ollama_hpc.md。
- 只有环境验收完成，完整live LLM复验仍需按原顺序单独登记，保持缓存回放与真实调用分开，禁止planner回退冒充模型成功。旧队列在c-belief失败已保留；外层入口适配器修复并通过10项HPC回归，续跑使用新runID，不覆盖失败记录或重复已完成阶段。
- [RUN] 用户授权清理其他项目以恢复配额；仅Github--llm和HM已删除，预删除占用合计26058240000bytes；当前Paper/gosc与已有models保留。清理证据 hpc-ollama-storage-cleanup-20261020；不得据此自动删除其他新目录。


## 当前进度权威索引（2026-10-20进度复核）

详见research/reports/progress_review_2026-10-20.md与research/sync/plans/next_steps.md。原23阶段队列4执行完成、1失败、18未运行，当前无活动复验；Ollama与3模型就绪，完整cached/live任务仍未运行。公开选参26700完成/22条历史差异/12冻结点匹配；选参后fresh1200与保存输出匹配；C-frontier6800、C-where5000完成执行但有479/364条历史差异（完成时间228/146），不能标为科学一致性通过。下一步先完善比较器覆盖并诊断差异，再以新runID显式恢复c-belief→其余原顺序阶段。0共同键不得作为历史一致证据。上游校准缺口保留。P2文献/RQ可并行，未启动新方法训练。早先段落与历史日志的旧状态不覆盖上述实际run证据。


## 当前进度更新（2026-10-20顺序续跑与P2）

本段优先于上文“4完成/未续跑/P2待做”的历史状态。新报告research/reports/resume_and_literature_2026-10-20.md；P2索引research/literature/reading_review_2026-10-20.md。比较覆盖保护已修正；36个受控诊断确认部分数值分支敏感但未完全解释selection/C历史差异，正式NumPy2.4.6不改。resume-c-belief-20261020完成1400项，1400共同键/0差异；resume-c-analysis-20261020完成原函数10000 bootstrap，均已回传。原6阶段执行完成不代表C历史科学一致性全部通过。

后续已获本轮用户授权按原顺序继续17阶段，入口scripts/repro_resume.py resume，父run hpc-ordered-resume-20261020；实际状态以该run及子run台账为准。跳过6个已完成阶段、保留旧失败，不重建工作区；原72h截止2026-10-22T10:36:15.888633Z，不重置。CPU workers2、数值线程1；现实链路候选124400，fresh上限10300且运行前由完成grid冻结精确任务/config/seed，并与原生pool目录核验。新增HTTP观察只记录原LLM调用tokens/attempt/latency/格式错误，不改变原prompt/options/retry策略。

本轮P2交付已完成启动10篇及D08/D10/B10共13篇笔记、Gap Matrix、RQ_v1和拒稿自查；长综述为注明范围的重点阅读，非42篇全读。D02已经提出receiver-context distortion/匹配反事实credit，BANDMAS/ToM2C/iCoTASC有直接机制先例，不得主张思想首次。新RQ仅为可观测摘要+陈旧/同步/估值成本下的可证伪净收益问题。新方法实现/训练未启动，待P1边界和M0 headroom协议审阅；私人PDF不入同步。

## M. Git 提交说明（用户 2026-10-22 明确指定）

- 每次 Git 提交都必须先在根目录 `commit/` 新增带日期的 Markdown 说明，与本次代码/文档改动一起提交；包括文档、修复、回滚等提交，不得省略。
- 文件名 `YYYY-MM-DD-NN-简短主题.md`，日期按 Asia/Shanghai，同日递增序号；保留旧说明，不覆盖。内容及模板见 `commit/README.md`，每次同时更新其索引。
- 说明至少写日期、目的、分支/基线版本、改动范围、实际验证与证据、失败/未完成项及后续事项；区分本次检查与此前 HPC 结果，不能将计划或旧结果写成本次已验证。
- 提交信息包含 `Commit-Note: commit/<说明文件名>`。自身提交哈希通过 Git 历史关联，不为补写自身哈希制造额外无说明提交。
- 提交前检查忽略项、暂存区、凭据/私人文件、大文件与 `git diff --cached --check`；不强制加入忽略的原始输出。用户已授权的提交/推送直接执行；不得强制推送或擅自合并到其他分支。
- 历史运行日志或源码补丁的空白提示单列说明，保留原始证据；另对当前源码/文档核对空白检查，不能为了全量检查变绿而改写旧实验记录。
