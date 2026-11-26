# T3-R-v2-I 精确词表计数资源修订申请 v2

> 当前状态更新：用户已明确回复“批准这1次计数及2GiB AS修订”，授权JSON单列。hpc-t3rv2i-counter-v2-20261126已按同一输入完成；原1GiB失败保留。下文Pending为提出时记录，不回写原budget v1。结果见11月26日压力资源报告。

2026-11-26，Asia/Shanghai。**Pending / NOT AUTHORIZED；未执行本修订。** 原model-free budget v1保持原样，不回写为已批准或已通过。

## 已完成与精确缺口

[RUN] `hpc-t3rv2i-contract-v2-20261126`：54项新版无模型测试通过；`hpc-t3rv2i-legacy-20261126`：67项旧synthetic回归通过。它们不代表新真实模型、部署或任务能力。

[RUN] 压力v3已在HPC保存完整人造请求列表及`counter-input.json`。唯一获批的helper批计数在继承AS=1GiB限制下报`runtime: out of memory: cannot allocate 4194304-byte block (8060928 in use)`，外层run exit1，未返回有效计数；stderr、输入和失败状态保留。该run child_max_rss=58816KiB，不能把低RSS等同于有足够虚拟地址空间，也不能证明失败唯一由AS导致。AS约束与Go虚拟地址需求不兼容是待验证解释，不是物理RAM不足的证明。

依本轮用户明确要求“超出授权边界时先停止并提交预算申请”，以及AGENTS E/E1资源与执行地点规则，原一次helper额度已用完，停止再次计数。结构审计、失败审计与完整回传可在原剩余预算内继续。

## 唯一建议的受限修订（需明确批准）

| 项目 | 修订候选 |
|---|---|
| 目的 | 只复核已保存的同一批合成人造完整输入；不再生成消息/构造新题或新协议 |
| 输入 | 固定压力v3的`counter-input.json`，以SHA冻结，先核其全部messages对应已存synthetic-requests，不读任何MASBench正文/gold |
| helper | 原SHA e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5；不重编译/安装/下载；原template/manifest pins不变 |
| 次数 | **额外最多1次**vocab-only批调用；即本任务累计helper尝试最多2次（第1次失败保留）。非真实LLM/服务请求 |
| CPU | HPC≤2核、单批/无并行，GOMAXPROCS/OMP/BLAS≤2，helper CPU≤20s |
| 时间 | helper≤20s，count-only登记≤40s；再核查审计≤30s，均从原660s计算总量及900s登记总量剩余额度扣除，不增加原累计时间 |
| 内存 | count-only Python/Go子进程各**硬AS≤2GiB**，不再是1GiB；RSS每0.05s观测停止阈值512MiB，采样不冒充硬RSS上限；实际容器quota需复核 |
| 存储 | 原输入只读复用；单新run output≤8MiB、stdout≤6MiB，沿用累计outputs≤24MiB、新SSD≤64MiB/HDD新增0；不足先停，无额外清理历史结果授权 |
| 成功条件 | vocab_only=true、tensor_context_created=false、完整输入/模板/render/token_ids SHA与长度一致，记录每请求实际tokens及16384/512安全判定 |
| 失败 | 超时、OOM、身份/usage/计数/资源/输出异常均停；保留原始stderr、stdout（在cap内）和journal，不再试第3批，不提升AS/窗口/模型 |

本修订不改16384/512真实候选窗口、Prompt、parser、评分、D1或探索门槛，不新增真实LLM、Ollama metadata/生成请求或服务切换，不授权原四题能力诊断、T4、正式校准/test/训练、Git提交推送。

冻结输入：`research/sync/runs/hpc-t3rv2i-pressure-v3-20261126/outputs/counter-input.json`，SHA-256 `f74a175d813aa004fa2135a13799e95575b3c68b6c443f7901bea6be3c4da0c2`；对应synthetic-requests SHA `55eb321df2acde7171562910fb0f05e4fb855e196ce7ec8fe8861f02b1e46c6d`。不得换另一批输入后沿用本批准。

即使补验成功，也只能支持**这些合成输入的词表计数**；真实服务有效窗口、render/usage绑定、真实资源硬上界与科研能力仍各自Pending。用户需明确接受“1次额外计数及2GiB AS”，本文件本身不构成批准。
