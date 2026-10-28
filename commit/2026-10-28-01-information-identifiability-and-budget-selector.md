# 2026-10-28 / 01：信息价值识别校准与预算selector验收归档

- 用户要求：“将这几轮的结果梳理一下，提交到github”。本轮在当前`research/progress-audit-2026-10-19`分支一次commit及普通push，不强推、不合并main、不新增科研运行。
- base HEAD及只读查询/fetch的GitHub分支HEAD均为`253a14b19c4410a4606a40c98b8ba24791c7ee43`。自身提交/推送身份以包含本说明的Git历史及远端引用核验，不回填自身哈希制造额外提交。
- [阶段汇总](../research/reports/recent_rounds_summary_2026-10-28.md)清楚区分GP-ID成本合同、156任务独立校准科学No-Go、7次原selector违规与BF独立版本工程Go。原上游`gosc/experiments/tests/results/LICENSE`不修改。

## 已完成成果（引用既有HPC运行，本轮未重跑）

1. GP-ID-v1机制对照/前瞻typed观测：343测试、52短成本fixture及独立审计，效果N0，1825同目录比较0差异不证明普遍等价。
2. 用户明确批准2400s/384MiB后，13方案×12全新world=156任务在777.088717s完成。5主要比较0组过联合门槛；paid-pose对periodic平均慢33.833333slots，通信/逻辑CPU比2.142032/3.664153，科学No-Go。
3. 原严格审计发现bits6/AoI1次选包>100，最大304；初始二分hi不可行。诊断全量复算账本/统计仍blocked_selection_budget，原失败不改写。
4. 独立BF-selector-v1/显式GP-ID-BF-v1：最终485完整HPC测试、7违规修复/192可行目录兼容、52短fixture及独立原始行/预算/组/成员/CRC/typed账本审计通过；补7个明确派生control-only修复到wire合同通过。主验收37.690869s，收益N0，旧默认/科学No-Go保持。
5. 四份写作内核、P1缺口清单、审阅/实施规格、预算提案/批准及冻结/执行索引、全部失败/红测试与HPC运行元数据/日志/源码快照/receipt均归档。

## 结果和证据的公开边界

- [8份小型汇总JSON白名单](../research/artifacts/gp-id-bf-20261027/README.md)由既有HPC原件逐字节复制，来源/大小/SHA在provenance.json；不新算统计、不改变状态。
- 原`runs/*/outputs/`和`pytest-tmp/`继续忽略；完整轨迹/raw数据留HPC及本地镜像，不能把8份汇总称完整原始数据公开包。不加入模型、缓存、环境、凭据或私人PDF。
- `.gitattributes`只对本次新information/budget-selector运行、10月27日新receipt和新白名单禁用换行转换。此前HEAD无这两类run，不批量规范化旧证据。暂存后逐blob核验源字节；不为消除patch空白提示改写原件。
- 科学结果的commit/dirty/sync身份仍是各run原manifest；本次归档提交不回填历史run，也不冒称运行时已使用本提交。

## 本次管理验证

- 本地执行Git状态/HEAD/remote、ls-remote、fetch和历史关系核验；无活动自定义hooks。当前分支普通快进推送，不新建PR或修改remote。
- 首轮候选清查439文件、808,519,731bytes，最大单文件21,282,462bytes，全部小于50MiB；399份独立内容及tar成员检查未发现高置信度私钥/token/敏感路径/PDF候选。是有范围的检查，不是绝对无敏感信息保证；记录在[文件审计](../research/logs/git-publish-2026-10-28/precommit_file_audit.json)。清查在本说明和最终导航加入前进行，最终范围以暂存审计及提交为准。
- 暂存审计/证据逐字节检查与当前源码文档空白检查见同目录staged_audit.json和管理记录；不可变source_changes.patch可能产生历史CR/空白提示，单列保留，不宣称全量默认空白检查通过。
- 本轮不执行HPC测试/仿真/统计/训练，不更新HPC运行状态；下一科研运行前仍需核对HPC Git身份及同步manifest。当前科研证据仍来自既有run，不能把Git归档当新验收。

最终暂存审计快照441文件/809,098,412bytes，332份证据blob与工作文件逐字节SHA一致，0差异；敏感路径/高置信度凭据、删除、受保护上游改动及>=50MiB单文件均0。当前源码文档的CR-at-EOL-aware空白检查通过；默认局部检查将新provenance.json的CR字节报作尾空白，未通过改写证据来消除提示。全量不可变run补丁空白未重新检查。加入审计结果和管理核验记录后最终文件数以Git提交为准；自身审计不自哈希。事实见research/logs/git-publish-2026-10-28/staged_audit.json与git_management_verification.json。

## Research Task Report

- **Research Question / Hypothesis**：整理可复核的阶段结论与版本，无新科学假设。
- **已核验前人工作**：[PAPER] 无新增论文核验。
- **实际阅读源码**：[CODE] 253a14b后扩展/测试/脚本diff与归档配置。
- **本轮新增或修改**：阶段汇总、本说明、8份小型汇总副本、导航/字节属性/Git管理审计，归档前几轮全部任务改动。
- **实际运行**：本地Git、文件/归档/哈希/暂存管理，普通commit/push；精确事实由Git及审计文件核对。
- **测试与结果**：[RUN] 本轮未运行项目测试；既有485测试和校准/审计事实如上。
- **失败/负面证据**：No-Go、预算超限、原严格审计失败、测试替身/夹具失败全部保留。
- **与原 GOSC 的差异**：独立研究扩展归档，原版代码/输出/许可证保持。
- **公平性与泄露检查**：没有新样本/调参；raw outputs仍忽略，敏感路径/凭据/归档成员已检查。
- **成本**：Git/文件管理；0新增科研运行、LLM/API/训练/GPU。
- **可否进入下一阶段**：Git归档可交付；研究正式test/扩N/训练仍No-Go。
- **用户需要批准的下一步**：本次commit/push已明确授权；新收益实验另行决定。
