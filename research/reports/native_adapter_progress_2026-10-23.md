# Research Task Report — 原生任务语义wire与付费闭环适配

- **Research Question / Hypothesis**：[HYPOTHESIS] 保留原CONF/INTENT/EVID语义与Planner，能否将实际wire帧长度用于候选prefix/率/预算，并通过付费服务后只更新实际接收者？本轮检验闭环软件适配，不检验收益。
- **已核验前人工作**：[PAPER] 沿用D01 p5 Eq4及D08 p6/p16笔记。GOSC已实现估值和选择，本轮复用其TeamModel/价值接口与lagrangian_select；不宣称新调度器、新编码思想或方法有效。
- **实际阅读源码**：[CODE] base4ff4147654c07781d77a42acee3f31c0b8792f38；gosc/messages.py bit公式/Packet、schemes.py Group/Option/build_groups/lagrangian_select、simulator.py phase_decide/communicate/deliver/declare/result、realistic.py平行options/prefix/apply。新wire统一替代两条旧抽象bit口径的适配候选；只支持exact/H0、正交UL、Planner search，不冒称所有realistic/shared/rescue模式兼容。
- **本轮新增或修改**：新增extensions/native_task_wire.py、native_paid_adapter.py，tests_ext/test_native_paid_adapter.py，scripts/repro_native_adapter_trace.py，两份事前合同/trace JSON及本报告。扩展paid_receiver_service支持task逐包选定rate、多选batch与付费历史task重播；默认task_window=1行为保留。原gosc/experiments/tests/results/LICENSE未修改。
- **实际运行**：[RUN] HPC登记hpc-native-adapter-contract-20261023与hpc-native-adapter-trace-20261023。主机n1、UID8301880、Python3.11.15，2CPU/24GiB、单数值线程；测试timeout300、trace timeout60。完整argv/config/source SHA/环境见manifest。未本地pytest/仿真。
- **测试与结果**：[RUN] **145passed in33.72s**：85原生+26 pose/RTT+17服务+17原生适配合同。新增覆盖无损语义往返、截断/CRC/未知namespace、实际帧长/prefix、task单包rate、本地幂等融合、edge不可免费清peer状态、零DL与短闭环。trace另保留同一seed16000002的三个4slot重复fixture：finite_dl_bits、zero_dl_bits、finite_dl_tom，原始结果/资源事件/哈希均已保存。不作为3个独立world或任务收益样本，不给效应CI。
- **失败/负面证据**：本轮两个登记run退出0；此前字节服务初版失败继续保留。任务wire变长，stop-and-wait批次节奏和历史重播会改变通信/等待；不能把新结果与作者旧wire/预算直接合并。未解决原校准/cache生成链或历史差异。
- **与原 GOSC 的差异**：GP-v1是显式时间/位置/检测记录的自描述无损语义序列化，**不是作者bit公式的逐bit实现**。只支持CONF/INTENT/EVID，拒绝FIFO片段/RAW/SEM/NL。原Packet.bits并非语义，decode后按新payload计数，outer实际10byte（type/length/source/id/CRC16）用于选包。保留原rates、TeamModel/原AoI接口和调度函数，bits基线按新payload goodput赋值；需重新独立校准价格。不能继续标为原版GOSC。
- **公平性与泄露检查**：edge仅decode成功wire；ACK只清发送队列，pending_llr等自收广播后才减；每receiver按(source,id)去重。局部belief/declared/位置/意图及EVID时间ledger仅由收到的task消息更新，不读edge最新值；pose只进入估值副本。global world真值只沿原生感知/任务评分使用，不参与估值。补发task历史逐帧付费，保证丢失后可补投但可能拥塞；不称最优同步。短测试world已曝光，16000000–16000002须排除后续calibration/test。
- **成本**：[RUN] 测试run wall34.196541s，runner child CPU user33.934074/system0.202548s、RSS58184KiB；trace wall0.379255s、CPU user0.324998/system0.098758s、RSS37148KiB，非独占系统峰值。0新LLM/付费API/下载/训练；未测助手tokens/能耗/GPU峰值。trace使用slot1秒、CPU0秒、price0的显式合同假设，不作部署时钟估计。
- **可否进入下一阶段**：**Go：支持范围内的原生语义→wire候选→付费服务→edge/局部接收→下一次Planner的短闭环合同。Pending：强周期基线、事件索引CRN、真实成本场景/前沿与独立校准功效。No-Go：未经这些关卡启动收益campaign或复杂训练。** 非物理层/MAC部署验收。
- **用户需要批准的下一步**：本轮授权适配与有界验证已完成；未Git提交/推送。下一步先补相同wire服务下的强简单baseline（特别periodic）与配对噪声协议，然后预算化成本/独立校准；新world/N/效应预算未冻结，不以短合同结果拍定样本或宣称提升。

## 实现约束与时序

[CODE] WireGOSC不是对已选原包事后加开销：先encode每个原待发prefix，按完整服务帧字节重新算可装长度和ceil channel uses，再以实际n重新求成功概率。CONF/INTENT也走同一规则；不以旧成功概率乘一个开销比例冒充新链路。

[CODE] NativePaidSimulation复用原phase_decide，使用每接收者独立公共视图；planning先于本slot服务完成，刚接收数据最早下一planning决策可见。batch未ACK前不重复入队，仍会逐次付费重传。每个已成功task frame按固定refresh补发历史，实际开销计入DL，重复交付不重复融合；低优先级可能积压，截止保留pending/inflight。任务广播与summary共享同一服务容量/CPU队列。

[CODE] 运行结果删除继承的未维护symbols/bits/dl_symbols/delivered_bits零计数，实际资源只从service账本读。global完成条件按edge的原任务语义判定，局部Planner不能使用global declared；edge确认不会免费清掉未收到消息的agent.confirmed_pending。

[HYPOTHESIS] 本轮明确了传输模型，未证明它最优或具备发表贡献。默认支持范围之外的模型被拒绝；FBL额外物理字段/真正fragmentation、可变CPU/硬件测量、共享上行、LLM与rescue迁移需另验收。periodic尚未接入同wire选择器，不能说已具备最强M0全套公平比较。

## 证据和命令

- [合同协议](../protocols/native_adapter_contract_v1.json)、[trace协议](../protocols/native_adapter_trace_v1.json)、[任务brief](../logs/native-adapter-2026-10-23/task_brief.md)。
- [测试manifest](../sync/runs/hpc-native-adapter-contract-20261023/manifest.json)、[测试stdout](../sync/runs/hpc-native-adapter-contract-20261023/stdout.log)、[JUnit](../sync/runs/hpc-native-adapter-contract-20261023/outputs/pytest.xml)。
- [短trace索引](../sync/runs/hpc-native-adapter-trace-20261023/outputs/index.json)，同目录三个JSON含result/events/cache计数；不是收益曲线或功效数据。
- [测试回传](../sync/receipts/20261023T063434Z-686ba4.json)、[trace回传](../sync/receipts/20261023T063704Z-c51c41.json)，均all_outputs_mirrored=true。

```text
python scripts/sync_hpc.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-native-adapter-contract-20261023 --kind test ... -- env [数值线程=1] timeout 300 {python} -m pytest -q tests tests_ext/test_receiver_pose_interface.py tests_ext/test_receiver_rtt_contract.py tests_ext/test_paid_receiver_service.py tests_ext/test_native_paid_adapter.py ...
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-native-adapter-trace-20261023 --kind simulation ... -- env [数值线程=1] timeout 60 {python} scripts/repro_native_adapter_trace.py --output {output_dir}
python scripts/hpc_runs.py pull --max-bytes 104857600
```

上列为可读缩写；精确命令以manifest为准。测试源码sync20261023T063218Z、trace源码sync20261023T063554Z，均0哈希差。最终文档同步另存delivery.json；执行状态与回传状态分别判定。
