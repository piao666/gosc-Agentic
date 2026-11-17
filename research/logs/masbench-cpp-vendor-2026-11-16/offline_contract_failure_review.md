# 离线首轮格式绑定失败与复核边界

[RUN] `hpc-masbench-context-offline-contract-20261116` 0.190880s、exit1，在manifest默认system层元数据检查处拒绝；没有启动helper，没有读取权重/GPU/HTTP。失败原样保留。

[CODE] 原检查将manifest `digest` 当作blob文件名，使用 `sha256-<hex>`；manifest实际规范是 `sha256:<hex>`。固定原始manifest的SHA、system摘要值、size68和实际blob SHA全部不变；仅修正manifest前缀，blob文件路径仍保持 `sha256-`。这不是换模型、放宽身份或跳过保护。

按已批准离线合同范围做一次有界复核；两次已登记计算时间合计仍≤120s，首轮消耗0.190880s，剩余119.809120s。候选入口helper执行检查105s后终止，预留清理；新run不重建helper、不重新分配1200s构建预算。两次开始/结束均分别保存，计算墙钟合计不冒称跨人工诊断间隔的单一120s自然时间窗。若剩余预算不足、helper/内容合同真实失败，停止，不自动换源、改服务或扩大合同。

[RUN] v2为0.778828s、exit1，helper实际词表加载日志显示 `vocab only - skipping tensors`；在fixture实际客户端边界检查失败。前两次计算合计0.969708s，剩余119.030292s。

[CODE] 受控客户端 `client.py::ControlledClient.generate` 明确只接受首条system，后续role仅user/assistant；renderer测试用例9（两条system）和13（后置system）超出客户端schema，但属于所检模板的可渲染域。最初fixture误将这些用例当作应该派发的窗口边界，因此失败。保留全部14个render用例与42个组合；合法12用例×3为36个真实窗口检查，另2用例×3为6个 `request_schema` 派发前拒绝检查。客户端和helper未改，不把6个schema检查冒充窗口通过，不把fixture请求当HTTP/模型生成。此为fixture期望修正，最后一次有界复核仍扣除前两次成本；不重置编译预算。
