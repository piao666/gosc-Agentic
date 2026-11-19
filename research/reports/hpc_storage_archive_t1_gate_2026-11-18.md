# HPC HDD 归档与 T1 恢复关卡

2026-11-18，Asia/Shanghai。状态为 **HDD 归档和读回已验证，SSD 清理待确认，T1 保持阻断**。

## 个人配额与现场状态

[RUN] 在 `n1` 上使用 Lustre 只读用户配额接口实测 UID 8301880。挂载点的 `df` 读数用于识别存储设备，个人可用额取该账号硬上限与已用字节的差。 [Lustre 配额接口文档](https://doc.lustre.org/lustre_manual.pdf)

| 卷 | 个人硬限 | 归档前可用 | 归档与还原演练后可用 |
| --- | ---: | ---: | ---: |
| SSD `/home/u202520081000097` | 100 GiB | 768 KiB | 768 KiB |
| HDD `/hdd/u202520081000097` | 500 GiB | 482.53 GiB | 482.30 GiB |

[RUN] 项目保持在 `/home/u202520081000097/jupyterlab/Paper/gosc`，Python 3.11.15，Git `d5f5522f99872d7453ef54cce06c9ae941846877`。225 条任务登记中 175 完成、50 失败，planned/running 为 0。Ollama 仍为 PID 37483，启动标识 4897373256，回环监听，无已建立连接、无直接子进程，GPU 0 MiB。218 字节恢复锁归属 `hpc-masbench-t1b-runner-recheck-20261118`，保持原状。 [盘点明细](../logs/masbench-t1-driver-2026-11-17/hpc_archive_inventory.json) · [归档前个人配额](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_before_archive.json) · [归档后个人配额](../logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota_after_archive.json)

## 复制、登记与还原验证

[RUN] 将两个 `completed` 且退出码为 0 的完整运行目录复制到 `/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1`。HDD 内延续原有 `research/sync/runs/` 与 `research/sync/receipts/` 结构，保留完整原始产物、登记状态、manifest、运行日志、源码快照。回执保存两份最早能覆盖对应清理候选的正本 `20261020T072033Z-ordered-94ad1a.json`、`20261022T025244Z-ordered-6f7572.json`，以及同时覆盖两次运行的最新已验证压缩回执 `20261118T080840Z-e03b60.json.gz`。

[RUN] 归档 **47 个文件、249,891,146 bytes（238.31 MiB）**。复制逐文件比对源与目的 SHA-256，登记产物额外与运行索引对照。独立执行 `sha256sum --strict --check SHA256SUMS`，47/47 通过。随后在 HDD 独立临时目录按原相对路径实际还原四个清理候选，共 196,585,815 bytes，逐件与 SSD 原件的大小、SHA-256 对齐。归档经过发布后复读。复制记录 1.944 秒，独立回读与还原演练记录 1.408 秒。

HDD 证据位于该目录下的 `archive_manifest.json`、`SHA256SUMS`、`readback_verification.json` 和 `ssd_cleanup_candidates.json`。 [复制与拟清理清单](../logs/masbench-t1-driver-2026-11-17/hpc_archive_copy.json) · [独立读回结果](../logs/masbench-t1-driver-2026-11-17/hpc_archive_readback.json)

## 等待确认的四个 SSD 原件

以下路径均以 `/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs/` 为前缀。

| 文件 | 大小（bytes） | SSD 实占（bytes） |
| --- | ---: | ---: |
| `resume-radio-noise-20261020/outputs/pool-001-jobs.jsonl` | 55,971,326 | 55,975,936 |
| `resume-radio-noise-20261020/outputs/legacy_results/noise.jsonl` | 55,899,295 | 55,902,208 |
| `resume-radio-overhead-20261020/outputs/pool-001-jobs.jsonl` | 47,187,332 | 47,194,112 |
| `resume-radio-overhead-20261020/outputs/legacy_results/overhead.jsonl` | 37,527,862 | 37,531,648 |
| **合计** | **196,585,815** | **196,603,904** |

[RUN] 目前全部 SSD 原件存在，实际释放为 **0 bytes**。四个文件均是普通文件、单硬链接。按当前实占预计可返还 **187.50 MiB**，以清理后 Lustre 个人配额复测为准。确认后应再次检查活动进程、SSD 文件身份和 HDD 副本 SHA，写入外部归档定位，再按四条精确路径清理并复测。两次运行在 SSD 的原登记和其他文件以及全量回执保留。

## T1、T2 与 B1

[RUN] 本轮是存储与文件管理，新增生成请求、真实题目曝光和科研运行均为 0。T1 仍保留上轮的现场失败与恢复锁。释放后先验证持久写入，再分别查渲染 499 与锁处置。真实合成复验的预算另行确认，T1 及独立审查通过后再进入 T2。真实四题 B1 仍由前置关卡和单独授权控制。整项目迁移待实际释放量与持续写入复查后才需要评估。 [T1 审计](masbench_t1_runner_recheck_2026-11-18.md)
