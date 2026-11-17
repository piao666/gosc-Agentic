# MASBench真实部署验收：具体方案

2026-11-16。本轮用户要求推进数据、计数与部署三项，并已批准隔离离线构建；**本方案中的服务配置/模型加载/合成生成尚未据此执行**。四题真实任务、正式评价、训练仍排除在本轮之外。

## 已重新核实的事实

[RUN] 当前HPC n1、UID8301880、2CPU/24GiB；Ollama0.11.11 PID8964，单并发/单模型、回环11434、默认context1024；只读`/api/ps`返回空列表，可见L40总34304MiB、查询时使用0MiB。这些都不证明32768生效、推理能力或未来GPU峰值。

[CODE] 固定source92b96d54efd6b49322b7cf046f9a0dc16b00cd0a中：

- `server/routes.go::ChatHandler`在`chatPrompt`之后支持`debug_render_only`，可返回**服务实际渲染文本**，但调用前会scheduleRunner，因而可能加载模型。
- `server/prompt.go::chatPrompt`可能裁剪历史。必须把服务返回文本与离线**完整输入**渲染逐字节比较，不能把debug成功本身当未裁剪证明。
- `runner/llamarunner/runner.go:721`的health只返回status/progress，不暴露活动sequence数；`/api/ps`也只表示驻留模型，均不单独证明idle。
- runner在请求context关闭时关闭`seq.quit`，处理循环检查退出并移除sequence。这是源码证据，不能替代当前部署上的实际取消验收。
- 空messages、keep_alive=0的`/api/chat`走卸载分支。若采用取消后卸载栅栏，应明确核验卸载返回、`/api/ps`空及此前runner PID消失；这证明清理后停止，不自动证明“原生断连立即取消”已被独立观测。

## 通过条件与执行顺序

1. **离线先决条件**：helper构建成功；官方toolchain SHA、固定源码/模块校验、实际Ollama build info、manifest/template/模型身份及合成合同通过。`binding.verified`继续false，不能从fixture复制。
2. **上下文配置方案**：离线评估完整请求所需空间后，再决定是否批准1024→32768。若扩大，全局变更前核无活动任务/其他客户端，备份精确服务配置与PID身份；仅更新本项目服务，保留回滚1024方法，不更新驱动或模型。单模型、单并发、CPU2保持。`/v1`的max_tokens不设置num_ctx，不能只改ClientConfig冒充服务配置已变。
3. **渲染与部署等价**：合成普通输入及多轮/多角色输入，通过native debug接口取得完整render；比对离线render字节/哈希；核实际runner加载日志/参数和有效context。生产二进制build info、helper源码与构建身份单列；若没有部署token IDs接口，只能如实记录相同源码/flags与有限render/usage对照，不能声称任意输入逐token独立等价已证明。
4. **正常合成调用**：同一完整messages经`/v1/chat/completions`，无真实题目，要求简短自然终止；helper派发前计数与服务usage对账，拒绝length截断、缺失或不一致usage。temperature0不是确定性保证。
5. **取消与清理合成调用**：暖模型后单个受控请求故意中断，持久记录预算与inflight；核静态取消链和实际停止迹象。若无法可靠观测直接idle，则执行已纳入预算的卸载栅栏，确认旧runner退出后才结束清理；未知/失败时fence，禁止下一生成，不向Ollama服务PID发送kill。是否接受“取消后卸载栅栏”作为未来live Driver停止策略，应与原生直接取消结论分开。
6. **结论**：仅在上述有限输入/客户端/engine/窗口范围内建立证据绑定；若接口或观测不足，保持Pending/Blocked，不声称完整部署验收通过。当前fixture sandbox不能直接接真实HTTP/词表helper，真实Driver仍需独立接线合同。

## 拟申请的合成预检范围

以下为可审阅提案，**不是新授权或已执行**：

| 项目 | 拟定上限 |
|---|---|
| 总墙钟 | 480s，内部派发截止420s，留60s清理；单操作≤60s |
| 模型 | 已有固定manifest的qwen2.5:7b；模型下载0，单并发1 |
| HTTP POST | ≤6：2次debug render、2次合成生成、最多2次卸载清理；不同类型分别计数，不自动借用 |
| HTTP GET | ≤40，仅版本/模型身份/状态；不以轮询次数扩大生成额度 |
| 生成tokens | 正常请求≤16、取消请求≤512，全部失败和中断也预留不退款；无真实题目 |
| 资源 | CPU≤2；进程树RAM与归属GPU显存拟限16GiB，采样阈值超过即停止派发并执行清理；这不是内核瞬时硬隔离保证，未实测峰值 |
| 数据/产物 | synthetic only，≤16MiB，日志只读白名单信息，不打印其他进程环境或真实历史prompt |
| 结果 | render/usage/context、取消及卸载清理各自判定；失败保留，无第二模型/自动加长上下文/重复生成挽救 |

该提案不消费原四题98次生成预算；未来若把预检证据复用于B1，须在统一版本化预算里明确哪些已发生、哪些预留，不能重复计成免费检查。当前离线构建尚未通过，不能先加载模型绕过计数关卡。
