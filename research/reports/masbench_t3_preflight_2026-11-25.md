# MASBench T3 准入进度

2026-11-25，Asia/Shanghai，Git 基线 `b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0`。T3 针对四个冻结开发问题验证任务能力和可追踪的配对通信差异。D1 与原注册表保持，base 为主诊断。 [T3 彩排规格](../protocols/masbench_t3_rehearsal_2026-11-25.md) · [预算提案](../protocols/masbench_t3_budget_proposal_2026-11-25.md)

## 禁网矩阵与阻断

[RUN] HPC `n1`、2 CPU，以 `timeout --kill-after=2s 88s {python} experiments_ext/masbench_t3_rehearsal.py` 登记 `hpc-masbench-t3-rehearsal-20261125`，1.182084 秒、exit 0。以 T2 的词表和实际冻结请求哈希，使用 505-token 虚构回答、实际 `ControlledClient`、应用和 wire transport 路径，跑通 16 组各 6 个总轮次，共 96 个假生成。条件顺序按题号与提示族交替，八对初始请求和私有视图一致，所有 Full 后续接收请求有消息可见性证据，No-A2A 对应未交付。另用虚构 gold 验证失败进入主分母、未启动单列。真实 HTTP、推理、模型口径的真实题目曝光均为 0。

| 彩排数据 | 最大序列化字节数 |
| --- | ---: |
| 单条生成请求 | 37,791 |
| 单条应用回复 | 42,115 |
| 应用结尾结果含原始 wire 事件 | 1,039,754 |
| 单 episode 应用进程传给 broker | 1,195,616 |

[RUN] 实测八个 Full episode 的原结尾结果超过 64 KiB 单包上限，累计也超过 512 KiB。8 个 No-A2A 的结果均低于两个原上限。Full 共 18,432 个合成传输帧、40 项消息实际进入接收方随后请求的证据。No-A2A 两者均为 0。全部 16 个结尾包共 8,390,864 bytes，单独序列化的客户端审计共 1,949,524 bytes。这两个部分的大小未包含真实 API 和 helper 产物，不能用于承诺完整现场盘成本。 [彩排明细](../artifacts/masbench-t2-t3-20261125/t3-rehearsal.json)

[CODE] 为大结尾结果增加限长的长度／SHA-256 帧。普通请求沿用 64 KiB 单条及 512 KiB 累计控制上限。结尾结果另用最多 8 MiB、有原持久存储上限的载荷，经核验后再落盘。结果载荷不可充当新请求。 [Driver](../../extensions/masbench_reasoning/live_driver.py) · [回归](../../tests_ext/test_masbench_t1_live_driver.py)

[RUN] `hpc-masbench-t3-ipc-contract-20261125` 登记 7.899729 秒、exit 0，实际 **55 项禁网测试通过**。新增用例核验超过旧累计上限的 wire 证据能通过真实应用管道并持久化，以及内容被改时 SHA 校验拒收。两个运行目录已逐文件核验回传 551 份，共 12,834,238 bytes。 [禁网日志](../sync/runs/hpc-masbench-t3-ipc-contract-20261125/stderr.log) · [回传凭证](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

[RUN] `hpc-masbench-t3-storage-contract-20261125` 在 HPC 新建个人 HDD 隔离目录，禁网实做 8 MiB 控制日志预分配。完整写入 98 渲染／312 GET／108 清理 GET／18 卸载的虚构额度扣记及绑定，共 2,681 条哈希链事件。每一类额外一次均被拒绝，实际文件已读回检 SHA，重开后各额度和末尾哈希一致。实验登记的存储凭证写在 SSD，原始控制文件保留在 HDD。耗时 3.640730 秒、exit 0，之后 9 个登记文件核验并回传。 [存储合同](../artifacts/masbench-t2-t3-20261125/t3-storage-contract.json) · [定向回执](../artifacts/masbench-t2-t3-20261125/receipt_index.json)

## 真实执行预算和关卡

[RUN] T2 的 9973 输入／2 输出 tokens 用时 85.21 秒。HPC 在 T3 开始时空闲、恢复锁为空、配置 1024。个人 SSD 尚有 71,368,704 bytes，HDD 尚有 517,861,466,112 bytes。现行的盘容量与 6000 秒旧提案均需要重算。

[HYPOTHESIS] 候选真实配置用 16384，每次准备≤150 秒、生成≤180 秒、清理≤40 秒，98 个可能派发合计最多 34,800 秒现场预算。512 输出预留不变，拟合计上限 1,555,456 输入／50,176 输出 tokens。拟 SSD/HDD 增量分别≤32 MiB／1 GiB。HDD 用于完整链和证据，SSD 用于登记索引以及故障停发控制。以上均为拟议上限，实测的任务时延、512-token 输出充分性及实际磁盘开销继续等待现场。

**T3 准入组件通过，真实执行仍等待。** 进入真实执行还需将专用任务授权、任务与合成预算分账及 HDD 原始产物登记接入同一个试验 Driver，并单独确认本轮长期 GPU 占用额度。真实 B1 尚未启动，四题生成与模型曝光均为零。 [候选矩阵与硬上限](../protocols/masbench_t3_candidate_plan_2026-11-25.json)
