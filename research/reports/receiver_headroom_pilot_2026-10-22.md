# 接收端状态改进空间诊断 — 2026-10-22

[RUN] 本轮有界探索试验及独立完整性/算术审计完成。6组主要比较均未达到预设任务收益门槛，复杂模型训练保持No-Go。小样本且privileged状态获取免费，不能把结果解释为“接收端状态无价值”或已证明某可部署方法有效。

## 问题与冻结设计

[HYPOTHESIS] 固定原GOSC search任务、Planner、候选消息、编码/调度和信道模型时，给原TeamModel增加receiver私有pending belief、真实位置或二者，是否能比独立校准的强简单基线更快完成任务且不增加总通信？这是特权信息诊断，不是数学任务最优上界或新模型训练。

[RUN] 人类协议 research/protocols/receiver_headroom_pilot_v1.md 与机器协议 research/sync/runs/hpc-receiver-protocol-20261022/outputs/protocol.json 在试验结果产生前冻结。protocol于03:55 UTC生成，pilot03:59 UTC启动。extension、runner、测试、协议和gosc全部模块SHA在结束及独立审计时一致；未修改原core/结果/缓存。

- calibration seeds：12000000–12000007；validation：13000000–13000019；guard：14000000–14000002；训练预留11000000–11000099未使用。
- 对已登记输入目录保守查seed整数并核对已有world fingerprint，无冲突；提前记录62个W/seed指纹。查重不涵盖从未登记的运行。
- W100/W50共用同20验证世界，不能算40个独立世界。
- 每条件78候选，含public ToM、bits、AoI、38个periodic及三privileged mask；156×8=1248校准。
- 每family在校准均值UL≤10000的候选中按平均T、UL、ID选点；M0star在bits/AoI/periodic中按校准选择。选点文件先于验证写入。
- 最终13个不同选点×20seed=260验证。未达到280上限是W50 AoI无合格校准点；M0star只是已有选点别名，未重复运行。不删test seed、不改网格。
- 5条校准mission在400步仍未达成任务，保留截断结果；验证260条均达成任务。执行正常退出不等于校准任务全部成功。
- 外生噪声按seed/时刻/Agent/全局cell索引。保留原世界初始化，但改变了随机过程耦合，不能当作者历史精确重放。记录世界与首时隙潜在感知场，未逐个保存全部后续事件dump。

[RUN] 校准均值UL上限不是逐mission硬预算，也不保证验证实际等成本。资源端点是base simulator的UL+DL；privileged信息获取免费，未把摘要传输、估值计算等待等加入任务时间，故不支持部署性净收益主张。

## 主要结果

[RUN] 每行N=20配对世界；6比较×任务/成本两个端点=12项Bonferroni族，单区间99.5833%，20000次paired bootstrap。正任务增益=M0starT−privilegedT；资源比=privileged/(M0star)，UL+DL。门槛：平均任务提升≥3slots且区间下界>0，同时资源比区间上界≤1.05。

| 条件 | 免费特权字段 | 简单基线 | T增益slots [校正区间] | UL+DL比 [校正区间] |
|---|---|---|---|---|
| search-W100 | private belief | m0_aoi | -21.05 [-52.87,6.83] | 0.212 [0.177,0.270] |
| search-W100 | pose | m0_aoi | -7.35 [-29.82,14.35] | 0.500 [0.390,0.637] |
| search-W100 | both | m0_aoi | -3.35 [-24.72,17.02] | 0.482 [0.384,0.616] |
| search-W50 | private belief | m0_periodic | 6.70 [-23.30,34.75] | 0.825 [0.639,1.080] |
| search-W50 | pose | m0_periodic | 14.25 [-25.02,45.78] | 1.102 [0.798,1.534] |
| search-W50 | both | m0_periodic | 15.25 [-4.50,39.68] | 0.435 [0.353,0.532] |

[RUN] 0/6通过。W100三组都更省通信但平均更慢，属于质量—成本取舍。W50完整mask平均快15.25slots，任务区间[-4.50,39.68]仍跨零；不能事后只挑资源端点宣布成功，也不能据此宣布信息无效/等价。完整group statistics保留public ToM及全部简单基线，不隐藏强对照。

[INFERENCE] 这不是完整cost-matched frontier，也未独立隔离同eta下新增信息的效应。有限付费摘要、同容量无摘要/shuffle/age消融均未实现。小N和保守区间下保持证据不足；不得看test后扩大样本/改变regime来救结果。

## 检查、资源与运行入口

[RUN] 5项HPC测试通过：拒读屏蔽字段、公共投影等于native公开值、全特权投影等于native oracle、不同视野重叠cell随机事件匹配、相同策略重复结果一致。独立审计从原始记录重算覆盖、选点/M0star、配对world/seed/首场、区间和判决，全部通过。

HPC n1，Python3.11.15，2CPU/24GiB配额；580.84s wall，runner子进程CPU user1144.47s/system0.83s。child_max_rss_kib=58868是runner口径，并非容器总峰值。未使用GPU训练、未新增LLM调用、未采集训练标签。

真实登记命令及完整参数见各manifest：

```text
hpc_runs.py run --run-id hpc-receiver-protocol-20261022 ... -- {python} scripts/repro_receiver_pilot.py --mode prepare
hpc_runs.py run --run-id hpc-receiver-tests-20261022 ... -- {python} -m pytest -q tests_ext/test_receiver_diagnostic.py -p no:cacheprovider ...
hpc_runs.py run --run-id hpc-receiver-headroom-pilot-20261022 ... -- {python} scripts/repro_receiver_pilot.py --mode pilot --protocol research/sync/runs/hpc-receiver-protocol-20261022/outputs/protocol.json
hpc_runs.py run --run-id hpc-receiver-independent-audit-20261022 ... -- {python} scripts/repro_receiver_audit.py
```

证据根 research/sync/runs/：hpc-receiver-protocol-20261022/outputs/{protocol,preflight}.json；hpc-receiver-tests-20261022/{stdout.log,outputs/pytest.xml}；hpc-receiver-headroom-pilot-20261022/outputs/{calibration,validation}.jsonl，以及frozen_operating_points.json、validation_group_statistics.json、paired_effects.json、conclusion.json；hpc-receiver-independent-audit-20261022/outputs/independent_audit.json。

## 当前关卡与后续边界

[RUN] 有界pilot和审计完成；复杂训练No-Go、部署收益Pending。P1历史逐seed/cache/原校准缺口独立保留。既没有依据重跑整个复验队列，也不应启动大模型。

[HYPOTHESIS] 若继续该方向，先另立可审阅的付费摘要最小协议：确认32bit候选字段哪些不重复已有intent；最强M0可以不购买摘要；摘要与原消息竞争无线预算，计headers/ACK/重传/陈旧/丢失/推理等待；比较同容量无摘要、age-only和shuffle。先独立校准成本及信息可用性，再冻结新世界、功效/停止条件。此后续试验和训练未自动启动。
