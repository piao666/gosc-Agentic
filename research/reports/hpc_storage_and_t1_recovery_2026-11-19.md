# HPC SSD 恢复与 MASBench T1 复验

2026-11-19，Asia/Shanghai。接续 [HDD 归档与四路径确认清单](hpc_storage_archive_t1_gate_2026-11-18.md)。项目仍在 `/home/u202520081000097/jupyterlab/Paper/gosc`，HPC 为 `n1`，基准为 `d5f5522f99872d7453ef54cce06c9ae941846877`。

## SSD 清理和持久写入

[RUN] 用户确认四个指定 SSD 原件。清理前再次按已归档 SHA-256、路径、设备、inode、修改时间、单硬链接和登记索引校验。核对无登记活动任务，已读到的同账号进程文件描述符无命中，四个同 UID 进程的文件描述符表不可读。首次在删除前写 SSD 定位遇到 EDQUOT，当次零删除。随后先在 HDD 持久保存定位和操作日志，清理四件并写回两个历史运行目录的 `ssd_archive_location.json`。HDD 全量归档、SSD 原运行登记及其余文件保留。

[RUN] 删除前账号 SSD 个人配额剩 786,432 bytes（768 KiB），清理和定位写回后剩 197,382,144 bytes（188.24 MiB），实际增加 **196,595,712 bytes（187.49 MiB）**。留下同一探针累计三次 16 MiB 写入，每次 fsync 并按完整保留内容回读校验，累计 48 MiB，历时 10.324 秒。探针移除后即时配额数仍暂含探针，延迟复查恢复到 188.24 MiB。本阶段在原路径恢复写入。 [清理执行记录](../logs/masbench-t1-driver-2026-11-17/hpc_archive_cleanup_confirmed_20261119_v2.json) · [持续写入](../logs/masbench-t1-driver-2026-11-17/hpc_ssd_sustained_write_20261119.json) · [延迟配额复测](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_after_settling_20261119.json)

## 前次 HTTP 499 与恢复锁

[RUN] 2026-11-18 15:43:49 服务开始加载 runner，15:44:18 Ollama 调度日志记 `Load failed`、`context canceled`，`POST /api/chat` 用时 **30.07366354 秒**并记 499。最早成功的对照渲染用时 10.414385467 秒。失败运行的两条发送分别为初始 `GET /api/ps` 和渲染检查 POST，生成数为 0。 [带原始偏移与 SHA 的日志核查](../logs/masbench-t1-driver-2026-11-17/t1_restore_499_log_review_20261119.json)

[CODE] Ollama 0.11.11 的 `server/routes.go` 先调用 `scheduleRunner` 再处理 `DebugRenderOnly`，其 `handleScheduleError` 按 `context.Canceled` 返回 499。`server/sched.go` 把 HTTP 请求 context 传给 `Load`。旧 Driver 的 RPC worker 独立设 30 秒 socket 超时；父进程操作上限是 60 秒。证据表明 499 发生于冷加载期间的连接取消，和固定 30 秒 socket 上限吻合；加载较慢的底层原因及旧 worker 自身退出日志仍未知。现已改为传递父进程单调时钟截止时间，worker 上限 60 秒，派发前截止即拒绝；生成 watchdog 继续用发送后 0.25 秒。

[RUN] 第一次解锁核查发现旧控制日志两份原件不一致，按规则停在变更之前。上次本地回传的 22 条控制日志匹配登记 SHA，HPC SSD 当前 21 条是逐字节相同前缀，后者少的唯一一条为清理 GET 扣记，无发送。预算链 7 条匹配登记；两个控制版本和差异说明已复制到 HDD，原件在各自位置保留。再次独立校验链、原登记产物和运行身份后，在独占锁内完成三个只读 GET，两次 `/api/ps` 为空、服务 PID 一致、无子进程或已建立连接、GPU 0 MiB。218 字节旧标记与 SHA 先归档，再以行政恢复处置将标记长度变为 0。历史失败及未核验的旧 runner 退出保持原判断。 [两版日志核对](../logs/masbench-t1-driver-2026-11-17/t1_control_version_preservation_20261119.json) · [锁处置回执](../logs/masbench-t1-driver-2026-11-17/t1_metadata_only_lease_recovery_20261119_v2.json)

## 禁网回归与复验范围

[RUN] HPC 运行 `hpc-masbench-t1-post-storage-contract-20261119`，49 项合成替身测试全部通过，测试 6.922 秒、登记 7.459467 秒。两项新边界证明冷渲染可使用剩余 45 秒，截止已过则不会建立 HTTP 连接。未运行模型或重做 helper 合同。实际测试命令为 `timeout --kill-after=5s 85s <project-python> experiments_ext/masbench_t1a_contract.py`，由 `scripts/hpc_runs.py run` 登记。

[RUN] 用户单独批准同一个项目 Ollama 的固定合成复验。启动前复查默认窗口 1024、服务及 helper SHA、GPU 空闲、零并行登记、恢复锁长度为 0。计划与独立审计命令见 [已批准复验预算](../protocols/masbench_t1b_post_storage_budget_2026-11-19.md)。

## 本轮真实复验与独立审计

[RUN] `hpc-masbench-t1b-post-storage-20261119` 在完整同步 `20261119T025543Z`（1186 文件、0 SHA 差异）后登记。运行 62.013628 秒、exit 1。超窗负控制在零 HTTP 下通过。首例的已发请求为渲染检查，Driver 在发送后 **59.287267 秒**触发 60 秒单操作截止，同一 HTTP worker 实际记有 SIGTERM 和 SIGKILL。服务端在约 **59.659876 秒**返回 499，记录在加载期间断连及取消。加载日志已进入 `load_tensors`，未见 runner 就绪。这一记录尚不能归因到磁盘读、GPU 或其他基础设施环节。

[RUN] 运行完成了卸载请求和前后空驻留核对，缺失绑定过的 runner 身份，因此卸载退出证据标记为未验证。保留新标记（216 字节），未写入恢复派发许可。生成、预算预留、真实题目曝光均为 **0**；四例实际生成都未执行。既有旧标记已行政解除与本次的新标记是两个独立事件。资源采样 121 次，记录峰值 Driver RSS 89,382,912 bytes、服务树 RSS 2,111,815,680 bytes、GPU 444,596,224 bytes。 [运行摘要](../sync/runs/hpc-masbench-t1b-post-storage-20261119/outputs/summary.json)

[RUN] `hpc-masbench-t1b-post-storage-failure-audit-20261119` 在 0.197253 秒完成，exit 0。验证 11 项登记产物、冻结渲染请求与实际发送的 SHA、预算和控制链、操作截止、真实信号与清理状态。审计通过的是失败证据核查，结论仍为 `acceptance_passed=false`。全流程成功审计没有启动。两次 499 的核心原始行按原 SHA 保存至 HDD。 [独立失败审计](../sync/runs/hpc-masbench-t1b-post-storage-failure-audit-20261119/outputs/audit.json) · [原始服务日志归档](../logs/masbench-t1-driver-2026-11-17/t1_debug_stage_review_20261119.json)

[RUN] 三个本轮登记目录的 505 个文件、12,855,199 bytes 已逐文件验证并回传。采用定向回传以保持先前已核验的控制日志副本，HPC 和本地都有同一份回执。审计完成后 SSD 个人配额实测仍剩约 173.29 MiB。 [回执](../sync/receipts/20261119T034327Z-t1-post-storage-scoped.json) · [配额复测](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_after_t1_20261119.json)

## 阶段判定

**T1 No-Go。** SSD 持久写入已恢复，项目继续留在原路径。当前关卡阻断在真实冷加载就绪，原生断连后即时空闲仍未证明。下一步应把冷加载作为单独诊断，区分模型文件读取、runner 初始化和权重装载，保留新恢复标记直到按本轮证据处理。涉及加载模型的诊断与下一次真实合成复验均需分别核准具体预算。T2 和真实四题 B1 尚未启动。
