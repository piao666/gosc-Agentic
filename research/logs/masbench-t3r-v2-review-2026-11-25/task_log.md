# Research Task Log — T3-R-v2冻结前审查

2026-11-25，Asia/Shanghai；本地host=Windows管理端，cwd=`E:\gosc`。无HPC新run，故没有虚构run ID或资源测量。用户本轮授权只读审查/分组元信息/文档/Git/SHA；此前一次Git发布已完成，本轮明确不授权commit/push。

## 1. 启动与来源

完整阅读AGENTS、研究总说明书、指定T3-R A/B/C/D、旧审计README/验收矩阵与来源字段；结合README/最近任务记录及`research/sync/plans/next_steps.md`、`research/sync/project_status.json`当前入口，不执行其旧运行计划。按ARS科研审查的证据/负结果原则组织材料，不以skill扩大本轮授权；无子agent或跨模型审查。

本地HEAD与GitHub研究分支核验为f91d01070740703dc1ee845510569c0b31e66c51；当前remote为既有piao666/gosc-Agentic，未修改配置。历史T3仍为b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0+20261125T034132Z；旧manifest/snapshot/授权各自SHA列在source_inventory。新归档HEAD不回填旧运行。

三项既有untracked保持：.workbuddy/、11-17审阅任务安排.md、T3-R_科研失败归因与研究前提复核任务书.md。沿用用户保留原样/仅新增产物许可。没有清理、覆盖、重命名、add、commit、push；.workbuddy未读取。所有写入仅本轮四交付和本目录。

## 2. 实际命令与工具（重复读取合并；非完整终端转录）

只读Git命令：

```text
git status --short
git rev-parse HEAD
git branch --show-current
git remote -v
git diff --stat
git ls-remote origin refs/heads/research/progress-audit-2026-10-19
```

最后一条CLI退出1：getaddrinfo() thread failed to start。改用GitHub连接器只读 `search_branches(owner=piao666, repo_name=gosc-Agentic, query=research/progress-audit-2026-10-19)` 与 `compare_commits(base=f91d01070740703dc1ee845510569c0b31e66c51, head=research/progress-audit-2026-10-19)`；返回identical、ahead0/behind0、merge-base=f91。结果保存在git_identity_check.json；没有任何远端写入。

文本定位/阅读实用命令包括：

```powershell
rg --files -g AGENTS.md -g '!research/sync/runs/**'
rg --files research/reports | rg 'masbench.*(t1|t2|t3)'
rg -n '^def |^class |^    def ' extensions/masbench_reasoning/*.py
Get-Content -LiteralPath AGENTS.md
Get-Content -LiteralPath 硕士论文研究与实施说明书.md
Get-Content research/reports/masbench_t1_validation_archive_2026-11-19.md
Get-Content research/reports/masbench_t2_context_acceptance_2026-11-25.md
Get-Content research/reports/masbench_t3_execution_2026-11-25.md
Get-Content research/protocols/masbench_t3_execution_authorization_2026-11-25.json
Get-Content research/logs/masbench-t3r-2026-11-25/README.md
Get-Content research/logs/masbench-t3r-2026-11-25/acceptance_matrix.md
```

上述rg函数定位实际按application/client/evaluation/registry/wire/live_driver等文件组分次调用；Get-Content结合数组切片读取函数段，指定A/B/C/D也完整分段读取。只对索引/汇总字段投影，不打印私有正文。Source inventory通过 `Get-FileHash -Algorithm SHA256`、ReadAllBytes和仅LF规范化的SHA比较生成；snapshot仅按已知path查九项源哈希。D1附件通过 `Get-Content ...preflight.json | ConvertFrom-Json` 后投影data.all、D1_reserved、D1_remaining，不读取reasoning.json/未解封题目、不重跑registry builder。

写入工具：apply_patch新增四交付/任务文档；只对四份本轮新文档用ReadAllText/WriteAllText修正源码行范围到实际EOF（registry153、client383、evaluation85、reference conversation215、T3 launcher276）。无科学计算或测试命令。末态轻量检查在closeout_checks，交付SHA在delivery_manifest。

额外轻量字节操作：提取规格首个text围栏中的System模板，仅作Alice/Bob字面替换及SHA；生成固定六项公共时钟JSON/SHA，写prompt_contract_hashes.json。没有实例化LOCAL_TASK、运行tokenizer或修改真实Prompt。角色System分别2553/2549 UTF-8 bytes，不是token计数。`scripts/hpc_ollama.py` LF哈希f3afc556d9b47f64351e22988ea120ef84df1c5373175e0ca77aecc69af48bba与旧授权pin一致；原始CRLF哈希仍单列，不以此替代新运行绑定。

## 3. 审阅路径及发现

1. A：旧run_controlled遇A停且不能提供独立双final；形成唯一字面模板、六slot、全串标签与无板规则，不动实际代码。旧事实/错误事实不oracle处理，控制表无事实、final不互传。
2. B：新指标是双本地final家族均值，与旧团队答案不同；固定人工red/blue向量检查失败分母与重复词公式，不执行测试。有效子集受处理影响，不代替总体主指标。
3. C：既有聚合足够，保留52/36/34池；两ineligible不能假装都可用。新增开发需整分量扣除；不提供新题号/排序。
4. D：从源码发现每清理epoch是1+6次GET；生命周期GET在旧Driver外。给50生成/50render/358GET/10unload=468 HTTP计划；50helper另列。19100s重新分账，显存采样不是硬限额，新计数器/最坏输入/部署/回传仍缺。
5. E：保留旧C的2家族双EM、0.10、2正差及L1/L2门为未批准候选，解释事后风险与回答率混杂；不换指标/题目/模型凑Go。

## 4. 失败、支持域与实际成本

PowerShell默认profile引用不存在的外部openclaw脚本，早期调用有profile警告；后续使用login=false跳过profile，不修改用户profile。CLI网络身份读取失败由连接器只读比较解决，不请求推送或其他写权限。部分大段工具输出被截断，随后按函数段/特定字段读取，未据截断宣称通读所有684正文。

另有两项无副作用定位问题：rg接收Windows路径内嵌`*.json`字面glob报os error123；改用目录+`-g`/明确文件读取，未据失败作内容判断。旧入口`plans/next_steps.md`不存在，rg定位到实际`research/sync/plans/next_steps.md`后读取当前段，原文件未移动。时钟OrderedDictionary直接Select-Object显示null仅是终端投影问题；随后读回JSON确认六项turn/literal/SHA完整，不重生成科学数据。

T1 EDQUOT/未知usage/runner漂移、T2的60秒真实超时和T3科学No-Go保留；新文档不冒充修复。新版32项合同均未运行；无pytest、统计重算、模拟、helper token计数、HPC命令、服务GET/POST、部署切换或模型生成。新增推理tokens/channel uses/模型费用=0；本地编辑/管理CPU与墙钟未仪器化，GPU峰值未测。GitHub连接器仅取仓库ref，不上传研究数据/私有文件。

## 5. 交付与停止

四份指定交付及任务附件见README。静态方案Conditional Go；实现/无模型合同Pending且无授权；真实运行Blocked；任务能力/消息内容价值/无线净收益均未建立。原T3/G1/GP-ID No-Go与D1不变，T4/校准/封存test/训练不启动。

完成轻量交付检查后停止，等待研究者审阅；本轮没有提交或推送Git。任何未来受限实现与无模型合同也需新授权，真实生成另批。
