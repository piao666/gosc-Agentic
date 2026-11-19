# Research Task Brief — T1-B

2026-11-18 Asia/Shanghai。用户明确批准按提案执行 T1-B，只使用固定的虚构输入与已安装模型。验收结束后再审查 T1 整体。模型、服务和产物预算沿用原提案。服务独占事实仍需确认。客户端主动断连和原生即时 idle 沿用不同的证据要求。

已实现冻结计划 `research/protocols/masbench_t1b_synthetic_execution_plan.json`、接线入口 `experiments_ext/masbench_t1b_live.py` 与独立审计入口 `experiments_ext/masbench_t1b_evidence_audit.py`。启动文件绑定批准原文、服务 PID/starttime、版本、模型与模板 SHA、协议和冻结输入、源码和单次登记 ID。故障点只影响本轮自有进程。审批文件以新建模式写入。完成测试、合成部署、审计、回传和结束状态分别记录。

[RUN] 同一只读预检第一次遭遇自动审批服务 403，未执行。重试成功，n1/UID 8301880，现服务 PID 37483，1024、单并发、唯一同 UID loopback 监听，已建立连接 0、其他活动登记 0，GPU 0 MiB，未发现持久恢复标记。helper SHA 与 T1-A 一致。空闲观测无法代替现场独占确认。当前尚无真实请求。代码和预检源同步 `20261118T044714Z`，1091 文件，SHA 不匹配 0。

[RUN] T1-B 接线变更后，HPC 登记 `hpc-masbench-t1b-wiring-regression-20261118`，继承内核网络禁用。既有 40 项受控接线回归用于检验本轮新增超时与恢复代码，登记耗时 5.589345 秒、exit 0。旧 tokenizer 合同没有重跑。实际模型/卸载/GPU均未调用。

[RUN] unittest 5.243s，fixture 产物 4,864,157 bytes。先执行 408 份文件的批量 SHA 核验，再以标准 pull 建立双方回执 `20261118T050052Z-06c2ae`，全量已登记产物完成镜像。

现场命令（HPC 已核 SHA 后，待独占确认才能启用）：

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --run-id hpc-masbench-t1b-live-20261118 --kind test --stage T1-B --purpose authorized-frozen-synthetic-driver-acceptance --model qwen2.5:7b --config research/protocols/masbench_t1b_synthetic_execution_plan.json -- {python} experiments_ext/masbench_t1b_live.py
```

若某例在故障前正常结束、观察到服务占用/身份漂移、运行资源超限或清理未证实，停止继续派发，保留已用预约与未知值。正常两例需 usage 和同源计数一致，故障两例需有真实发送和自有进程信号、卸载成功、旧 runner 消失与预算未退款证据。

## 现场结果

[RUN] 用户确认执行后，前两次登记均在生成前触发磁盘配额错误。第三次登记采用可选 gzip 源码快照，在 HPC 实际发出两条合成生成。正常请求通过，watchdog 触发、服务端 499、账本保留 48 输入／512 输出预留，实际用量为 `null`。显式卸载已返回，旧 runner 身份观察缺失。外层停止，未派发控制器中断与恢复请求。独立审计复核证据并确认验收未通过。结论、时间线、命令和回传回执见 [T1-B 验收报告](../../reports/masbench_t1b_live_driver_acceptance_2026-11-18.md)。
