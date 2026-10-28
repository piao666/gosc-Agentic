# GP-ID-v1：信息使用、获取服务与阈值机制的识别协议

> 执行更新2026-10-27：[343合同、52短成本fixture及独立审计已完成](../reports/information_identifiability_acceptance_2026-10-27.md)，详见[执行状态](information_identifiability_execution_2026-10-27.json)。UL/DL速率1/2由原默认值显式写出；旧失败保留，最终冻结源码身份见HPC prepare。以下10月26日“未运行/连接失败”与示例runID均为制定时快照，不是当前状态。无新收益校准、正式test或训练授权。

日期2026-10-26；代码基线253a14b。当前为**实现完成待HPC合同验收**，不是已冻结独立校准或已证实收益。机器入口为[information_identifiability_v1.json](information_identifiability_v1.json)。学校VPN/HPC不可达，用户明确要求先完成实现，故本轮不执行科研计算。

## 问题与可识别范围

[HYPOTHESIS] 在保留原Planner、任务候选、lagrangian_select、事件索引CRN和GP-v2服务规则的前提下，付费接收端时间戳/位置能否超出只用已收到native EVID时间戳的简单阈值规则，并抵消信息获取成本？已有GP-v1/GP-v2负结果不撤销。

[CODE] 原age是同决策全部价值乘f=1/(1+mean_age)，理想目标等价p_eff=p/f。数值选择器有二分与破同分，不能声称所有有限精度轨迹逐位相等。native-price、paid-price用于诊断实现与阈值机制，不事后替换主方法。

## 对照矩阵

| Arm | 购买摘要 | 时间戳规则 | 位置投影 | 目的 |
|---|---|---|---|---|
| public-fixed | 否 | 无缩放 | 无 | 本地ToM参照 |
| native-age / native-price | 否 | 仅本地已收到native | 无 | 简单阈值是否足够；缩放/调价数值比较 |
| paid-ignore | 是 | 无缩放 | 无 | 购买服务而忽略其内容 |
| paid-native-age | 是 | 仍仅本地native | 无 | 隔离购买服务与购买时间戳的使用 |
| paid-age / paid-price | 是 | 有效且更新的已收到摘要，否则native | 无 | 时间戳内容使用的增量 |
| paid-pose | 是 | 无缩放 | 有效已收到位置 | 固定price下的位置增量 |
| paid-pose-native-age | 是 | 仅native | 有效已收到位置 | 相同native调价规则下的位置增量 |
| paid-pose-age | 是 | 有效摘要，否则native | 有效已收到位置 | 相同paid时间戳规则下的位置增量 |

同格式bits、AoI和periodic k8/eps0另作简单参照；price只用既有1e-4工作点，**不代表成本已匹配或重新选参**。未来主比较必须重新论证有限强baseline集合与实际通信/CPU成本支持，不能仅凭同price/W比较。

关键差分：paid-age − paid-native-age识别共同购买规则下的时间戳使用策略差异；paid-pose-age − paid-age识别共同时间戳规则下的位置使用策略差异；paid-native-age − native-age帮助审查服务代价。整个闭环的动作、消息和后续接收历史会内生变化，所以这些不是单条消息的受控直接因果效应，也不能相加成独立成本因果分解。

## 观测合同

- 估值输入仅本observer实际已收到的native ledger/summary cache。native-only规则不读取paid cache。位置投影只作用于估值副本，age在投影前原本地view计算，避免投影本身破坏native/摘要匹配判断。
- 每decision记native/selected created、received/TTL、来源、age/factor、base/effective price、本地/估值位置、cache拒绝原因、age之前的实际候选和selected signature。候选已含位置投影（若启用），不是额外计算出的public影子候选；periodic没有完整GOSC目录，明确记null。
- 每DL frame记唯一frame_id、kind、bytes、required uses、enqueue t和每次实际served uses；末尾记未服务/在途，不虚构mission后的服务。UL每实际尝试记真实bytes/rate/uses/成败，丢失仍收费。
- CPU admission/completion记job_id、observer、kind、ready、预留秒/排队时间；成功到达、CRC解码处理、cache可见资格分开。wire hash仅用于观测关联，重复相同字节可能复用hash，不能当唯一投递ID。DL服务用frame_id，CPU用job_id。
- 观察器不调用随机数、不插入CPU/无线工作、不读取未来reward；这是研究日志，物理/逻辑模型不计日志工作量，实际process/wall会包含它。开/关运行需报告开销，不称部署实测效率。
- observations输出按decision/channel/service分组，**不是文件行顺序的全局事件时间线**。按t、frame_id/job_id和边界解释。
- probe在仿真结束后，对每个实际记录的pre-age候选目录重新执行scale与price两种形式；原形式必须重现实际选择，两种形式的差异如实保留。该数值诊断不产生新任务分支、标签或效果N；单独记录后处理耗时，不混入mission时间。

## 合同与有界成本probe

全部只能在HPC经hpc_runs登记；本地未运行。tests_ext覆盖观察开/关全科学字段与指定私有状态/RNG计数、四个旧arm的GP-v2短fixture等价、权限/时间戳/TTL、投影前age、字节服务/CPU账本、右截断、选择器有限目录及独立审计拒绝篡改。合同中的旧/新fixture只证明该支持范围，不能称全历史等价。

合同上限240s；prepare60s；probe120s；独立审计60s；单worker/数值线程1，无GPU/LLM/训练。prepare必须读取通过的登记run/JUnit与源码快照，任一失败/跳过/源码SHA不同阻断。原始冻结GP-v2文件不改。

探测种子候选27000000–27000001，仅在HPC核对可发现登记目录、旧保护范围和world指纹后才能冻结；碰撞直接阻断，不静默换seed。合同fixture26000000单列。13方案×2world×观察开关=最多52个24slot短fixture，**独立任务收益N=0**，不利用截断任务值选arm、计算功效或宣称任务优势。固定先off再on，开销不是随机化benchmark。

脚本只有prepare/probe模式，没有calibrate/test/train。独立stdlib审计重算DL分类及censor、UL、CPU/收到/解码守恒、时间戳/factor/候选成员/预算和观察开关结果一致；它不证明选择器全局最优、完整信息因果效应或正式任务收益。

## 后续门槛与停止

1. HPC不可达：只交付实现与文档，明确测试/prepare/probe/审计全部未运行。
2. 合同、源码SHA、observer、registry或账本任一失败：保留失败run，修复后新runID；不推进任务收益实验。
3. 合同/probe/audit通过后：另立前瞻独立校准设计与预算；已有两批12world已曝光，原预留test封存不动。任务效应、成本支持、比较族、N/功效/硬预算在执行前固定；不得依该probe选择效果最好方案。
4. 若native对照解释全部优势，收缩购买摘要的必要性主张；若同服务/同调价下位置仍无增量，不进入复杂估值训练。小样本不显著不等于证明等价；判断无价值需另定有功效的等价/最小效应标准。
5. 降成本服务仅形成可审阅候选；延后编码、合并、捎带、ACK处理优化均需额外合同与真实计费，不能从账本删费推断相同任务收益。Work2/3与训练不启动。

## 恢复HPC后的命令模板（本轮未执行）

先核验ssh身份/目录/Python/配额/无running任务，明确核对远端HEAD与origin。若远端HEAD仍为旧版本，先保留其工作区并核验祖先与源码清单，不用reset/checkout覆盖；同步器遇差异会停止。使用现有经审核的单向SHA同步流程，确认本次manifest。

```powershell
python scripts/hpc_runs.py launch --run-id hpc-information-contract-20261026 --kind test --stage information_identifiability_contract --purpose passive_observation_and_information_permissions --seed 26000000 --config research/protocols/information_identifiability_v1.json -- env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout 240 '{python}' -m pytest -q tests tests_ext -p no:cacheprovider --basetemp '{run_dir}/pytest-tmp' --junitxml '{output_dir}/pytest.xml'
python scripts/hpc_runs.py launch --run-id hpc-information-prepare-20261026 --kind infrastructure --stage information_probe_prepare --purpose contract_SHA_and_world_registry_gate --config research/protocols/information_identifiability_v1.json -- env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout 60 '{python}' scripts/repro_information_identifiability.py --mode prepare --contracts-run research/sync/runs/hpc-information-contract-20261026
python scripts/hpc_runs.py launch --run-id hpc-information-probe-20261026 --kind simulation --stage information_cost_fixture --purpose observation_and_typed_service_cost_only --seed 27000000 --seed 27000001 --config research/protocols/information_identifiability_v1.json -- env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout 120 '{python}' scripts/repro_information_identifiability.py --mode probe --frozen research/sync/runs/hpc-information-prepare-20261026/outputs/frozen.json
python scripts/hpc_runs.py launch --run-id hpc-information-audit-20261026 --kind analysis --stage information_independent_audit --purpose independent_typed_resource_and_decision_check --config research/protocols/information_identifiability_v1.json -- env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout 60 '{python}' scripts/audit_information_identifiability.py --results research/sync/runs/hpc-information-probe-20261026/outputs/results.json
```

每个命令必须以前一个实际成功为前提，不批量越过失败/超时。未来日期执行使用新的真实runID，不回填2026-10-26运行事实。launch自动回传，另核对receipt是否all_outputs_mirrored；未完整下载的产物不称交付完成。
