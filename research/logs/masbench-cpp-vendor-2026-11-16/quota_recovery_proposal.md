# 本轮管理快照无损压缩提案（尚未执行替换）

2026-11-16。[RUN] 预览见 `snapshot_archive_preview.json`，本地原件复核见 `local_snapshot_verification.json`。

仅限这两份JSON列明的7个run目录中的 `source_changes.patch`：5次Go/helper失败构建、2次C++/vendor准备。原件433,544,727bytes；临时盘gzip副本67,124,966bytes；逐份解压SHA-256与原件及本地回传原件一致。将HPC原件替换为同目录 `source_changes.patch.gz` 后预计释放366,419,761bytes（349.45MiB），不保证满足后续全部构建配额。

申请执行范围：

1. 逐份再次验证原件SHA、压缩副本恢复SHA及本地保留原件证据。
2. 将已核验gzip复制到原run目录，fsync后再核验；新增归档侧车JSON，记录旧路径/大小/SHA、新路径/大小/SHA及 `gzip -dc source_changes.patch.gz > source_changes.patch` 恢复方式。
3. 仅移除同目录已验证的未压缩patch副本。本地7份未压缩原件继续保留。每份操作失败即停；不删除结果、日志、模型、缓存、许可证或其他项目。
4. 保留v2原始running状态副本及配额失败证据；核实无进程后新增纠正记录，将状态标记为失败，明确原收尾缺失，退出码/精确结束时间若未找到则写未知，不编造。
5. 后续源码快照使用从固定HEAD建立的独立 `/tmp` Git索引，避免旧真实索引产生虚假删除；不reset/checkout/clean，不修改真实索引或历史patch。

理由：[RUN] HPC HEAD916289b与旧索引不一致，`git diff --cached --shortstat HEAD`报告600文件/904198删除，而已同步源码实际存在。此前只对齐HEAD却未处理旧索引，是本轮管理快照失真的原因；原patch保留当时事实，不能改写成新的正确patch。此次只准备可恢复存储方案。

授权依据：AGENTS.md D、E1要求保护历史结果/运行记录；替换已有证据的存储形式涉及移除HPC未压缩副本，因此先取得明确确认。这是对证据保护规则的具体应用；文件未要求对任意压缩副本创建重复申请。

当前：压缩副本仅在 `/tmp/gosc-snapshot-archive-preview-20261116`；所有HPC原件仍在。新编译器未安装/执行，helper/合同/部署未通过。该提案不授权新编译器安装、模型加载、题目输入、服务改动或Git提交。
