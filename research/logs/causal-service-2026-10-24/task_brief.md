# Research Task Brief — 2026-10-24

- 科学问题：[HYPOTHESIS] 统一可因果观测的反馈/CPU时钟、限制盲目重播之后，已接收pose估值能否在强简单对照和实际成本约束下获益？本轮首先检验服务合同，不预判收益。
- 前人成果：[CODE] 基线47389eba9c6e2838139df3aa47863ab88634e97a；此前12独立world校准No-Go、48次同world观察不是新增N。来源为periodic_crn_calibration与sync_cost_value_review两份2026-10-23报告。作者原校准/cache生成链/历史数值差异仍另列，服务修订不能填补这些缺口。
- 拟修改：extensions服务/适配器的默认等价扩展点；新增因果时钟及有界catchup服务、paid-ignore/age/shuffle估值；tests_ext合同；新协议、HPC运行与审计脚本、报告/状态入口。原gosc/results/cache不改。
- 时钟：RTO下界=1+传播delay+ceil(decode_seconds/slot_seconds)，不读未来队列；实际排队仍可能超时重传。任务和摘要采用同一预设下界。估值工作按固定场景参数入共享CPU队列，另记录实际process/wall耗时，不声称硬件部署测量。
- 重播：只按edge接受时间、固定年龄窗/次数/刷新轮帧数选择；不查询任何receiver是否收到。保留在途帧、丢失风险和mission末尾censor。
- 验收设计：旧合同回归+新合同（时钟、旧ACK、新generation、丢失、预算/CPU/TTL、catchup界限、消融局部信息/CRN）；合同通过后独立新world清单冻结与成本probe，预算合格才独立校准。校准之前冻结候选、端点、停止规则；不能扩旧N救结果。
- 成本上限：合同300s；prepare120s；probe120s；条件校准600s且保守投影<=480s；单worker/数值线程1、现有2CPU/24GiB以内、0GPU/0LLM/0训练。正式test未授权，N/预算必须经新校准提出；若合同或公平支持失败则停止依赖步骤。
- 可能反例：减少重播损害peer知识/完成率；同RTO不代表同ACK实际等待；摘要虽改变选择仍无净收益；单个price无成本前沿支持；固定CPU假设对结论敏感。
- Git/HPC：启动本地clean47389eb，HPC4ff4147是其父提交。同步工具禁止不同HEAD；先核对/备份远端原同步工作树和索引、确认严格祖先，再仅快进引用/索引并用SHA同步源码，保留原始结果和远端独有文件。无运行中登记任务（pgrep无匹配导致SSH退出1，不是身份/环境失败）。
- 本轮最终产物：实际命令/日志/逐run receipt、合同结果、失败记录、范围限定的报告；不提交Git/不push，不把新协议仿真称作者原wire精确复现。

## 已执行关卡（保持上述事前计划不改）

[RUN] 187主回归+28补充合同通过；冻结214world/21候选；42短probe和独立事件审计通过。按原公式投影895.5021709203719s>480s，因此没有启动校准。已向用户提交独立预算提案（投影门槛1080s、hard timeout1200s），提案不是批准。本轮没有校准任务收益分析、正式test或训练。详见本轮报告、各run manifest及delivery记录。
