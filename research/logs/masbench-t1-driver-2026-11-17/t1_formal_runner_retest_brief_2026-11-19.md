# Research Task Brief · T1 runner 更替复验

[RUN] 首轮现场四次合成派发中，两次故障恢复通过，最后一条生成后的卸载遇到未绑定的 runner。原始日志、账本与标记继续作为独立记录。 [首轮验收](../../reports/masbench_t1b_formal_acceptance_2026-11-19.md)

[HYPOTHESIS] 对同一固定模型，渲染显式设置 `num_thread=2`、而兼容生成使用服务默认选项，可能导致 Ollama 调度器更换 runner。对齐两条路径的默认选项后，正常及恢复生成应在响应后取得与派发前一致的 PID 和启动时间。调度器也可能因进程健康检查等原因触发重载，因此复验仍需独立核实进程身份和全链路清理。

[CODE] 本轮修改 `extensions/masbench_reasoning/live_driver.py`、T1-B 登记入口、独立审计和必要的回归用例。保留已建立的 exact count、`ContextBinding`、`ControlledClient`、持久预留和两条故障注入路径。对观察到的未绑定 runner 收集独立退出记录，仍保持派发栅栏。健康响应后的进程观察和终末卸载需形成可审计的身份链。

[HYPOTHESIS] 计划使用相同四条合成输入和超窗负控制，HPC 2 CPU，禁网回归 90 秒。同一现场上限为四次生成、4096 输入／1088 输出 tokens、1020 秒、SSD 56 MiB；独立审计 90 秒。既有 helper 仅查 SHA。现场授权和旧标记归档处置以本轮预算为准。

验收需要分别证明三次卸载的原进程退出、两次故障恢复后的实际派发、两笔未知使用量维持保守预留，以及正常与恢复两条响应与实际绑定 runner 一致。任一条件缺失即保留证据并记录阻断。T2 和真实四题仍受各自前置关卡与授权约束。
