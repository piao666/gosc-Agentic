# 下一阶段提案：固定checkpoint的MC标签精度检查（未批准/未运行）

## 为什么先做这个

[RUN] 本pilot8missions、14点、R4，12/13个非零点的MC SE不小于|均值|，所有主要mean/rho区间宽且跨零。当前不足以判定某个消息稳定有害，也未证明ToM不如简单特征。不能直接据这些有噪声标签开发复杂估值器或挑有利seed。

## 具体新批次（仅提案）

- 固定当前14个point_id/packet_id（per_point.csv），复用可信本机snapshot/tape；0个新world，8个既有开发world不变。保留2个空时隙，不补点。不把它们叫unseen evaluation。
- 保留replicate0–3原结果；新增 **replicate4–31**，每点success/failure，最多`14×28×2=784`新增branch continuations，合并后每点R32。源码核心、配置、selected packet、native当前时隙tape、解码干预与5条future RNG key定义不变。
- 新runner/version、输出目录与manifest，不改旧数据/协议/冻结分析；读取pickle前核验自产路径、源码/配置/环境/tape与state hash，不读取来源不明文件。旧112条均保留原hash。
- 2workers各1数值线程。按本次112branches/70.76s线性外推约 **495s=8.3min**；只是估算，轨迹异质性/IO与调度会变，建议wall15min硬上限。没有GPU/API/模型下载或额外训练。
- 主目的为估计**同一packet标签的MC收敛**，不是扩大独立mission N。合并R4/8/16/32均报告mean、MC SE、正/负/零配对分布和真实下一次目标变化；预先固定所有层级，不按正结果提前停止/增加R或筛除点。
- 保留当前mission等权/cluster统计，同时披露R32仍只有8clusters；不得把14×32个配对当448个独立mission，不能据重复增多宣称跨世界稳定。
- 先判断噪声是否降低到能支持标签解释；符号仍不稳则保留连续均值/SE，不硬分好坏包、不训练标签分类器。若未来要比较receiver-state估值器，还需单独审定可观测特征、同步费用和M0基线；本批次不实现它们。

## 边界

当前批准128上限内实际112已结束；剩余16不是自动扩展R的授权。新增784超出当前范围，须用户确认。当前实验/报告为complete；新提案not_run。原strictR4 failed和R4-S1 inconclusive继续保留。若不批准该精度检查，可在目前证据处停止该机制路线；不能宣称已证明receiver状态无用。
