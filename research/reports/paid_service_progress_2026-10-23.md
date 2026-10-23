# Research Task Report — 付费字节服务链与效果设计关卡

- **Research Question / Hypothesis**：[HYPOTHESIS] 当task/summary竞争UL、ACK/广播竞争DL且CPU处理占时间时，摘要能否只在实际解码后进入估值cache？本轮检验服务合同，不检验任务改善。
- **已核验前人工作**：[PAPER] 沿用D01 p5 Eq4与D08 p6/p16既有笔记；没有新增文献查新或新颖性主张。原GOSC已含公共广播、ToM与部分控制计费；本服务是显式实现对照。
- **实际阅读源码**：[CODE] base4ff4147654c07781d77a42acee3f31c0b8792f38；gosc/messages.py的bit公式/Packet、simulator/realistic两条估值与广播路径（沿用上一轮映射）；receiver_pose_interface、receiver_rtt_contract、receiver_transport_replay。原核心未改。
- **本轮新增或修改**：新增extensions/paid_receiver_service.py、tests_ext/test_paid_receiver_service.py、paid_service_contract_v1.json、paid_service_effect_design_v1.md、任务brief及本报告；RTTLane新增offer_ready以接收CPU处理完成但仍保留原生成时间的帧。既有offer仍要求当slot生成。更新研究入口/状态；保留此前未提交成果。
- **实际运行**：[RUN] HPC n1、UID8301880、Python3.11.15，quota200000/100000=2CPU，RAM25769803776bytes。两个登记test run：hpc-paid-service-contract-20261023失败，hpc-paid-service-contract-v2-20261023成功。均单数值线程、timeout300，无LLM/GPU/训练/任务收益campaign。
- **测试与结果**：[RUN] 初版126pass/1fail；修复后**128passed in33.42s**（85原测试+26 pose/RTT+17服务测试）。新集合替代首次，不相加；上一轮129包含18个旧codec测试，本轮以17个服务测试替换，不能说原129少过一项。覆盖真实CRC长度、UL残余、DL零容量/分slot服务、广播接收者丢失、单CPU排队、created/TTL、task ACK、期末截断和独立累计账本。无新效应值或CI。
- **失败/负面证据**：[RUN] 初版零DL场景下导出cost未初始化dl_uses，导致KeyError；没有偷偷放宽断言，补全零值字段并新增逐事件重算UL/DL账本测试。失败run与源码快照保留。未恢复原作者校准/cache链或历史差异。
- **与原 GOSC 的差异**：[CODE] 服务接受显式bytes任务输入并统一CRC16，summary沿用原审计codec，非原GOSC完整wire实现。未更改Planner、原候选/调度或公共belief。端到端原生任务适配尚未接通，不把合成字节合同当成GOSC净任务效果。
- **公平性与泄露检查**：UL task优先，summary使用剩余同预算；DL task ACK→summary ACK→task广播→summary快照的固定优先级/FIFO，逐帧收费、逐receiver丢失。task逐slot重试与summary RTT重试规则不同，明确记录并需跨arm固定。CPU编码/解码共享各Agent单队列；slot/处理时长是显式场景参数，非硬件实测。service.next_t有限，finish不补虚构尾部。没有新world采样、标签或训练。
- **成本**：[RUN] 初版run wall35.401516s，v2 wall33.894144s；v2 runner child CPU user33.585106/system0.259727s、maxRSS58108KiB。管理开销包含在runner口径，非独占算法性能。0新LLM/付费API/下载/训练；助手tokens、GPU峰值和能耗未测。不是实际RF测量。
- **可否进入下一阶段**：**Go：有限字节服务链合同；Pending：原生task编码/options/投递适配、部署时钟、cost-matched前沿、新world与功效设计；No-Go：直接任务收益campaign/复杂训练。** 本轮没有声称完整原生闭环已完成。
- **用户需要批准的下一步**：当前授权已推进至可审阅服务内核与HPC验收。下一实施对象是native task适配及相同格式下的候选/预算重建；效果计算仍须形成精确新world清单、N/功效和预算后决定。无需提供API Key；未Git提交/推送。

## 服务实现与剩余边界

[CODE] 数据流：本地提交→CPU编码完成→task优先UL/summary RTT→edge解码→付费ACK/广播共享DL→至少下一slot到达→逐receiver CPU解码→PoseKnowledge cache。任务payload同样经服务后输出task_received；原Simulation如何消费此payload尚未适配。value_view可读取此cache，未替代原Planner。

[CODE] DL帧服务可跨slot扣容量，但属于分段codeword账本，没有真实分片MAC头/重组协议；dl_offered_bytes、dl_completed_bytes和实际dl_uses分列，不能把尚未发完字节当完整空口包。低优先级可能饥饿，finish保留pending DL/CPU/task/summary与inflight，不能省略不利场景。

[HYPOTHESIS] [效果设计](../protocols/paid_service_effect_design_v1.md)明确M0star/public-ToM/paid-ignore/paid-pose/age/shuffle，pose本身就是直接位置刷新，不重复设置同实现别名。新world需查重，N需独立calibration方差与功效；当前未把旧20world或合成服务输入当新独立N。数据划分原则和停止规则已写，**最终数值manifest未冻结**。

## 运行命令与证据

完整argv与source SHA以manifest为准；实际命令结构为：

```text
python scripts/sync_hpc.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-paid-service-contract[-v2]-20261023 --kind test --stage paid-service-contract --config research/protocols/paid_service_contract_v1.json -- env [数值线程=1] timeout 300 {python} -m pytest -q tests tests_ext/test_receiver_pose_interface.py tests_ext/test_receiver_rtt_contract.py tests_ext/test_paid_receiver_service.py -p no:cacheprovider --basetemp {run_dir}/pytest-tmp --junitxml {output_dir}/pytest.xml
python scripts/hpc_runs.py pull --max-bytes 104857600
```

- [失败记录](../sync/runs/hpc-paid-service-contract-20261023/status.json)、[失败日志](../sync/runs/hpc-paid-service-contract-20261023/stdout.log)。
- [成功manifest](../sync/runs/hpc-paid-service-contract-v2-20261023/manifest.json)、[成功stdout](../sync/runs/hpc-paid-service-contract-v2-20261023/stdout.log)、[JUnit](../sync/runs/hpc-paid-service-contract-v2-20261023/outputs/pytest.xml)。
- [事前合同协议](../protocols/paid_service_contract_v1.json)、[任务brief](../logs/paid-service-2026-10-23/task_brief.md)。

源码同步20261023T061505Z（417文件/0哈希差），修复同步20261023T061854Z（418文件/0哈希差）。最终回传及文档同步单列delivery.json，不将执行完成冒称两端已同步。源码保护检查git diff --name-only -- gosc experiments tests results LICENSE无变化；历史结果未重写。本地只编辑、Git、文件/哈希管理和同步，没有本地pytest/仿真。
