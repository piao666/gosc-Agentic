# 2026-10-26 / 01：因果服务、独立校准及age机制审查归档并推送

- 日期与时区：2026-10-26，Asia/Shanghai。
- 目的与授权范围：用户要求“先提交一次github，保持工作区干净”。一次新提交归档10月24–25日连续任务成果，普通快进推送当前研究分支；此前未推送祖先47389eb随历史一同推送。不强推、不合并main，不新增科研运行。
- 分支：`research/progress-audit-2026-10-19`。
- 本地基线：`47389eba9c6e2838139df3aa47863ab88634e97a`；本轮只读查询并fetch的远端同分支为`4ff4147654c07781d77a42acee3f31c0b8792f38`，是本地严格祖先。
- 自身提交/推送身份：通过包含本说明的Git历史和远端引用核对，不回填自身提交哈希制造额外提交；最终结果在用户回复中报告。

## 改动范围

1. GP-v2独立命名因果服务：统一task/summary解码反馈下界、共享CPU估值预留、有界盲目catchup；paid-ignore/age/shuffle对照。旧GP-v1默认构造路径通过两个短fixture与归档源码全字段比较；不是全历史/作者旧wire等价证明。
2. 保留21候选/214world冻结、原预算blocked、用户明确批准1200s修订、42短probe、252校准任务（独立N12）、独立账本/CI/N/前沿/消融审计与图表来源。原始outputs继续Git忽略。
3. 摘要成本/age机制审查：精确UL费用、DL保守识别界、编码预留/任务重播、固定轨迹账本敏感性和1536合成选择器比较；新协议仅审阅候选。
4. 测试、分析/复算脚本，协议、报告、任务brief/commands/delivery、HPC manifest/status/log/source snapshot/receipt和导航状态。`gosc/experiments/tests/results/LICENSE`未修改。
5. `.gitattributes`只对上述新HPC run与10月24–25日新receipt禁用文本换行转换，保留证据原始字节；这些路径此前未被HEAD跟踪，不对旧运行记录批量正规化。R2/R3既有字节保真规则保持。

## 实际验证与证据

### 本次Git/文件管理检查

- 实际执行`git status --short`、`git rev-parse HEAD`、`git remote -v`、`git ls-remote --heads origin`、指定分支fetch、`git merge-base --is-ancestor`与提交差异/忽略检查。没有活动自定义Git hooks，提交不触发本地项目测试。
- 首次文件清查179候选文件/348482565bytes，最大单文件21260683bytes，主要为16份保留的HPC source_changes.patch；均小于50MiB，无模型/环境加入。16份新增源码tar.gz、298成员均检查，未发现高置信度私钥/token/敏感路径或私人PDF候选。不是绝对无敏感信息的保证。结果见`research/logs/git-publish-2026-10-26/precommit_file_audit.json`；该清查在新增本说明等管理文件前取得，最终范围以暂存审计和Git提交为准。
- 暂存区范围/证据字节/忽略项/大文件/白名单与空白检查记录在同目录`staged_audit.json`。原始历史patch空白提示单列，不为通过检查改写证据；当前源码/文档另行核验。自身审计文件不自哈希，最终提交身份通过Git验证。
- 实际暂存审计快照183文件（加入自身结果前）：135份新增HPC证据blob逐字节SHA与原文件一致，0差异；ignored/敏感路径、受保护上游、删除、>=50MiB文件均0。默认`git diff --cached --check`退出2，2,410,734提示均来自16份不可变source_changes.patch，主要为原CR字节；`core.whitespace=cr-at-eol`后仍174提示、同16文件。排除运行/日志证据的当前源码/文档检查退出0。原补丁字节保留，不宣称全量默认空白检查通过；加入审计结果及本段管理说明后再核对当前文档/暂存范围。
- 本次不重跑HPC pytest/仿真/统计，不新增LLM、模型下载或训练；下列科学结果均是之前的登记HPC运行，不冒充本次新结果。

### 此前HPC证据（本次未重跑）

- [RUN] GP-v2主回归187项、补充28项（含重复，共190不同测试）；旧GP-v1两个16slot短fixture与47389eb源码结果全字段相等。见`research/reports/causal_service_progress_2026-10-24.md`。
- [RUN] 预算修订获用户明确批准；21候选×12新world共252任务447.369435s完成，950281事件/CI/N/前沿/消融独立复算通过。pose较periodic快8.6667slots，但通信比1.606664/逻辑CPU比2.813743；较public快8.3333slots，成本比3.018507/3.481296。联合实际成本支持未达，规划N21907>200上限，科学No-Go。见`research/reports/causal_calibration_audit_2026-10-25.md`。
- [RUN/CODE] 成本/age审查18合同、原数据分析、1536合成选择器比较与独立复算通过，新mission/N0；摘要UL20516uses占全通信34.27%，全部免去UL费用的固定轨迹账本仍超主要阈值。age理想目标等价动态price，但native-age对照/历史factor和DL类型未记录。见`research/reports/summary_age_mechanism_review_2026-10-25.md`。
- [RUN] 本次三个delivery对应的完整回传receipt保留；校准及审查原始输出在HPC和本地镜像，不强制加入被忽略outputs。原R2/R3白名单47文件随父提交47389eb推送，不重写原始run身份。

## 未完成项、负结果与限制

- GitHub归档不等于科学关卡通过。GP-v2正式test、扩样本和训练仍No-Go；native-age/显式动态price及新观测合同仅review_candidate，未实施/运行。
- 旧作者校准/cache生成链及历史数值差异仍部分通过，未证明付费摘要或真实LLM任务净收益。既有报告“未提交/未推送”保留当时含义，以本次提交说明与Git引用识别版本归档状态。
- CPU逻辑预留与实测process/wall分开，DL界不是CI或精确分类；不把账本费用删除当可实现免费通信，不把合成选择器一致当所有闭环逐位等价。
- source_changes.patch等不可变运行证据可产生空白检查提示；不删除、重写或忽略其不利科研记录。

## 后续事项

本次普通push后确认远端分支HEAD等于本地HEAD、`git status --porcelain`为空。不再修改已提交文件来回填自身哈希或推送时间。后续如继续研究，先审阅native-age/动态price最小对照及前瞻观测合同，再决定新协议/预算；本次Git授权不包括自动实施新实验。

## Research Task Report

- **Research Question / Hypothesis**：本轮仅版本归档，无新科学假设。
- **已核验前人工作**：[PAPER] 未新增原文核验，沿用既有纸码映射。
- **实际阅读源码**：[CODE] 47389eb后扩展点diff、Git忽略/属性及归档/运行入口；无核心方法改动。
- **本轮新增或修改**：本说明/索引、归档导航、Git审计凭据及证据字节属性；归档既有连续任务改动。
- **实际运行**：本地Git和文件/归档/暂存检查，普通commit/push；精确阶段检查见本任务日志。
- **测试与结果**：[RUN] 本轮未运行项目测试/实验；已完成HPC结果如上，最终提交/远端/clean结果由Git核验。
- **失败/负面证据**：科学No-Go保留，历史空白提示单列；不将其伪作全量检查通过。
- **与原GOSC的差异**：归档GP-v2扩展，原上游核心代码/结果/许可证不变。
- **公平性与泄露检查**：仅当前授权源码/报告/元数据；ignored raw输出/凭据/私人PDF不加入；原边界不改。
- **成本**：Git/文件管理；0新HPC计算、0LLM/token、0训练。
- **可否进入下一阶段**：版本归档可交付，科研正式验证/训练仍No-Go。
- **用户需要批准的下一步**：本次提交/推送已明确授权，无需重复批准；新研究实验另作决定。
