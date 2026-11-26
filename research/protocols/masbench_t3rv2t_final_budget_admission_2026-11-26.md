# T3-R-v2-T 最终预算与执行准入矩阵（待批准）

2026-11-26 Asia/Shanghai；base `c0621a1ab2cc249bbb6acb3b81cf1cec14591bcd`。这是新任务阶段候选，不是旧2000秒阶段的续跑，不构成真实任务运行授权。

## 任务、身份和历史债务

[CODE] 新计划 `masbench_t3rv2t_plan_2026-11-26.json` 只从历史计划取四家族ID/私有视图SHA元信息，8个episode按预先交替条件顺序逐个执行；6机会/episode，24机会/条件，最多48次任务生成。每个episode重新构造两个Agent、transport、packet累计状态；全局账本/截止/调用和字节预留永久累计。无并行、缓存、失败补请求、跨episode上下文或结果重用。

[RUN] 历史两次人工probe仍绑定Git458a96f、snapshot20261126T032819Z；输入625/8720、输出14/14，108.091165秒。长输入invalid_exchange与原2000秒连续交付超期不撤销。父journal SHA `314f853404d1e0b5c60f80583c9c134e58ba7dfa7dab5df3a0ab580cebd1f79c`，历史起点49751956.782184586，不退款、不更换起点。新阶段最多48，合计最多50次生成。两阶段分别原HTTP上界156和新440，保守关联上界596，不能再写468。新阶段独立18360秒上界不能宣称原期限内完成。

## 精确计量与请求上界

| 项目 | 新阶段永久上界 | 接线及失败语义 |
|---|---:|---|
| 真实任务generation | 48 | 发送前唯一永久reserve；每episode6、每条件24；未知usage保留512输出/完整输入预留并fence |
| 原生render HTTP | 48 | 每slot1，model/runtime/完整render与计数同源；不是免费生成 |
| 任务GET | 152 | 每episode首slot空驻留8 + 每slot render后ps/version与发送前identity共3×48 |
| cleanup GET | 56 | 每episode清理前1 + 最多6次退出观察；不是生成重试 |
| unload | 8 | 每episode一次，失败不再次尝试；陌生runner不卸载 |
| lifecycle GET/准备尝试 | 128 | 两次启动各最多61，含listener未就绪的永久计价；其余idle/回滚共享剩余6，不够则停 |
| 全部HTTP | **440** | 上列之和；连接失败亦不退款，无外部endpoint |
| 完整输入vocab-only helper | **56** | 8个初始本地输入预计数 + 每slot即时重计数48；无新增合成生成；helper不能创建tensor context |
| 服务start / stop | 各2 | 1024→16384→1024，journal先计数；分离spawner保留服务AS继承 |

[CODE] qwen2.5:7b、Ollama0.11.11；模型manifest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`，权重SHA `2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730`。实际模型/模板/helper/服务PID+stamp/16384有效窗口必须逐请求绑定，metadata标签不能替代实际证明。完整字面Prompt SHA沿用 `00c91af181b4bcedf62acbfee2ab77b8555392d07a52196d3878936d4a375fb4`，不调Prompt。

每slot精确完整输入≤15872，固定最大输出512，总窗口≤16384；最大永久输入预留761856、输出24576。即使实际输出较短也不退款。计数器必须证明完整request SHA、token IDs及其SHA、全render与SHA、模板SHA；原生render与helper逐字节相同，usage.prompt_tokens必须等于计数。逐slot真实信息依赖上游消息，8次初始计数不能代替其余即时计数。

## 墙钟、资源与证据

| 阶段 | 秒上限 | 依据及剩余限制 |
|---|---:|---|
| 48×准备 | 7200 | 每slot150，helper≤20、render≤120，共享准备截止 |
| 48×生成 | 8640 | 每次180，含发送前identity；旧60秒被T1/T2/T3否定，不复用 |
| 8×清理 | 320 | 每次40，完整PID/驻留/GPU退出栅栏 |
| 生命周期/事前 | 600 | 8×20初始helper160、全权重SHA≤120、启动/退出及检查共享；非额外budget |
| 应用/序列化/计量 | 600 | 有限文件、单进程；未通过现场最坏时间证明 |
| 独立审计 | 120 | 新任务审计尚未现场执行，不用本轮fixture审计冒充 |
| 完整回传 | 600 | HDD索引、逐件SHA、双端receipt；失败不释放科研继续门 |
| 安全余量 | 280 | 不用于额外生成或重跑 |
| **总计** | **18360** | driver在17360停止正常执行，留1000给审计/回传/余量；每dispatch另检查安全尾部 |

[HYPOTHESIS] 这是分项候选上界，不能保证48次一定完成。真实四视图尚未绑定/精确计数；48次长历史的token/时间与现场最坏成本均Pending。任何输入超窗/超包，直接保留失败并停，不裁剪、压缩、换模型、换题或补请求。必须用执行状态、独立审计及完整回传三个门，而不是仅task_summary的score或completed。

CPU≤2、worker1、串行生成；cgroup合计24GiB。driver/helper硬AS各2GiB；driver树2GiB、service树16GiB和GPU16GiB是用户已接受的≤0.5秒采样停止阈值，**不是子树/GPU硬隔离，不保证瞬时无过冲**。服务进程不继承driver2GiB AS；监测中断/间隔超界fence。进程生命周期计数与HTTP/计数器是不同账项，均不可重置。读盘SHA、quota查询、渲染/序列化纳入墙钟/CPU与原始日志，不另称免费通信。

HDD任务原件≤1GiB（ledger/artifact999MiB、两个服务日志各8MiB、余量9MiB）；SSD新增≤32MiB仅小摘要/索引/状态。运行前SSD个人余≥64MiB、HDD≥2GiB；保留SSD32MiB/HDD1GiB停止余量。IPC请求规范化JSON单包≤65536B、episode累计≤524288B，终端result≤8388608B；RPC外包≤1MiB、HTTP响应≤512KiB、helper返回≤768KiB。原始模型内容≤65536B，规范文本≤4096B，超界原件保留、不得截断修复；episode原始历史不免费压缩。artifact写入先reserve，失败不继续下个episode。

## 真实执行准入

| 条件 | 本轮判定 | 获批前须满足 |
|---|---|---|
| 独立task授权/plan/ledger/loader/六阶段接线 | 新路径无模型通过 | 仅新task schema；旧probe授权永远不可授权任务 |
| 8×6人造合同、独立审计、完整回传 | 25新合同/独立审计/回传通过 | 所有新增T01–T16有真实证据，失败保留 |
| 历史probe/旧冻结源码保护 | 13份冻结材料SHA一致 | 不改变旧身份/限制/结果 |
| 实际四私有视图HDD bundle及SHA | **Pending** | 从原曝光家族合法离线导出，strict schema，不含gold；每对匹配历史view SHA，不加载原生300记录在线 |
| 8初始真实输入精确计数/大小 | **Pending** | 独立用户授权的新阶段开始后最多8次无生成helper；失败即停，不能因此补生成 |
| 本轮剩余52 records/D1 | 保持封存 | 不读/不选/不改registry/不拆分量 |
| 新run ID、baseline PID/stamp、完整source LF SHA及授权SHA | **Pending** | 现场重核，不预填旧run；approved:false模板阻断 |
| 现场quota、GPU空闲、退出/rollback、完整任务审计/回传 | **Pending** | 新阶段必须实际核验；本轮模拟不能替代 |
| T4/正式测试/训练及科学No-Go修改 | **No-Go** | 本申请不包含 |

决定：静态预算可供审阅，但**真实任务开跑Blocked**，不是无条件48请求准入。可提交一次有条件、最多48次的开发诊断预算申请；在bundle、真实输入支持域、source/现场身份与独立执行授权具体化前不得调用。若输入或资源支持域不成立，维持Blocked，不通过扩大模型/窗口、放宽D1或改指标解决。

[RUN] 本轮结束quota：SSD个人余79466496B，HDD余517703073792B；仅支持当时阈值，未来运行前须重核。25/25新无模型合同及独立审计通过，原件全部回传；真实输入/运行Pending不因这些结果消失。
