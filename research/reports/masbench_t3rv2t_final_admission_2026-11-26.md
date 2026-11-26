# Research Task Report — T3-R-v2-T Final Admission

2026-11-26，Asia/Shanghai。**现场预检通过。唯一真实 run 待批准。** 本轮生成请求为 0，服务 HTTP 请求为 0。已完成针对性合同、独立审计与回传入口、历史私有视图恢复和现场预检，冻结了运行身份及预算。[一次性执行申请](../protocols/masbench_t3rv2t_final_execution_request_2026-11-26.md)

## 工作与证据

[CODE] `fair_final_v2_task.py` 的 `evidence_links` 检验送达载荷、来源、接收者完整的下一请求和终答请求。`scientific_gate` 按四个不同家族计算正差集合，并且只接受该集合中 Full episode 的同一消息证据链。需要独立语义记录和可追溯的终答引用。工程基础设施门、样本范围、阈值仍按原计划。

[CODE] `masbench_t3rv2t_admission.py` 从历史审计索引定位原四个 `protocol/No-A2A` episode 的双方首个本地请求。只读八个 SHA 已绑定的原件，抽取问题、角色、对方名字和本地信息，再按家族复核四个原私有视图 SHA。原数据集和封存 52 条未打开。私有 bundle 及 token ID、render 原文保留在 HPC HDD。公开预检回执只有范围、计量、哈希和现场身份。

[RUN] 新合同 `hpc-t3rv2i-task-final-contract-20261126` 通过 8 项，登记 1.096769 秒。覆盖相同证据链、借用非正差家族的 L2、错误终答请求 SHA、消息未进入下一请求、重复配对和超期，以及原件/账本篡改和回传损坏。只运行这一组。已有 25 项合同的报告与 SHA 在新回执中链接。

[RUN] 现场 `hpc-t3rv2i-task-admission-20261126` 登记 7.692747 秒，八个初始本地输入计数通过。资格不含 Full 接收真实交换消息后的动态输入，生成前必须逐 slot 重新计数。

| 历史计划家族 | Alice tokens / 字节 | Bob tokens / 字节 |
|---|---:|---:|
| f1 | 3202 / 17313 | 3085 / 17006 |
| f2 | 2744 / 13383 | 2088 / 10187 |
| f3 | 2731 / 13783 | 2000 / 9877 |
| f4 | 2313 / 10766 | 2698 / 12843 |

[RUN] HPC n1，CPU 配额 2 核、内存 24 GiB。SSD 用户余量 76804096 字节，HDD 余量 517703073792 字节。1024 基线 PID 42070，启动戳 4975206358，自己的 loopback listener 空闲、无 runner、GPU 0 MiB。读取并核对权重、模板、模型 manifest、二进制和 helper SHA。未来若现场已漂移，停止后重新审阅绑定。

[CODE] `masbench_t3rv2t_live_audit.py` 独立复核实际运行登记、源码快照、HDD 文件集合、账本链、逐 slot 的输入/渲染/使用量、监测与 1024 回滚。`masbench_t3rv2t_closeout.py` 把真实注册执行、独立审计、HDD 与登记证据传回、SHA 校验回执接到一次启动。这个终态审计入口尚无本轮真实任务的运行产物。`collect-only` 用于恢复传输，不重新启动模型。

[RUN] 两个无生成登记的回执共 19 文件、1914048 字节，逐件 SHA 校验通过。新版 SSH 流式传输和本地 SHA 恢复以同批 19 文件独立演练，耗时约 1.20 秒。600 秒满量回传和真实终态双端确认尚未实测。[证据索引](../logs/masbench-t3rv2t-final-admission-2026-11-26/evidence_index.json)

## 管理记录与决定

HPC Git 本来仍在 `c0621a1`，此次备份 HEAD 和索引，仅快进元数据至 `4a7ab22`。对齐的命令末尾因 PowerShell 行尾导致只读 `git diff` 返回 usage，之后另次核验确认 HEAD 正确、暂存区无差异。按现有工具同步后的 `20261126T092125Z` 无 SHA 不一致，两个预检使用同一快照，manifest SHA `7e4d0514e771336a4c4b56ca2e4e32b6f3eee5d0458c18c7830f6ae8bc9cc730`。历史运行各自保有原身份。

实际运行命令为 `python scripts/sync_hpc.py`（排除既有三项未跟踪资料），随后在 HPC 使用 `.venv/bin/python -m experiments_ext.masbench_t3rv2i_register run` 分别登记 `masbench_t3rv2t_final_contract` 和 `masbench_t3rv2t_admission`。本地用上一阶段的 `collect_evidence.py` 回传这两个登记，再用新版 `stream_archive` 与 `restore_archive` 演练。没有新增 Git 提交或推送。

只申请一次，最多 48 个真实任务请求。批准对象和资源上界见执行申请。阶段决策仍以独立审计、回传和同一家族的 L1/L2 证据为准。
