# Research Task Brief — 摘要增量信息与同步成本，2026-10-22

用户授权执行下一步核查。本轮不训练、不运行新方法效果实验、不修写原校准/cache/历史数据来制造复现通过。

科学问题：候选receiver摘要是否包含现有INTENT/EVID之外的信息？真正供GOSC估值器使用，需在哪些端点获取/分发/等待？32bit旧草案是否漏计应用头、CRC、时间、ACK、控制/广播/补发与竞争机会成本？

前人证据：GOSC/PragComm/ToM2C已有receiver信息估值；本项目免费特权pilot0/6过门槛，不等于无价值。文献新颖性不再重做或扩大检索，本轮仅以已读原文和当前源码为证据。

设计：只在extensions新增审计候选codec（非GOSC兼容wire格式、无估值策略），scripts新增有界观测/成本分析，tests_ext验证帧与信息权限。原GOSC/core/旧冻结协议/历史结果不改。
计算全部HPC登记：5分钟测试上限、10分钟审计上限，CPU workers<=2/数值线程1，0GPU/0HTTP/0训练。对旧calibration12000000/12000001、两W选定publicToM共4条做被动观测，并以4条未观测control核验同策略结果/世界不变；不作新独立N或任务收益检验。仅有审计副本的codec时延、字节和shadow机会成本，不声称真实空口或paid-summary任务效果已实测。

事前固定候选：去target-only重复；novelty为本地own_pending相对本地已接收common belief的TV三bit分桶，不能叫正确率；选加fresh pose（原EVID已传过，但可能陈旧）。time用9bit覆盖400slot，session/restart需另行协议；不使用任意Agent其他私有状态/未来真值。对3/4byte应用帧真实编码和CRC16例子测长，HDR/CRC不能双计。原32bit草案另行列缺口，不静默改其冻结定义。

成本表：H=0/16/64，rate=.25/1/2/6，W=50/100；被动shadow每1/5/10slot刷新，H16，按原fixed-rate及最小可容纳更高rate规则；只评估对原剩余容量是否挤占、同slot观测信道能否解码，未实际竞争或改变策略。成功UL需再广播给发送端；统计新增DL payload/非空slot额外帧头/可靠ACK，保留理想DL范围。丢失/延迟/catch-up依源码审计说明，完整付费链路验证仍未做。禁止把shadow成本当实际任务效果。

验收：逐字段权限/冗余/表示损失ledger；两调度路径的成本/可用时序映射；HPC原始观测、control结果一致、codec测试、成本表/微基准、明确不包含的成本及Go/NoGo。若仅有聚合信息且无法接入原ToM，不凭空发明估值公式或进入训练。旧材料缺口继续独立列出。

## 后续有界传输核查授权与范围

用户在首次shadow结果后明确批准“写入、HPC核查并同步”，对象是独立receiver_summary_transport_audit_v1.json冻结的96条件；复用4校准轨迹，至多10分钟，不训练/不改任务策略。新增反馈/快照实际编码、ACK丢失、剩余预算排队/重试/TTL，仅作条件成本/可达性诊断，不冒充最初设计的确认性任务效果实验。五个run均完成，最终23测试通过；旧协议和失败/结果不覆盖。
