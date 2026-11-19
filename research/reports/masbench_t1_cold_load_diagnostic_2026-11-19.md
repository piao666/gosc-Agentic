# MASBench T1 单次冷渲染诊断

2026-11-19，Asia/Shanghai。用户批准执行 [单次诊断预算](../protocols/masbench_t1_cold_load_diagnostic_budget_2026-11-19.md)。**唯一一次渲染完成，HTTP 200，服务清理证据齐全。** 本轮为零生成冷加载诊断，T1 四例验收仍待单独安排。

## 授权、实现和首次失败

[CODE] 实施位于 `experiments_ext/masbench_t1_cold_load.py`、禁网夹具 `masbench_t1_cold_load_fixture.py` 和独立审计 `masbench_t1_cold_load_audit.py`。诊断入口绑定批准、注册 ID、源代码、预算和输入计划 SHA，端点仅允许固定的本机状态 GET、冻结 `_debug_render_only` 和卸载。沿用 Ollama 0.11.11、同一个 `qwen2.5:7b`、同一模板及 1024 窗口。GPU 和 CPU 数值只作本轮工程证据。正式 T1 Driver 的 60 秒配置未改。

[RUN] 首次登记在旧标记复核时触发 Python 局部变量遮蔽，worker 未产生发送事件或模型调用，保留一次已扣旧状态 GET。旧标记 SHA 未变。原失败与只读审计保留。修正后在禁网夹具中实测模拟 HTTP worker 能输出发送和响应事件。HPC 最终 6 项禁网测试通过，测试用时 0.065 秒。定向复核前次失败账本、5 条发送哈希和 11 项产物；两次现场复核 GET 加上首次扣记，共占用旧标记 GET 额度 3，未退款。原 216 字节标记连同逐字节内容保存于 HDD 归档下的 `t1_cold_diagnostic_old_marker_20261119.json` 后才解除。

## 唯一一次真实渲染的时间线

[RUN] `n1`、Git 基准 `d5f5522f99872d7453ef54cce06c9ae941846877`，最终执行同步 `20261119T051349Z`，1208 个文件、0 SHA 差异。发出前空驻留、无服务子进程、GPU 0 MiB。模型权重固定，页缓存冷热未知。以下均相对唯一渲染发送，采样事件约为秒级精度。

| 阶段 | 时间或观测 |
| --- | --- |
| 服务日志记录 runner 启动命令和 Go runner 初始化 | 约 0.73、0.75 秒 |
| 首次记录 runner PID 50055／启动标识 4915346992 | 0.906 秒 |
| 最早权重张量日志所在区间 | 约 3.98–10.00 秒，相关行自身没有可对齐的精确时间戳 |
| 首次观测到固定模型文件进入该 runner maps | 5.158 秒 |
| runner 就绪 | 约 10.00 秒 |
| 渲染成功返回 | 服务端 HTTP 200，10.009569 秒；Driver 从发送到记录结果 10.050872 秒 |
| 清理 | 卸载响应确认，再核对驻留列表空、本轮 PID 与启动标识退出、GPU 0 MiB，诊断恢复标记长度变为 0。Driver 清理耗时约 1.14 秒。 |

[RUN] 13 次资源样本，包含同一 runner 的 10 次 I/O 样本。首次至最后一次该 runner 的 `read_bytes` 增量为 1,613,197,312 bytes（约 1.50 GiB），`rchar` 增量 6,056,419 bytes，主缺页计数未增加。服务和 GPU 显存采样峰值分别为 4.93 GiB、4.84 GiB。进程计数跨越采样区间内的模型与其他读取，无法直接确认物理 SSD 带宽。文件映射、读计数和张量装载可重叠；原证据不足以把 10.05 秒精确拆成 SSD 与 GPU 耗时。 [独立审计和原始日志定位](../sync/runs/hpc-masbench-t1-cold-load-audit-v2-20261119/outputs/audit.json)

## 登记、回传和关卡

[RUN] 最终现场登记 `hpc-masbench-t1-cold-load-v2-20261119`，exit 0、12.351913 秒。完整收尾动作含 2 个旧复核 GET、1 个常规 GET、3 个清理 GET、1 个渲染 POST、1 个卸载 POST。生成请求、生成 token 预留及真实题目均为 **0**。独立审计登记 `hpc-masbench-t1-cold-load-audit-v2-20261119`，exit 0、0.199451 秒，校验 13 项登记产物、请求哈希、进程观测和退场证明。

实际运行由 `scripts/hpc_runs.py run --gzip-source-patch` 登记。续轮入口分别为 `timeout --kill-after=2s 78s <python> experiments_ext/masbench_t1_cold_load_fixture.py`、`timeout --kill-after=2s 207s <python> experiments_ext/masbench_t1_cold_load.py`，以及 `timeout --kill-after=2s 88s prlimit --as=2147483648 -- <python> experiments_ext/masbench_t1_cold_load_audit.py`。两轮六个登记合计运行约 14.00 秒。定向回传 67 项，逐文件 SHA 验证 14,129,416 bytes，本地与 HPC 同一回执。 [回传回执](../sync/receipts/20261119T051630Z-t1-cold-load-scoped.json) · [首次失败](../sync/runs/hpc-masbench-t1-cold-load-20261119/outputs/summary.json) · [现场摘要](../sync/runs/hpc-masbench-t1-cold-load-v2-20261119/outputs/summary.json)

**冷加载诊断通过，T1 整体验收仍待执行。** 一次成功说明当前服务能完成冷渲染，结合先前 30 秒及 60 秒取消，冷加载耗时有明显变动，且较慢用例具体归因仍未完成。下一份 T1 预算可将冷启动与生成故障 watchdog 分开计时并完整入账，仍需单独审批。原生断连后的即时空闲以及真实四题任务效果仍未验证。
