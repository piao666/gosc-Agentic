# Research Task Brief — 2026-10-25 摘要成本与age/动态price审查

- 科学问题：[HYPOTHESIS] paid-pose开销的哪些部分可从现有账本精确识别？age的观察优势是否可能主要来自统一价值缩放/动态price，而非pose内容信息？
- 授权：用户“进行审查”；仅源码、原252校准任务数据与有限选择器合同诊断，无新mission、调参、正式test、LLM或训练。当前dirty均为本会话前轮授权成果，保留，不reset/覆盖；Git起点47389eba9c6e2838139df3aa47863ab88634e97a。
- 前人成果：[RUN] 12独立world×21候选，950281事件已独立核对，原No-Go/N21907>200保持；[PAPER] 本轮不新增论文原文/新颖性主张；沿用既有纸码映射。
- 关键源码：[CODE] causal_paid_simulation.select/valuation_view，paid_receiver_service.tick/_cpu，summary encode/feedback/batch，lagrangian_select、WireGOSC.build_groups。冻结方法文件不修改。
- 文件：新增纯分析脚本、选择器/成本边界合同及审查协议/报告；更新状态入口。每run的inputs SHA/commands/raw-derived outputs保留。
- 设计：分析原始252行与950281日志，精确UL摘要uses、CPU action计数、重播bytes；DL帧kind及age factor未记录，禁止用重仿真补造历史观测。DL摘要仅给可证明界，说明计费/控制路径，不把差值伪作精确分类。
- 数学：f=1/(1+mean effective age)>0，目标f*sum(V)-p*C与sum(V)-(p/f)*C的理想最优集一致；不假定有限精度选择器/闭环轨迹逐位等价。仅固定合成候选和factor/price网格检查实现，非新的任务结果。
- 成本：HPC单worker/数值线程1，现有2CPU/24GiB；合同<=60s、现有数据分析<=120s、独立复算<=120s。0GPU/0新LLM/0新mission/0训练，不使用任何预留test世界。
- 反例：age在price0下理想不改变目标但实际结果不同，不能无证归因浮点；任务回路/有限精度/未记录状态须区分。摘要买得更便宜不保证任务收益；同曲线或计数不证明全payload/接收轨迹相同。
- 验收：原冻结/decision/结果身份校验；UL拆分和DL界不越账本；固定轨迹费用删除仅称会计敏感性而非可实现效果；选择器诊断保留全部不一致；独立审计、两端receipt、明确新协议仅review_candidate，不撤销No-Go。

## 实际完成（保持上述事前范围不改）

[RUN] 18合同通过；1536固定合成选择器比较0不一致，未称普遍逐位等价。读取原252任务/950281事件，v2收紧非购买分支DL摘要上界为已知0并补充生成预留下界，首版保留。独立v2重新解析252事件文件复算UL/DL/CPU action/重播bytes、费用界及汇总，2.496631s通过。新mission/N/正式test/LLM/训练0次。缺失历史DL kind和age factor仍明确标为未记录，未重仿真补造。

[RUN/CODE] age理想目标等价p_eff=p*(1+mean_age)，当前仍缺native-age不买摘要对照；选中pose精确摘要UL20516uses，固定账本将其全免仍超主要成本阈值。原No-Go保持，新协议只为审阅候选。详见本轮报告和最终delivery.json；本轮未Git提交/push。

[RUN] 5个审查run均正常完成，精确命令及实际资源/sync身份保存actual_commands.json；最终receipt research/sync/receipts/20261025T140226Z-a6af80.json的all_outputs_mirrored=true。18合同是本轮新增检查，不将原190合同冒充重跑；1536选择器比较不是mission或独立N。
