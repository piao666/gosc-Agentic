# T3-R-v2 HDD复用与SSD空间保护

2026-11-26 Asia/Shanghai。用户已授权复用HDD/迁移部分文档以保持SSD余量；此为存储授权，不是模型生成、服务切换或资源保证降级授权。

## 当前落地

[RUN/管理] 3类非活动项目管理文件已无损迁到`/hdd/u202520081000097/gosc-admin-archives/20261126-deployment-admission/`：diagnostic-wheels、git-checkpoints、sync-backups，共634文件/87764721B。所有目标重新读SHA通过后才去除SSD源副本；三个原目录均留`ARCHIVED_HDD_20261126.json`恢复索引，没有symlink。当前源码、Git索引、registry及历史run位置未改。

逐文件路径/大小/SHA/mtime/mode与原路径恢复映射见[迁移计划](../logs/masbench-storage-hdd-2026-11-26/migration_plan.json)，[实际回执](../logs/masbench-storage-hdd-2026-11-26/migration_receipt.json)与[独立读回](../logs/masbench-storage-hdd-2026-11-26/independent_readback.json)。本地只回传管理清单，不公开包含旧内容的HDD归档。

## 后续布局（待接入具体新执行入口，不冒充已自动强制）

| 内容 | 位置 | 保护 |
|---|---|---|
| 活动checkout、.git、.venv、既有模型/服务 | 保持当前路径 | 不通过迁移在用环境解决配额；源码/模型SHA绑定照旧 |
| 新run的manifest/status/stdout/小索引/receipt | 既有`research/sync/runs`数据通道，SSD | 新原始大文件不混进stdout；受阶段SSD上限和个人quota约束 |
| 新原始请求/响应/frames/fixture临时树/大型审计证据 | 独立新HDD run目录 | 必须由新入口显式绑定，逐写收费、预算/原路径映射、全量SHA回传；不依赖symlink |
| 非活动同步备份/Git管理副本/下载归档 | HDD专用管理归档 | 先复制/fsync/逐件读回/manifest，再去SSD副本；没有删除证据 |
| 已有实验原件及历史run元数据 | 保持原路径 | 本轮不移动/改写，原结果和历史身份继续成立 |
| 当前研究说明/规格/报告源码 | checkout继续保留 | 不为省小量文字空间打断Git/同步；其历史备份可有HDD位置索引 |

新执行前核个人quota（不是共享df）：16MiB无模型阶段要求SSD可用>=32MiB；32MiB真实候选阶段要求>=64MiB。阶段内逐写预留与清理/失败空间分开，低于剩余写入需求+保护空间就停写/停派发，保留前缀；不能先写满再删失败。本文不是常驻清理任务，不创建自动删除/cron；下一入口必须真实接入这些检查才可称强制。

当前核验SSD余95662080B（91.23MiB），超过上述准入阈值，但**未达理想1GiB缓冲**。本轮安全白名单已迁完，不扩大到其他项目、实验结果、模型或环境来凑1GiB。后续大产物放HDD，SSD在新阶段最多按冻结16/32MiB消费；空间变化以执行前重新核验为准。

未来标准sync仍可能在`.local/sync-backups/<新sync-id>`生成小型覆盖前副本，这是原脚本安全行为；新备份可按本次同等copy/SHA/receipt协议定期有界归档到新HDD批次，不覆盖本次目标、不自动重跑一次性脚本。原sync_hpc.py未修改，不能称其已永久改用HDD。

## 回滚与故障

从迁移计划取一条source/target，仅在source不存在、目标SHA匹配、源SSD空间足够且路径非symlink时原样复制回原路径，恢复mode/mtime，fsync后复核SHA。若原路径已有新文件，禁止覆盖；HDD原件始终保留。无需回滚时不把全部归档再复制回SSD。

本次无测试/模型/服务调用；storage Go仅表示本轮迁移与当前容量门核验通过。真实部署仍有独立live入口、硬资源与16384逐请求绑定/退出回滚等未通过项，GPU/RSS监测候选并未获批，不因此进入T3能力诊断或T4。
