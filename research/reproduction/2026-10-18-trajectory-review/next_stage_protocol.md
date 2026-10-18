# 下一阶段待批准协议：原14点rep0的逐slot观测回放

**状态：提案，未批准、未实现、未运行。** 当前用户授权仅已有轨迹审查，本文件不扩张授权。

## 问题与范围

[HYPOTHESIS] 当前next-plan之后的决策变量缺失，无法解释延迟轨迹分叉的具体原因。先补可观测日志并核验无扰动，不先做关闭迟滞/免费私有belief之类机制干预，更不训练估值器。

- 固定原14个point/packet、原开发world5000–5007、**replicate=0**，success/failure各一条，共**最多28条重新执行的continuations**。它们是观测回放，不增加独立world/MC样本或替换原结果。
- 保留原native顺序、原decoder调用、原stream key与ACK/queue/fusion/motion；不改scheduler/channel/Planner/阈值/价/预算。2workers各1数值线程，新目录，不覆盖旧数据。
- 由旧112条/70.76s与784条/413.06s成本粗略外推，预计15–35s；**仿真wall上限120s、最多28条，不自动重跑/补样**。这是估计不是实测；契约/完整测试与归档另计，无GPU/LLM/API/下载/安装。
- trusted本机自产checkpoint先以同一bytes验SHA再反序列化；source/config/tape/原raw/依赖/测试gate全部匹配。原实验源码/结果继续保留。

## 只观察，不改变因果处理

在每slot现有phase边界采集target_before/after、pos、old target arrival、无jitter的old/best分数和best cell、margin、local/shared/private belief hash/norm、declared/确认集合变化、selected/delivered packet ID、资源增量、各RNG before/after hash。小体积原始感知record与消息描述保留本机，用以区分belief更新、位置刷新与重传时序；不向线上估值器提供这些离线诊断字段。

日志hook不得额外调用plan/sense/transmit/channel或消耗随机数；只读取已产生状态，任何重算也不能改变浮点数组/缓存。完整belief如需保存只存本机并控制体积；优先hash与必要局部证据，不上传checkpoint/PDF/私有状态。

## 验收和停止

1. 先完成针对hook无扰动的契约和现有完整测试，冻结源码与approval/gate hashes。
2. 每条回放与既存rep0的result（除wall/CPU/RSS外）、完整trajectory、final state hash、初始/结束future RNG hash逐项相等；**28/28严格匹配**才能解释新增日志。不以容差悄悄放宽final-state标准。
3. 异常/timeout/不匹配保留失败与partial后停止，不追加预算、不替换旧数据。若增加日志导致hash结构变化，预先只在外挂collector记录，不向被哈希sim注入持久字段；否则先修契约，不在结果阶段豁免。
4. 全14点/两分支出逐slot证据链，区分可观测关联与待拆分因果。rep0不是总体代表性证明，不作新的性能推断/重复累加N。
5. 只有新日志能够支持明确机制问题，才另审mask/history/private/position拆分对照与成本协议；本协议不授权这些消融或M0训练。

完成后报告并停止。本方案仅解决日志缺失，不能保证发现可修复缺陷，也不能改判strictR4或R4-S1复现状态。
