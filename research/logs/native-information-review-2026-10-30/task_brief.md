# Research Task Brief — Native-Information Task Value 静态审查

- 授权：用户指定仅完成G0/G1静态技术规格和资深审稿式可行性审查，完成交付后停止；无算法实现、测试/任务实验、扩样本、训练、付费API、Git提交或推送授权。
- 基线：014b85dfc472c45d8ea5f15e83e0c1ed8e938daf；本轮git核验一致。初始dirty仅为上轮research/README.md、2026-10-29报告与日志；已确认是会话既有产物并原样保留，本轮另建文件。
- 科学问题：只改变EVID价值，G1能否在合法native信息及固定候选/服务/selector下区别于G0、ToM和价格机制？本地Lc/待发记录的更新顺序是否允许构造不重复计数的belief变化？
- 前人成果：GP-ID科学No-Go、7辅助对照预算违规、BF支持域工程验收与上轮决策；均保留，不能当成本轮新检验。
- 拟验证假设：源码静态追踪可界定本地输入；空间权重可能只产生尺度变化或被最长FIFO前缀限制；shadow诊断只能检验选择区别和成本，不能证明任务收益。
- 文件：新增research/protocols/native_information_value_spec_v1.md、research/reports/native_information_feasibility_review_2026-10-30.md，以及本目录brief/完整阅读索引/证据映射/manifest/任务日志/管理校验。不修改原报告、源码、冻结协议或原始实验数据。
- 方法：完整分段阅读用户指定文档/源码；追踪SensorModel.apply、phase_decide、on_step、接收/ACK/队列清除及估值调用顺序；推导定义、归一化、复杂度、反例、诊断准入/停止条件。只做文档/轻量文件管理核验。
- 成本：0新增科研计算、0新mission/独立N、0训练/付费API；不连接HPC，不同步，不运行pytest/数值例子/统计。实际估值耗时标为未测。
- 反例与停止：Lc已包含消息或记录身份不清时阻断该快照，不扣除公共证据伪造反事实；G1仅共同缩放/不改变可行选择则No-Go；当前数据不足时明确Pending，不添加模型掩盖。
- 验收：精确G0/G1、字段来源与不重复记账边界、仅EVID替换接口、强对照/共同校准、未来有界shadow设计、Go/No-Go与审稿缺口；本轮无执行放行，报告完成即停止。
