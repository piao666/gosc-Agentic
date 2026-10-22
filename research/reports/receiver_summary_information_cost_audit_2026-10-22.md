# Research Task Report — 摘要增量信息与同步成本（2026-10-22）

## Research Question / Hypothesis

[HYPOTHESIS] 接收端摘要是否增加既有公共信息之外的可用信息，且能在完整获取/分发/重传/等待成本下值得使用？本轮只核查字段、软件编码与条件通信可达性，不训练估值器，不测试新方法任务收益。

[RUN] 核查完成：最终23项测试、4对原策略/被动观测完整轨迹一致检查、4条补充payload观测与全部先前观测字段一致检查、96组通信回放和独立算术/覆盖审计通过。**复杂训练仍No-Go；旧32bit摘要不能直接作为已验证的可部署receiver估值输入。** 有限协议可以明确实现与计费，不等于已证明任务净收益。

## 已核验前人成果与实际源码

[PAPER] 延续已读GOSC/ToM2C/PragComm/BANDMAS/iCoTASC的机制边界，不重新宣称receiver-aware、反事实或轻量估值思想首次。页码与来源沿用 literature/reading_notes/、Research-Gap-Matrix-2026-10-22.md；本轮未重新读全部论文或检索新SOTA。

[CODE] HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f，原gosc核心在HPC按旧冻结SHA逐文件核对不变。字段和时序锚点：

| 路径 | 具体事实 | 对摘要成本的影响 |
|---|---|---|
| gosc/messages.py:8,64–65；Packet | 原应用头8bit，INTENT默认18bit；Packet.created是Python元数据，原intent计数未独立列时间字段 | 新格式要说明时间来自帧还是额外元数据；不能只数“32bit payload” |
| gosc/simulator.py:107–115,130–145 | view维护本地收到的common；EVID更新team_pos、INTENT更新team_intent | 最新值可能尚未通报，但字段/机制已有；需区分新语义与刷新 |
| gosc/schemes.py:407–494 | 各Agent本地build_groups/TeamModel再选择与发射 | 摘要只到edge不足；其他发送端也要成功收到才可用 |
| gosc/voi.py:44–58,86–95 | oracle输入完整pending LLR、确认集与位置；public路径用公共belief/位置 | 三bit聚合桶不能直接代替完整空间belief，更不能靠打开tom_oracle读取真值 |
| gosc/realistic.py:403–480 | central/price两模式仍先从Agent视图构建选项；再汇总请求/分配预算 | 不存在只在edge加一个免费cache即可复用原估值的接口 |
| gosc/simulator.py:214–284,167–194 | decide→UL→edge融合→DL；丢失/延迟下本地view落后且有catch-up | 同slot新摘要不能反过来影响该slot先前的决策；快照需扩展到摘要cache |
| gosc/realistic.py:505–521 | 计UL额外头、请求、DL广播、ACK/grants | 现有1bit ACK是模型假设，非独立反馈帧完整序列化 |
| gosc/config.py:36–41,74–87 | DL rate2、ACK1、request/grant/price等口径 | 需要分开bytes、UL/DL channel uses与绝对物理时延 |

## 逐字段增量信息判断

| 候选字段 | 是否增加信息 | 权限/代价及判断 |
|---|---|---|
| target10bit | 可能刷新尚未送达的当前意图，机制已有 | 不能叫完全冗余；已有更短INTENT候选，应与直接刷新INTENT对照，而不是把它包装成新语义字段 |
| current pose10bit | EVID已报告位置，独立pose主要提供更及时位置 | 需要实际送达和时间戳；只能更新估值专用cache，不能顺手改变Planner公共位置后把收益归因估值 |
| uncertainty3bit | 旧草案未定义语义；当前audit改为私有证据差异桶 | 只从本地已收到common+自己的pending计算TV；**不是正确率、校准置信度或任务效用** |
| state-version8bit | 可用于去重/协议状态 | 不是新增任务知识；在本轮同mission、单时隙一代摘要条件下用创建slot标识可避免独立version字段 |
| slot-modulo8bit | 元数据必要，但400slot mission内会回绕 | 本审计用9bit不回绕时间，严格拒绝超范围；跨mission/restart/时钟同步仍需另计 |
| valid/padding | 协议辅助位 | 必须计入实际编码；不提供任务内容 |
| 完整pending belief/确认集 | 与oracle增益相关的真实私有状态 | 当前聚合桶无法表达；禁止把它免费传入估值器冒充已压缩 |

[RUN] 使用原calibration seeds12000000/12000001、W100/W50的既有冻结public ToM点，共2274个“新感知之后、上传之前”的Agent-slot观测。此时所有行TV非零是正常时序现象；不证明这些差异都值得发送。四条观测的“target尚不等于已收到intent”分别365/474、426/594、445/534、550/672；pose不同于edge最后记录位置分别465、587、525、666。说明需要评估刷新价值，不能把已有字段当完全静态，也不能将新鲜值重新命名为新语义创新。两W复用同两个世界，slot/Agent行不是独立任务N。

[RUN] 测试构造了相同公共数组、不同private数组得到不同桶的例子，同时也构造不同空间private数组映射到同一桶的例子。前者只证明该函数可以增加不可由该公共输入决定的字段；后者证明它不是完整oracle状态的充分表示。不是互信息估计或闭环任务价值证明。

## 真实测到的软件字节与计算成本

[CODE/RUN] 独立审计命名空间的codec（未注册进GOSC Packet/策略）：
- novelty：应用头8+时间9+差异桶3+valid1+padding3=24bit，3byte；实际加CRC16后5byte。
- novelty+pose：应用头8+pose10+时间9+桶3+valid1+padding1=32bit，4byte；CRC后6byte。
- 旧32bit草案是payload32；若还需原应用头8及额外CRC16，应分层计费，不能称整帧32bit。旧冻结草案保留，未静默改写。
- 反馈独立帧：头/计数2byte+每项2byte(sender、发射slot、success)+CRC2byte；失败UL以正交lane识别sender和发射slot，不偷读无法解码的生成时间。
- 完整最新快照：头/计数2byte+嵌套应用帧+CRC2byte，摘要不重复加CRC。命名空间、session和同步是假设，不宣称可直接接入真实MAC。

[RUN] HPC四个首观测状态各重复1000次：TV特征提取p50分别15.524/15.673/15.834/15.953微秒；encode+CRC+decode+CRC p50分别4.777/4.757/4.767/4.817微秒。包括Python/NumPy实现，非LLM推理，也非设备独占能耗。没有物理slot持续时间，未把微秒虚构成任务slot等待。

[RUN] 以下是六Agent同时成功刷新、R_UL=1、R_DL=2、独立CRC反馈/快照帧的显式编码例子，非同slot任务收益：

| 格式 | 六Agent上行 | 显式反馈DL | 快照DL | 合计channel uses |
|---|---|---|---|---|
| novelty | 240 | 64 | 88 | 392 |
| novelty+pose | 288 | 64 | 112 | 464 |

首轮简化shadow示例323/395 channel uses使用1bit ACK等较简口径；本轮独立完整反馈/快照帧是不同协议，不能混为计算错误或覆盖旧输出。真实PHY前导/保护、调制器、跨mission与时钟同步并未测量；这是软件编码加条件无线账本，不是实测真实空口。

## 有界通信回放：已付费的可达性与陈旧度

[RUN] 输入仍是四条原H0任务轨迹，原策略/负载固定，2种应用帧×刷新1/5/10×DL erasure0/.1×额外DL delay0/2×四条轨迹=96条件；不是96独立世界。采用R_UL1、R_DL2、TTL20，规则事先写入独立protocol。它是在第一轮成本观测之后设计的探索诊断，不冒充预登记确认性方法实验。

任务优先，摘要每Agent每slot至多一次且只用原任务剩余grant；未获容量则排队。上行失败/ACK丢失会收费重传；新代摘要替换旧待发，旧ACK不能清掉新代；edge只存成功decoded数据；下行独立ACK/全最新快照逐帧付费，逐接收者丢失；cache只由成功收到的帧更新，TTL过期忽略。UL t发送的数据最早在t+1+delay使用。到原mission结束仍待发/在途的帧记右截断，不凭空续出信道。

**当前重传是朴素的逐slot立即重试，没有等待已知反馈RTT的定时器。** delay2时重复发送成本很明显；因此不能据本设计成本高就断言所有同步方案都不值得。RTT-aware timer、合并/捎带/事件触发是未测试的低成本对照，下一步应优先审查它们。

以下按固定展示条件“刷新5、DLloss.1、额外delay2”列全部四轨迹×两格式；全部96结果保留，未删有利/不利行。usable fraction是receiver–sender–slot对中未超过TTL的cache占比，不是摘要正确率或任务成功率。

| W/seed | 格式 | 生成/尝试/重传次数 | 新增总channel uses | 有效cache占比 | age中位/P95 | 预算不足等待slot数 |
|---|---|---|---|---|---|---|
| 100/12000000 | novelty | 96/315/230 | 21776 | 0.940 | 6.0/14.0 | 50 |
| 100/12000000 | novelty+pose | 96/315/230 | 25784 | 0.940 | 6.0/14.0 | 50 |
| 100/12000001 | novelty | 120/398/294 | 27928 | 0.969 | 6.0/14.0 | 75 |
| 100/12000001 | novelty+pose | 120/396/293 | 32992 | 0.969 | 6.0/14.0 | 77 |
| 50/12000000 | novelty | 108/353/268 | 24620 | 0.924 | 7.0/16.0 | 99 |
| 50/12000000 | novelty+pose | 108/345/265 | 28120 | 0.835 | 7.0/16.0 | 117 |
| 50/12000001 | novelty | 138/441/325 | 30080 | 0.973 | 6.0/14.0 | 98 |
| 50/12000001 | novelty+pose | 138/437/326 | 34952 | 0.902 | 6.0/13.0 | 110 |

[RUN] 全96条件的有效cache占比范围为 0.820–0.991；这只是条件可达性。独立审计逐case重算原始UL尝试/bytes/decoded/剩余容量、DL字节到symbols、总账、年龄/TTL与完整网格，全部通过。

## 成本覆盖和剩余限制

| 项目 | 当前覆盖 | 未证明的部分 |
|---|---|---|
| 应用内容/头/时间/CRC | 实际二进制长度与解码/损坏/有效期测试 | 非既有GOSC wire兼容/部署协议 |
| UL预算与重传 | 实际回放事件逐条付费，严格不超过原剩余grant | 原任务H0而摘要CRC16；不是全系统同开销的策略比较 |
| ACK/DL快照 | 真实序列化长度、反馈丢失、旧ACK隔离、完整最新快照 | 缺少RTT timer优化；不是原生catch-up同一协议 |
| DL可达性/年龄 | erasure/额外delay/TTL/右截断显式 | 不是实际射频BLER、时钟/跨mission实现 |
| shared UL requests/grants | 源码口径已映射 | 本回放只做正交剩余grant；共享调度的额外控制还需计入 |
| feature/codec计算 | HPC实测微秒与原始样本 | 没有把CPU等待注入task clock或量测功耗 |
| 任务净收益 | 未测试，cache不参与policy | 没有paid-summary cost-matched frontier、无摘要/shuffle/age任务消融 |
| 资料与历史复现 | 旧事实保留 | 原校准1000–1079、作者cache链、frontier/where历史差异未由本核查解决 |

## 本轮变更、命令、证据与关卡

[CODE] 仅新增extensions/{receiver_summary_audit,receiver_transport_replay}.py、scripts/repro_{summary_audit,summary_transport_audit}.py、tests_ext/{test_receiver_summary_audit,test_receiver_transport_replay}.py和两份预算/协议JSON，新增本报告与字段ledger；原core/结果/cache/旧协议不改，已有工作区修改保留。

[RUN] 真实入口完整参数在各manifest：
```text
hpc_runs.py run --run-id hpc-summary-cost-tests-20261022 ... -- timeout 300 {python} -m pytest ...
hpc_runs.py run --run-id hpc-summary-cost-audit-20261022 ... -- {python} scripts/repro_summary_audit.py
hpc_runs.py run --run-id hpc-summary-transport-tests-20261022 ... -- timeout 300 {python} -m pytest ...
hpc_runs.py run --run-id hpc-summary-transport-audit-20261022 ... -- {python} scripts/repro_summary_transport_audit.py
hpc_runs.py run --run-id hpc-summary-cost-final-audit-20261022 ... -- {python} -c [recorded independent audit]
```

最终23测试通过（包含先前16项，不相加充当39项独立测试）；首分析10.07s、通信回放7.58s、独立审计.44s。HPC n1/Python3.11.15/2CPU24GiB配额，数值线程1，分析串行；0新LLM调用/0训练/无依赖或模型下载。runner CPU/RSS口径含元数据，非容器独占性能。没有科学运行失败；自动审批超时均发生于执行前，后经用户明确批准和工具允许的重试完成，不伪装成运行失败/通过。

证据根 research/sync/runs/：hpc-summary-cost-audit-20261022/outputs/{observations.jsonl,observability_summary.json,guard_replays.json,codec_benchmark.json,cost_tables.json,shadow_cost.json}；hpc-summary-transport-audit-20261022/outputs/{payload_observations.jsonl,transport_events.jsonl,transport_replay.json,observation_guards.json,evidence.json}；hpc-summary-cost-final-audit-20261022/outputs/cost_integrity_audit.json。两测试run保留stdout/JUnit。同步完成另见本任务delivery.json。

**Go：字段审查、显式软件帧与条件传输链可以复核。Pending：摘要如何在不改变Planner/调度器/表示的条件下进入估值。No-Go：直接把旧32bit方案投入新方法全量实验或复杂训练。** 下一步应先完善RTT-aware重试/捎带的低成本协议对照及最简单的估值接口，另立固定成本/信息权限/世界划分的验证协议；不自动启动训练，也不把本轮reuse的calibration轨迹当全新test。
