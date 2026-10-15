# 待确认方案：限定ToM路径的receiver因子诊断

**状态：未批准、未执行。不是把整体R4-S1改写为通过。**

## 为什么提出范围变更

[RUN] 全部5200次已完成；104项中4项均为throughput低eta的不确定结果，整体R4-S1仍Pending。ToM的原private600条及冻结headline的GOSC600条保存字段无差异；W100 ToM700条也无差异。后一headline仅保存task/symbols。因此已有直接证据支持在固定本机环境中单独研究ToM的receiver假设；尚不能声称强throughput比较基线已完全统计复现。

[HYPOTHESIS] receiver的私有证据与真实位置对ToM决策的作用可以在这一已核验路径中分离，而不依赖throughput数值问题先解决。这是探索性机制诊断，不用于宣称新方法超过throughput/AoI、SOTA或等成本任务收益。

## 具体执行（沿用原先冻结设计）

- 原`gosc`、Planner、scheduler、channel、task、eta全部保持；仅已测试adapter改变TeamModel的可见receiver信息。
- 3个原search设置default/W50/snr-5；4个模式shared/private/position/joint；独立seeds4000–4099，1200次重新运行。
- 六个主要单因素对照，paired bootstrap4000次、Bonferroni6区间、实用效应至少shared均值5%；joint与交互为次要。同步/访问特权状态不计价，明确固定eta而非等资源。
- 首先复核shared/joint endpoint与原实现一致的contract及adapter哈希。所有seed、负结果、例外和完整输出保留。
- ≤4workers、每worker1数值线程，估计5–15分钟，上限25分钟；不下载模型/安装依赖/调用API/改核心算法。
- 原strict R4保持failed、R4-S1保持inconclusive；新的门控准入单独记录为`tom_path_diagnostic_only`，不能伪造旧passed manifest。
- 不改变6个主要比较、4000–4099 seed集合、5%实用阈值，不训练新估值器，不追加任务/模型。

## 验收及停止

报告N、配对CI、正/负seed、资源UL/DL和失败。即使某模式有收益也不自动认定论文创新或可部署收益。若无稳定实用收益，明确报告负面证据并停止方法堆叠。下一步是否需要更真实任务/成本匹配须另行审查。

## 必须确认的原因

本轮已冻结的`statistical_protocol_v1.md`明确规定所有104项通过才允许receiver实验。现在4项不确定，限定路径准入是基于已见结果提出的**协议范围变更**，不能擅自执行。批准此具体方案后才修改准入逻辑并运行；原始失败和不确定记录永久保留。作者询问仍为本地草稿，发送渠道/收件对象须另行明确。
