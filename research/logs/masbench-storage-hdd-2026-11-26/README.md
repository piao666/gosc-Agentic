# HPC HDD复用与SSD恢复证据

2026-11-26 Asia/Shanghai。用户已授权存储处理。本轮只迁移非活动管理归档，634文件/87764721B全部保全；当前SSD个人余91.23MiB。storage Go，真实部署其他关卡不放行。

- [最终报告](../../reports/masbench_t3rv2_storage_resolution_2026-11-26.md)、[后续布局/空间门](../../protocols/masbench_t3rv2_hdd_storage_policy_v1_2026-11-26.md)
- [任务brief](task_brief.md)、[任务日志](task_log.md)
- [HPC原始迁移计划](migration_plan.json)、[复制读回证明](copy_verified.json)、[实际迁移回执](migration_receipt.json)、[每件去源记录](removal_journal.jsonl)
- [独立634项读回与当前quota](independent_readback.json)、[原始远端凭证SHA](hpc_receipt_sha256.txt)、[双端管理回传凭证](transfer_receipt.json)
- [迁移工具](relocate_archives.py)、[独立读回工具](verify_archive.py)：只执行本次固定白名单，不能自动重跑同一目标。
- [既有交付保护](protection_check.json)、[交付SHA](delivery_manifest.json)

HPC原件及完整旧管理归档保留在`/hdd/u202520081000097/gosc-admin-archives/20261126-deployment-admission/`；原3目录留恢复索引。历史研究/旧run原件不动，19项HPC保护SHA和前序62项本地交付保持不变。没有真实模型、HTTP或服务操作；没有新pytest/科学测试、提交或push。

未对GPU/RSS监测替代硬隔离作默认批准，也未通过16384真实运行、退出/回滚等验收。部署准入原Blocked报告保留当时含义；最新变化只解除SSD容量阻断。
