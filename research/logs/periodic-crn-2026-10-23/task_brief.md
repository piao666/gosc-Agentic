# Research Task Brief — 同格式 periodic、配对噪声与独立校准

- 用户授权开始此阶段。已有未提交内容属于前序连续任务，原样保留；不Git提交/推送，不改原gosc/tests/results/LICENSE。
- [CODE] base 4ff4147654c07781d77a42acee3f31c0b8792f38。阅读原SemanticAggregated/RateAware/Filtered/Suppress、Channel、Simulation和新GP-v1适配/服务。periodic沿用相同语义过滤，按周期准入、CONF严格优先、FIFO evidence prefix和实际帧长的期望goodput选率；重传与CPU/DL服务各arm相同。不是原SEMA/fragmentation的逐bit复现。
- [HYPOTHESIS] 强简单对照补齐后，付费pose是否仍有足够任务/成本headroom支持一次独立验证？先验证外生随机场对策略消费顺序不敏感，再作新世界独立calibration，不将旧fixture计入N。
- 修改：新periodic、event CRN、HPC专用运行/分析脚本及tests_ext；原生适配仅加选择/随机事件hook，默认行为保留。传感噪声按global cell、slot、agent；fading/planner按slot/agent；FBL按slot/agent/完整wire digest；DL按到达slot/receiver/kind/wire digest。
- 预算：HPC合同timeout300s，成本探测timeout120s（2个新world、12候选、24slots），0LLM/GPU/下载/训练。独立calibration最多12新world×12候选×400slots，仅成本探测推算保守总wall<=480s时执行，硬timeout600s，单进程数值线程1、RAM上限24GiB；不达门槛保留预算阻断。所有run登记并回传；不在本地计算。
- 配置为场景假设：UL100 uses/agent/slot、DL2000 uses/slot、slot1秒、编码/解码各0.001秒、TTL20、catchup5、服务额外delay0、DL独立丢失0.05。不称部署测量。基线periodic间隔1/2/4/8×filter_eps0/0.02，加bits/AoI及public-ToM/paid-pose（同price1e-5）；这是冻结的有限候选族，不称全局最强。
- 独立性：HPC登记源/协议/任务账本可发现seed和world查重，排除原split、旧pilot与所有合同seed；成本probe与calibration、预留test互斥，test不运行。未记录的外部实验无法据此排除。
- 功效：两个主要比较×任务/总UL+DL成本四端点；Bonferroni单侧alpha=.0125，联合power目标.8（各端点.95）。任务阈值3slot、设计备择6slot；成本比阈值1.05、设计备择1。校准bootstrap95% SD上界、正态近似估N，最低40、最多200world；小校准下仅规划近似，零方差不当已证明零风险。若需N>200或校准无任务改善且成本更高，冻结No-Go/不执行，而不追加样本救结果。
- 验收：HPC回归/CRN合同；原始每world/candidate结果+成本+指纹；独立校准统计和机器可读预算/判决。最终test预算提案可冻结，绝不自动执行test或训练。若校准/成本门槛失败，明确Pending/No-Go原因，不虚构已冻结可执行campaign。

事前实现修订（尚未运行probe/calibration）：合同v1/v2各155通过/1失败保留。夹具显式隔离pending与INTENT预算；同时短包选率改为期望有效bits/channel-use，避免只最大化成功概率而占满短包slot。支持范围/候选数/世界/预算不变。
