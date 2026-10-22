# 数学结构清单（2026-10-20）

[PAPER] 公式以本地PDF为准，完整上下文见各reading_notes；本清单未提出新定理。

| 来源/锚点 | 目标与变量 | 可用条件 | 不可直接迁移的结论 |
|---|---|---|---|
| D01 p.4–6 Eq.4/5、Thm1/2 | 候选包/可靠性选项的ToM价值减资源price，multiple-choice knapsack | value/price单位、固定payload选项、单slot可行约束 | 单slot解不等于mission全局最优；误差鲁棒性有阈值/乘性条件 |
| A02 p.3–6 Eq.3/6/9/10 | 固定packet准入，RCE两上下文评分；bytes/queue/context资源价格 | offline profile/validation/test隔离，已完成service反馈 | RCE不是任意上下文因果真值；非自由在线Agent拓扑学习 |
| B04 p.3–9 Eq.11/14/19、Alg2–6 | 加权任务成功η(o)×timely delivery；压缩/功率/带宽/二元用户 | 代理曲线拟合、特定信道、共享importance、SCA近似 | KKT子问题结论不等于原联合混合问题全局最优 |
| B10 p.3–4 Eq.2–8 | IG权重×拟合量化utility，离线表＋online RB greedy | 固定encoder/importance与slot容量可知 | 非凹情况下greedy无全局最优保证，可加代理不证明真实utility可加 |
| D08 p.5–6 Eq.1–6 | ToM监督目标/观察预测；删消息KL阈值监督边 | CTDE标签与部署特征权限区分 | subgoal KL非整段任务因果收益，float长度非空口成本 |
| D10 p.5–7 Eq.13–22 | 长期J、传输F、预算MDP/Lagrangian/Pareto slope | Markov/稳态/成本/ACK条件 | 不能从有限LLM任务散点推出最优凸分段线性前沿 |
| A01 p.3–5 Eq.1–11 | learned complex symbols、语义cosine与任务CE/LoRA | 指定视觉task/训练体系与SNR条件 | 不能把包准入称为JTCM或把LoRA收益归因估值 |
| B01 p.3–6 Eq.1–14 | semantic/channel编码、CE加MI估计 | 文本重建与所训练信道 | embedding相似度非任务成功，MI估计非容量最优证明 |

[HYPOTHESIS] 候选V(m|O,t_arrival)为可观测信息条件下的到达增量任务效用；与packet可靠性只合并一次。正式实现前定义任务reward、时间截断、不可达/失败与标签成本。首先经验检验，不套用缺少假设的最优性定理。
