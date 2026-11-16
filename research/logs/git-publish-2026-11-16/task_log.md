# Git管理记录 — 2026-11-16

用户要求整理文件并提交一次GitHub。基线4754bed、当前研究分支research/progress-audit-2026-10-19；ls-remote证实远端同SHA。已有dirty均为已完成研究/管理成果，保留不reset/checkout/clean，不移动冻结源码或原输出。

本次组织为：固定五章节commit说明与索引、阶段摘要及两级README入口、6份原outputs逐字节白名单/provenance；原源/报告/日志/manifest/status/source_snapshot与receipt按既有路径归档。12个重复source patch/tar计358,066,710bytes保持忽略，原件本地/HPC不删除；不force-add outputs、模型或环境。

只对新路径追加-text，保存新证据raw SHA，不重新规范化旧tracked文件。前置约11MB未归档文件最大为约1.2MB回传receipt；不是模型数据或新的任务成绩。白名单6份10,454bytes，索引绑定源artifact SHA；17、最终24、前序20/22/23与旧147+5严格分开。

本次实际验证仅Git和轻量文件/哈希/Markdown/说明格式/凭据/大文件检查。73冻结源码与最终执行代码校验，不重跑HPC合同、不调用模型、不安装或清理其他项目。quota和同步失败、用户清理/停止服务授权及最后901文件源校验都保留，科研No-Go不因提交改变。

暂存核验后将7份约8.47MB重复全历史transfer inventory改为原件SHA/大小及本轮文件条目的receipt_index；原件保留本地/HPC，新忽略规则仅影响Nov10新receipt，不删旧tracked历史。原始记录两处空白提示（failed final_upload_stderr.txt尾空格、preflight_observed.json末空行）单列保留；自有源码/文档排除这两个精确原件后检查，不改证据来变绿。

检查具体结果见precommit_file_audit.json、staged_audit.json；如发现stage换行差异，只处理本次新增路径，不改历史原件。最终一次普通commit/push后核远端同SHA与工作区状态，不为回填自身哈希制造第二次提交。之后HPC科研工作应先核新的Git/source同步身份，本次不自动更新HPC Git或运行科学任务。

最终管理核验：blockers0、73冻结源不变、3个集成Python与v4执行快照一致、6份输出及7份原receipt指纹一致，新stage blob保持raw bytes，无删除/模型/环境/私人PDF/忽略输出。原始全量空白检查exit2仅对应上述两个精确原件；排除它们后exit0，证据未被修饰。整理后暂存约3MB、最大单文件约0.29MB；最终路径数量以Git树与staged_audit为准。实际提交前再核origin仍为base，再一次commit/push并读回Git远端引用；没有追加HPC测试。
