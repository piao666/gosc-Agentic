# Research Task Report — 交付包、最小位置估值接口与HPC验收

- **Research Question / Hypothesis**：[HYPOTHESIS] 能否只给原估值器提供已送达、有效且比本地EVID更新的pose，并保持原Planner、候选消息与调度规则？本轮验证软件合同，不验证任务收益。
- **已核验前人工作**：[PAPER] 沿用D01 p5 Eq4、D08 p6/p16的原有阅读证据。位置刷新属于已有机制的简单对照；三bit桶不等于空间belief。未新检索论文、训练或宣称新颖性。
- **实际阅读源码**：[CODE] 起点4ff4147654c07781d77a42acee3f31c0b8792f38；gosc/voi.py的TeamModel、_points、_belief_mass；schemes.py的build_groups/evidence_voi/transmit；realistic.py的平行build_groups/apply、shared central/price与result；simulator.py的deliver/snapshot/downlink/decide。原gosc/experiments/tests/results/LICENSE保持不变。
- **本轮新增或修改**：新增extensions/receiver_pose_interface.py、receiver_rtt_contract.py，两份tests_ext测试、scripts/repro_pose_contract_audit.py、冻结合同测试JSON、47份交付副本及manifest/说明、本报告/任务日志；更新导航和当前状态。不改旧协议、历史失败或原输出。
- **实际运行**：[RUN] HPC登记hpc-pose-contract-tests-20261023（测试）与hpc-pose-delivery-audit-20261023（stdlib文件/JUnit交叉审计）。实际完整argv、seed、Python、dirty/source SHA、配额与退出码见各manifest/status。命令类别及同步证据见下文。执行主机n1，UID8301880，Python3.11.15，2CPU/24GiB；数值线程1，0GPU任务。
- **测试与结果**：[RUN] **129 passed in34.00s**，包括85原生测试、26新增接口/RTT合同、18既有codec/传输合同。不是129次LLM调用或任务样本；原生LLM测试仍为fake transport。本轮无新真实LLM调用。独立入口审计核验JUnit、77保护文件、5实现/测试/协议文件与47份交付副本SHA，全部通过。没有任务效应CI；效果实验**未运行**。
- **失败/负面证据**：首次本地SSH被sandbox网络限制拒绝，经工具权限批准后连通；第一次读取cgroup v2路径不存在，改读v1后核验实际2CPU/24GiB。首次以裸SHA创建bundle被Git拒绝空bundle，改用既有分支ref成功。这些均发生在正式科学运行前；两个登记run均退出0。未来付费任务系统未集成，测试通过不能替代收益证明。
- **与原 GOSC 的差异**：估值专用位置视图、每接收者本地EVID时间ledger和RTT lane均在独立扩展。继承原两条build_groups，以投影视图调用原逻辑，无全局TeamModel monkeypatch。不开oracle，不读peer私有pending/当前pose；无cache时回退原值；不改Planner、公共belief、候选内容/bit/率规则。实验标识pose_cache_tom_contract独立于GOSC。
- **公平性与泄露检查**：仅使用已成功解码帧；同slot摘要不可回流，过期/乱序/冲突/更旧摘要回退；native时间来自实际接收snapshot，不能偷用edge新状态。固定mission命名空间，未实现跨session协议。三bit桶被忽略仍须按旧帧付费。测试seed15000000–15000002仅为合成/最多3slot的fixture，不能当独立任务N，也不进入后续calibration/test。共享UL、rescue、LLM模式拒绝接入；本轮验证默认exact值/H0接口，未证明全部非默认配置或paid闭环公平性。
- **成本**：[RUN] 测试登记wall34.837434s、runner子进程CPU user34.223326s/system0.529393s、child_max_rss62260KiB；审计wall0.198714s、CPU user0.118131s/system0.122635s、RSS36656KiB。runner资源含管理子进程，不是容器独占峰值；未测GPU峰值/能耗或助手tokens。0新LLM/付费API/模型下载/训练。两次pull新增下载分别1,843,040和1,834,972bytes；源码同步/32,355,400byte Git bundle成本另计，未测总链路流量。
- **可否进入下一阶段**：**Go：可提交交付包、默认配置最小接口/RTT合同与HPC回归；Pending：付费传输/预算/DL与CPU时钟集成、新world与功效设计；No-Go：直接效果campaign、M1/M2训练或部署收益主张。** 事件触发、快照合并与捎带仍未新增实现/回放；旧96条件不能当新RTT实验。
- **用户需要批准的下一步**：本轮授权的交付包→最小接口→有界HPC验收已完成。尚未Git提交/推送。效果实验须先具体实现完整成本/服务时序与强对照，再冻结新world、N/功效/统计族和预算，不能以合同通过跳过这些关卡；不重复全量复验或用新响应填作者cache。

## 1. R2/R3可提交成果包

[RUN] [成果包](../artifacts/r2-r3-20261019/README.md)包含47份原产物副本，1,330,880bytes：原R2 17PDF/18TeX、三个summary、命令/输入完整性、R3 mission/命令/日志与独立TableVI补件。manifest/README另计。每份SHA既比对原run/artifacts，又比对原输出和交付副本，原件不移动、不重绘。

原R2 table_values.tex的5格n/e保留，后续table-only补表单列supplements；不掩盖首次重绘的缺项。包内没有私人PDF、模型、LLM提示/响应、凭据。此包准备为普通非忽略文件，没有改.gitignore或git add -f；**未提交/未推送GitHub**。不能把复制入包当新仿真或新独立N。

## 2. 最小接口与RTT实现边界

[CODE] PoseKnowledge只接受CRC通过的单帧/快照，保留created/received/TTL，按observer分隔cache。value_view仅复制team_pos/team_intent给TeamModel，不暴露agents；位置时间ledger不匹配公共值时保守回退。PoseGOSC/PoseRealisticGOSC继承原候选构造，不引入自己的估值公式。

[CODE] PoseLedgerSimulation与PoseLedgerRealisticSimulation跟随原deliver及_downlink，记录接收者实际看到的EVID末record.t。较晚到达的旧record仍要跟随原公共位置回退时间，不能用max时间误标。测试覆盖有损/延迟快照与短轨迹一致性。

[CODE] RTTLane将latest pending与inflight attempt分开；supersede不重置timer，旧ACK不删新代，timeout后才重试，ACK丢失不能免费成功。每attempt按完整CRC帧长和rate取ceil且不超过residual。它是单sender状态机合同，不是新96条件传输回放，也未自动计入整个系统task/DL/CPU时钟。

[HYPOTHESIS] 真正paid系统仍需要把成功UL→edge→实际DL队列→每发送者cache连成统一服务链，并给所有原task帧相同H/CRC语义、同UL/DL容量/等待规则。当前enable_pose_values仅是显式测试hook，没有免费自动摘要服务，也不能把fixture手工收到的帧当部署协议。

## 3. HPC版本核对与同步

[RUN] HPC初始HEAD为876fc52，本地为已归档后继4ff4147。先核验祖先关系、核心基线差异为0、无running登记任务；备份远端HEAD/index后，仅git read-tree（无-u）/update-ref/symbolic-ref对齐归档元数据。前后1055个目标tracked路径的工作文件哈希完全不变；未reset/checkout/clean/merge，未覆盖远端文件。证据：[元数据核对回执](../logs/minimal-interface-2026-10-23/hpc_archive_reconcile.stdout.json)。这不把旧run的commit倒填为新值。

[RUN] 正常scripts/sync_hpc.py首次同步409文件、72变更，sync20261023T020638Z，0哈希差；测试manifest SHA d6352340abd004e68959635a8c735a499ee0d78747b82b6e95af303113e9e243。审计入口后续同步410文件、1变更，sync20261023T021029Z，0哈希差。远端独有文件保留，run/receipt不随源码上行。

## 4. 实际命令与证据

本地仅文件复制/哈希/Git/SSH/同步管理；所有pytest及文件结果审计都在HPC登记：

```text
python scripts/sync_hpc.py
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-pose-contract-tests-20261023 --kind test ... -- env [四个数值线程变量=1] timeout 300 {python} -m pytest -q tests tests_ext/test_receiver_pose_interface.py tests_ext/test_receiver_rtt_contract.py tests_ext/test_receiver_summary_audit.py tests_ext/test_receiver_transport_replay.py ...
python scripts/hpc_runs.py pull --max-bytes 104857600
ssh hpc <project-python> scripts/hpc_runs.py run --run-id hpc-pose-delivery-audit-20261023 --kind analysis ... -- env [数值线程=1] timeout 60 {python} scripts/repro_pose_contract_audit.py --output {output_dir}
python scripts/hpc_runs.py pull --max-bytes 104857600
```

上列为可读缩写，精确展开命令以manifest为准：

- [测试manifest](../sync/runs/hpc-pose-contract-tests-20261023/manifest.json)、[测试stdout](../sync/runs/hpc-pose-contract-tests-20261023/stdout.log)、[JUnit](../sync/runs/hpc-pose-contract-tests-20261023/outputs/pytest.xml)。
- [审计manifest](../sync/runs/hpc-pose-delivery-audit-20261023/manifest.json)、[完整交叉审计](../sync/runs/hpc-pose-delivery-audit-20261023/outputs/pose_delivery_integrity_audit.json)。
- 回传：[首次回执](../sync/receipts/20261023T020835Z-79c06a.json)、[审计回执](../sync/receipts/20261023T021132Z-361dfd.json)，均all_outputs_mirrored=true。原run输出仍遵守忽略规则，交付包白名单副本单列。
- [冻结合同协议](../protocols/receiver_pose_contract_tests_v1.json)、[任务说明](../logs/minimal-interface-2026-10-23/task_brief.md)。

最终文档同步与本地轻量diff/JSON检查另存本任务delivery.json；执行完成与文档同步完成分别记录，不用旧回执冒充新文档已上行。
