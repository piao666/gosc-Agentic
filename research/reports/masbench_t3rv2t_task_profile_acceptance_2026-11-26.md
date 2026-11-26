# Research Task Report — T3-R-v2-T

2026-11-26 Asia/Shanghai。**任务Profile新增路径与无模型合同：Go；真实任务执行：Blocked，尚非48请求开跑授权。** 最多48次的条件式开发诊断预算和未批准模板已形成，停止待研究决策审阅。

- **Research Question / Hypothesis**：独立task Profile能否在不改变probe限制、历史默认行为和科学阈值的条件下，实现原四曝光家族8×6任务计划、私有视图、逐slot计量及独立工程门？不评价真实能力。[HYPOTHESIS] 48次真实任务的完整输入/现场资源支持域尚待核实。
- **已核验前人工作**：本轮未新增外部[PAPER]检索或论文结论；复用已审MASBench适配及T3-R-v2协议。实际完整审阅AGENTS、研究说明、rounds_review、live_acceptance、bounded_diagnosis_request和相关源码。原始T3与两probe只作既有[RUN]成本/失败依据。
- **实际阅读源码**：[CODE] base c0621a1ab2cc249bbb6acb3b81cf1cec14591bcd；Agent/parser、ControlledClient、FairLedger/Ledger、wire、LiveDriver、RPC/helper、Monitor/Deployment及ServiceSpawner。函数/行范围见[实现与冻结核查](masbench_t3rv2t_implementation_review_2026-11-26.md)。本轮源码未提交，真实run以manifest/source_snapshot/未提交源归档为准。
- **本轮新增或修改**：独立task模块、campaign、launcher、task plan/approved:false授权、25项新无模型测试、登记wrapper、独立audit、定向collector、预算准入矩阵及任务日志；共享v2_runtime只加task精确类型/异常/计量分支。没有改旧base/protocol默认、旧评分、Prompt、核心client/wire或probe授权。
- **实际运行**：[RUN] n1/uid8301880，Python3.11.15，cgroup2CPU/24GiB；3次新增合同+1次独立审计，全程人工PrivateView、固定响应/FakeRPC或已有sandbox。模型/实际Ollama HTTP/helper/服务切换/真实题目读取均0；seed/model/cache不适用。精确命令见[commands.md](../logs/masbench-t3rv2t-2026-11-26/commands.md)。
- **测试与结果**：[RUN] 首轮23通过1失败，r2为24通过，最终r3为**25/25**、T01–T16均覆盖；不是73项独立测试。完整8×6人工路径与FakeRPC真实适配器路径均完成，独立stdlib核验两类48请求hash链、隔离/来源、清理、计量和13份旧冻结材料。测试不是随机科研样本，CI不适用。原件见下表。
- **失败/负面证据**：首轮task cleanup事件未识别，导致首episode停止和失败journal重复seq99；全部原件保留。修复仅限新TaskLedger解释复用事件，旧Ledger未改。原probe长输入invalid_exchange、原2000秒连续交付超期仍成立。启动Git bundle首次引用错误及结束cgroup v2路径不存在均如实保留为管理失败，随后使用实际HEAD引用/cgroup v1核验。
- **与原 GOSC 的差异**：只新增MASBench公平双本地终答任务Profile，不新增调度/估值/训练算法；无线净收益未测试。
- **公平性与泄露检查**：每条件4家族/24机会，角色时钟/Prompt/模型/输出预算固定；Full按原始来源传递合法MESSAGE，No-A2A保留双final；不互传final，不免费纠错/去重/累计板，不跨episode缓存。空/null/非法E/占位/弃答均沿冻结parser；已启动失败保留双方分母，未启动条件NA，不能以评分可算代替全部计划、slot和基础设施完整。D1/registry未改，剩余52记录未读/未选/未解封；本轮也未读四题正文/gold，fixtures全人工。
- **成本**：[RUN] 3次合同登记总33.998555秒<240秒，独立审计登记0.383877秒<120秒；每次均<120秒，AS256MiB、worker1；最大runner child RSS40716KiB（含Git，不是模型独占峰值）。HDD人工常规原件合计5416073B；四run及HDD镜像完整回传1683文件/11818187B<32MiB。结束SSD个人余79466496B（75.79MiB），HDD余517703073792B；profile不存在、锁0字节、GPU0MiB。新HTTP0、模型tokens0、真实任务wire0；人工wire账目不可当无线测量。
- **可否进入下一阶段**：新task新增路径/无模型合同Go；最多48次预算**Conditional Go仅供审阅**，真实执行Blocked。实际四视图bundle/SHA及8初始计数未取得；每slot动态输入必须即时计数，48次支持域未证明；当前服务PID/stamp/现场配额、真实任务独立审计/回传流程及完整deadline仍待新阶段核验。真实部署只沿两probe已测范围，不能称完整任务已部署通过。
- **用户需要批准的下一步**：审阅[最终预算与准入矩阵](../protocols/masbench_t3rv2t_final_budget_admission_2026-11-26.md)、[一次性条件申请](../protocols/masbench_t3rv2t_execution_request_2026-11-26.md)与[未批准模板](../protocols/masbench_t3rv2t_authorization_2026-11-26.json)。在全部前置具体化和用户单独批准前不启动真实任务。没有Git提交/推送；保持T3/G1/GP-ID科学No-Go，禁止T4/正式测试/训练。

## 新执行证据与回传

| run ID（均位于research/sync/runs/） | 状态与登记墙钟 | 证据 |
|---|---|---|
| hpc-t3rv2i-task-contract-20261126 | failed，7.276632s | [首轮原始输出](../sync/runs/hpc-t3rv2i-task-contract-20261126/stdout.log)，[原始清理失败账本](../sync/runs/hpc-t3rv2i-task-contract-20261126/outputs/hdd_raw/pytest-tmp/test_T11_task_real_adapter_all0/hdd/fixture/budget/ledger.jsonl) |
| hpc-t3rv2i-task-contract-r2-20261126 | completed，11.545622s，24通过 | [r2回执](../sync/runs/hpc-t3rv2i-task-contract-r2-20261126/outputs/contract.json) |
| hpc-t3rv2i-task-contract-r3-20261126 | completed，15.176301s，25通过 | [最终合同](../sync/runs/hpc-t3rv2i-task-contract-r3-20261126/outputs/contract.json)，[逐项矩阵](../logs/masbench-t3rv2t-2026-11-26/acceptance_matrix.md) |
| hpc-t3rv2i-task-audit-20261126 | completed，0.383877s | [独立审计](../sync/runs/hpc-t3rv2i-task-audit-20261126/outputs/audit.json) |

最终r3 Git=c062（dirty）、source snapshot=20261126T074815Z，manifest SHA `d0f3d14dbe76606c143933bdbd20eba3c2ee210538376610fe4c8a4e0ebb878d`。新增未提交源码由source归档及逐件LF SHA绑定，不拿c062本身冒充新实现已在Git中；旧HPC dirty状态如实登记，不擅自清理。

双端完整receipt：`20261126-t3rv2t-fca11334f6.json`（首轮412文件/3002294B）、`20261126-t3rv2t-925e22a879.json`（r2+r3共1262文件/7854786B）、`20261126-t3rv2t-39cfb51354.json`（审计9文件/961107B）。常规原件、tar和source快照全回传；仅pytest便利symlink未作为常规证据，HDD原件仍保留。执行完成与完整回传分开核验；没有把首轮失败改为completed。

## 冻结科研解释

保留完整四家族配对、Full至少两个家族双方EM1、家族平均DeltaF1≥0.10、至少两个家族正差且对应两条件双方有效、真实L1与独立可追踪L2。E声明不是L2；不能提高回答率就宣称证据整合、消息内容价值或无线资源收益。已曝光四家族只作开发筛查，两个Agent、turn和请求不增加独立N，不作显著性/稳定因果/独立确认性结论。

**新版实现通过 ≠ 无模型合同通过 ≠ 完整真实部署通过 ≠ 科研能力成立。静态方案值得实施 ≠ 真实任务能力成立 ≠ 消息内容价值成立 ≠ 无线资源净收益成立。**
