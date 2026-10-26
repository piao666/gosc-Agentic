# 摘要成本 / age机制：后续协议审阅候选

状态：**review_candidate_not_executable**。用户本轮授权的是审查；本文不是新实验预算、冻结配置或收益承诺。现有GP-v2 No-Go、原N上限和预留test封存继续有效。

## 必须先识别的问题

[CODE] 当前age仅用一个正标量f缩放同次决策全部候选价值。在理想目标层面，`f*sum(V)-p*C`等价于`sum(V)-(p/f)*C`。所以paid-age的观察优势不能直接归为pose内容或receiver-aware语义效用；时间戳信息本身仍可能有价值，不能反向声称“age完全不需要信息”。

[RUN] 现有日志没有逐决策factor、有效时间戳、prestate候选与DL类型，当前不能用重仿真生成另一套历史后假装补齐原观测。新研究需要前瞻观测合同。

## 优先的最小机制对照（尚未实施/运行）

| Arm | 使用信息与动作 | 要分离的问题 |
|---|---|---|
| public-fixed | 原本地ToM，固定price，无付费摘要 | 原公共估值参照 |
| native-age / native动态price | 仅实际收到的native EVID时间戳；f_native，或显式p/f_native；不发摘要 | 本地陈旧度调价是否已足够 |
| paid-ignore | 原公共估值但真实发送/计费摘要 | 付费服务本身的成本/时序影响 |
| paid-age / paid动态price | 只用已收到且有效的新摘要时间戳；位置不投影；仍真实付费 | 买来的时间戳是否超出native动态price |
| paid-pose | 已收到新位置仅进入估值副本，其余不变 | 在统一调价/信息/成本边界下，位置内容有无额外价值 |

native-age与paid-age不是同信息量对照：差异正是要计价和检验的信息获取。它们必须保持任务候选、Planner/Channel/服务和实际成本比较规则；不能让免费baseline读取paid cache或peer隐藏最新状态。不能因为现在age均值最好就事后把它改成已确认主方法。

## 先补观测，再讨论降成本服务

- 每次真实估值保存sender/t、native/实际收到摘要的created/received/TTL、eligibility原因、f、基础price与effective price、候选key/值/长度、选包signature；观测不得修改策略、随机流或读取未来reward。只记录本地可见内容。
- 每个DL frame保存enqueue时刻、id、kind、bytes、required/served uses及mission末未服务量；CPU received作业同时记消息类型，分清offered/served/received/decoded/decision可见边界。
- 可审阅的降费候选是延后编码/合并覆盖的待发生成、真正编码的捎带、对控制ACK的接收/解码路径优化；它们需保留CRC/地址/长度/反馈时延/TTL/丢失风险并计价。不能先删费用、再报告任务不变。
- 只去掉现有3个常0 bucket bits仍使4byte app占满4bytes，不能据此宣称独立6byte UL帧变短。换更短时间戳/隐含身份/组合帧，须另外检查歧义与过期/重传合同。

## 后续执行关卡

先做无新任务收益的观测等价/选择器边界合同，再做有硬上限的成本探测。若通过，才前瞻冻结未曝光world、有限候选、强简单baseline、实际通信/逻辑CPU与实测compute口径、主要端点、N/预算/停止规则。原12校准world已曝光，不能再称独立验证；正式test预留集合不得用于新方法调参。新硬件模型、研究目标、任务/数据划分或长实验需另作明确决定。

Go仅限审阅候选，**不允许自动扩N、扫参、替换主方法或启动训练**。现有负结果、失败和原作者复现缺口分别保留。
