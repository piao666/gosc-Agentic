# Research Task Brief — 同步成本与估值实际改变率审查

- 用户授权审查前轮负结果。已有dirty文件均为本会话连续任务资产，保留，不reset/checkout/clean、不提交/推送。
- [CODE] base4ff4147654c07781d77a42acee3f31c0b8792f38；原校准run hpc-periodic-independent-calibration-20261023，冻结research/protocols/periodic_crn_stage_v1.json。原结果/源码/协议不改。
- [HYPOTHESIS] 摘要送达后可能因TTL、本地EVID更新或相同位置而不改变投影；投影改变也未必改变裁剪后的候选价值/最终选包。通信成本可能来自ACK滞后重复UL、summary反馈、全历史task重播与CPU/排队，不能只看summary应用字节。
- 先审查现有总账与源码；现有记录缺逐决策价值和分类DL/重传账。因此新增仅观察的诊断包装器，回放原12calibration world的public_tom/paid_pose两arm，共24条，不新增world/N，不运行reserved test。
- 记录链：peer机会→有效/较新pose→坐标变动→相同pre-state下candidate expected-value变化→实际选择变化。shadow只重复只读build_groups和确定性lagrangian_select，不向其他分支推进、不读未来奖励/隐藏状态、不改变Planner/随机场/服务。
- 包装已有service回调，按实际attempt、DL frame id与实际服务uses分解任务首发/失败重试/edge已收但ACK未到重复、summary、ACK、task首次广播/历史重播、CPU工作/排队/slot量化。逐frame保留右截断，不把offered等同served。
- 每条回放result必须与原结果逐字段完全相同（curve、成本、队列、指纹等全部），不匹配即失败、停止解释新增trace并保留证据。原冻结源码SHA核验通过后才回放。
- HPC预算：合同timeout120s；24条诊断回放timeout360s（原两arm合计约87.5s，额外shadow估值预计增加一倍以内，硬上限约4倍原成本）；逐任务60s。单进程、数值线程1，既有2CPU/24GiB配额；0新LLM/API/GPU/下载/训练。分析/独立算术审计另60s。仅新outputs写入登记run，不覆盖旧结果。
- 验收：纯观察包装器合同、24/24原结果精确匹配、UL/DL/CPU分类与原总账相等、带明确分母的改变率、全部seed保留、局限/替代解释/下一步建议。当前No-Go不因诊断自动撤销，不调协议/价格/样本。

辅助观察修订：首轮24回放/审计完成后，静态复查发现summary_same_generation辅助计数会把同slot其他快照未修改的cache项重复计入。原result、主要价值/选择/成本指标不受影响；保留v1，修正观察对象identity判定并加针对性合同。v2重复原24条（仍新N0，累计回放预计约252s，低于原360s预算量级），必须再次精确匹配原result；独立审计也用新runID。后续报告以v2观察记录为准，不把未使用辅助计数当旧校准错误。

v2硬timeout230s（首轮实际125.882817s，合计上限355.882817s），不重新获得一份360s实验预算；独立审计同时逐项核验v1/v2的主要价值/UL/DL/CPU统计相同。
