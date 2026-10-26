# Research Task Brief — 2026-10-26 GitHub归档与干净工作区

- 用户授权：“先提交一次github，保持工作区干净。”本轮将既有实现、报告、协议、运行元数据/源码快照和审计凭据整理为一次新提交，正常推送当前研究分支；包括此前未推送的祖先47389eb，不强推、不合并main。
- 科学问题：[HYPOTHESIS] 无新增科学问题或实验。本轮只归档已验证事实，不修改No-Go、原始数据、旧失败记录或历史run身份。
- 前人成果：[RUN] 既有GP-v2 252校准任务/N12和成本/age审查；190不同历史合同及本轮前序18新增合同属于此前HPC证据，当前不重跑、不做训练。[PAPER] 本轮不新增论文核验。
- 启动：[CODE] 当前branch research/progress-audit-2026-10-19，HEAD47389eba9c6e2838139df3aa47863ab88634e97a；origin为用户指定仓库。已有dirty是本连续会话授权成果，提交请求覆盖其归档处理，不reset/checkout/clean/删除。
- 文件：新增commit/2026-10-26-01-causal-service-and-age-review.md并更新commit/README索引，添加本任务轻量Git/文件/归档/暂存审计凭据；必要更新最新状态入口的归档指引，不回写历史报告的“未提交/未推送”。
- 验收：远端分支为本地严格祖先；所有非忽略变更经范围/大小/凭据/私人文件检查（含新增源码tar.gz成员）；没有原gosc/experiments/tests/results/LICENSE修改或ignored outputs被强行加入；暂存diff和历史空白提示分开；原始证据不为检查变绿而改字节。提交含Commit-Note，普通push成功、远端HEAD与本地相同、git status --porcelain为空。
- 成本：本地Git/轻量文件管理；0项目测试、0HPC计算、0新仿真/LLM/训练，不安装依赖。大型原outputs继续忽略，不为本次归档强制上传。
- 反例/失败处理：遇远端新工作、密钥/私人PDF、超大blob或push拒绝，保留文件与本地提交并处理阻断；不强推或删除成果以制造clean。
- 自身提交哈希由Git历史关联；本任务说明/审计在提交前写好，提交/推送后不因补写自身哈希再制造额外脏文件或额外提交。

## 本次实际管理检查

- [CODE/RUN] 本地HEAD47389eb、origin同分支4ff4147是严格祖先；指定fetch未合并工作树。无活动自定义hooks。
- 文件/源码归档检查结果precommit_file_audit.json：16包298成员，未发现高置信度credential/private-PDF/敏感路径，最大单文件21260683bytes；更新管理说明后按原内容SHA复用不变文件扫描结果。
- staged_audit.json的183文件快照（自身审计加入前）：135份HPC证据blob字节一致，0强制ignored output/受保护上游/删除/>=50MiB文件。
- 全量空白检查退出2，16份历史patch共2,410,734提示，cr-at-eol后174；当前源码/文档范围退出0。保留历史证据字节，`.gitattributes`仅为新证据路径禁用换行转换。未执行任何本地/HPC项目测试或科研计算。
- commit/push/clean以最终Git命令和用户回复报告，不为回填自身哈希另作提交或留脏文件。
