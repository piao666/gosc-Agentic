# 基线合同（2026-10-20）

| 候选对照 | 本轮状态 | 公平比较要求 |
|---|---|---|
| 原GOSC ToM/bits/AoI/TV、tuned periodic | [RUN] 原源码可执行，部分复现完成/差异保留；不是全部P1验收 | 同world/seed/候选/表示/调度/channel，按实际资源前沿；不等η |
| M0 type/size/age/公共metadata轻量规则、线性或lookup | [HYPOTHESIS] 未实现 | 与复杂模型相同训练/调参预算和可观测权限；强简单对照优先 |
| M1同容量无receiver摘要/有摘要/shuffle/仅age | [HYPOTHESIS] 未实现 | 容量与训练样本相同；新增摘要成功送达且全成本计费 |
| BANDMAS-style metadata/shrinkage/adaptive admission | [PAPER] A02原文读过；未运行其官方系统 | 若适配须另名，不把固定文本QA lossless数据直接混为网格空口baseline |
| ToM2C-style goal-change proxy | [PAPER] D08原文读过；未训练 | 原ToM2C是CTDE/GNN/学习策略，改成固定GOSC估值仅是机制适配 |
| iCoTASC-style offline importance lookup | [PAPER] B10原文读过；未训练 | embedding量化/RB与typed message/mission不同；不能直接搬数值 |
| JTCM/DeepSC/AgentComm/B04 | [PAPER] 原文已读；官方代码未执行 | representation/encoder/LLM或任务不同，第一篇作为机制对照；若做数值需统一task/模型/资源 |
| privileged receiver全状态/任务真值oracle | [HYPOTHESIS] 仅未来离线headroom诊断 | 独立标oracle，不称deployable；访问未来真值禁止参与在线调度 |
| Genie | [CODE/PAPER] 理想通信参考 | 不是任务最优上界，也不是免费新增receiver状态的科学证明 |

源码可追溯目前仅本项目GOSC HEAD876fc523/upstream387b493；其他repo入口/commit/可执行性未独立核验。不造官方实现或虚称已复现。所有新对照计算未来仍在HPC，当前未开始新方法训练。
