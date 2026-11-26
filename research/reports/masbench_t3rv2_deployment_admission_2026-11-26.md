# Research Task Report — T3-R-v2真实部署准入补齐

2026-11-26 Asia/Shanghai。**现场准入发现硬阻断，真实部署仍Blocked，尚未完成；有界T3能力诊断申请不释放。** 已完成独立只读现场核查、源路径审查、补齐合同和具体资源修复/真实预检候选；没有用静态文档代替真实验收。

## 科研问题、行为与结果

- **Research Question / Hypothesis**：[HYPOTHESIS] v2公平终答是否具备安全真实部署所需身份、资源、独立入口和可计价执行条件；不验证任务能力。
- **已核验前人工作**：AGENTS/总说明书/README/最近v2-I日志、四份v2审查文档、HPC同步工作流和旧T1/T2/T3执行路径。本轮未新增[PAPER]结论/文献检索。
- **实际阅读源码**：[CODE] 当前base458a96f及未提交v2-I源，见下方表。原T3仍b05ea73+20261125T034132Z，不重写历史来源。
- **本轮新增或修改**：[部署准入合同](../protocols/masbench_t3rv2_deployment_admission_v1_2026-11-26.md)、[具体阻断修复申请](../protocols/masbench_t3rv2_deployment_remediation_request_2026-11-26.md)、[纯合成真实预检候选](../protocols/masbench_t3rv2_deployment_probe_candidate_2026-11-26.json)、人工字面输入资产、现场快照、矩阵及任务日志。**生产代码无修改，也没有声称新增live adapter已经实现。** task brief原拟代码/测试在quota关卡后延期，不触碰前序未提交成果。
- **实际运行**：[RUN/管理] SSH只读id/host/HEAD/.venv、个人Lustre quota、cgroup权限、服务白名单环境/PID/二进制与清单/helper SHA、GPU读数、3次GET。GitHub ls-remote与本地/HPC均458a96f。没有同步/测试/服务切换/生成；没有任何新hpc_runs执行。原始快照见[任务目录](../logs/masbench-t3rv2-deployment-2026-11-26/README.md)。
- **测试与结果**：本轮新测试**未运行**；HPC quota不足使冻结16MiB无模型预算无法预留，按启动关卡停止。前序54+67/独立审计只在其历史支持域成立。只读行政快照不是工程测试通过记录。
- **失败/负面证据**：SSD余6.29MiB；服务仍1024；无子树/16GiB GPU硬限证据；v2实际只接fake，旧live worker仅接受旧授权。查询旧Ollama安装归档路径不存在，未迁移不存在的文件；随后只定位3个实际存在的诊断wheel缓存并核SHA，没有扫描/清理其他项目。
- **与原GOSC的差异**：无算法/调度/信道/训练改动，仅部署准入审查；未撤销T3/G1/GP-ID科学No-Go。
- **公平性与泄露检查**：原四题/剩余52条正文/gold未读取或选取；registry只沿用既有SHA，不解析；新候选完全人工blue parcel，不用旧正确答案优化Prompt；字面System SHA保持。全部48份前序交付文件SHA一致。
- **成本**：真实生成0、helper调用0、render/unload/start/stop0；只有GET3。主只读collector0.367944s，SSH/Git/其他SHA管理开销未仪器化；不是注册command累计性能。GPU当前0MiB读数，不是峰值；推理tokens/物理无线实验均无。未来156/596HTTP及2000/20360s全部未批准候选。
- **可否进入下一阶段**：现场身份部分通过；独立live入口/无模型接入/硬资源/真实部署**Blocked/Pending**。T3能力诊断、内容价值、无线净收益未建立；T4不放行。
- **用户需要批准的下一步**：明确是否允许将3个已冻结SHA的下载缓存原样迁往HDD，以恢复无模型接入空间；选择继续严格硬隔离还是另批监测停止合同。此批准仍不包含真实生成。待接入验收通过再签发两次纯合成真实部署预检申请，部署通过后才申请48任务生成。

## 源码审查与完整缺口

| 文件/函数与行范围 | 已确认事实 | 本轮处理 |
|---|---|---|
| `fair_final_v2.py:37–55,133–170,173–266`，system_prompt/public_clock/Agent/run_episode | 字面SHA、局部历史与六机会；173–185仅FixtureDriver | 字节不改；新live入口不能删门绕过 |
| `fair_final_v2_guard.py:86–125,188–216,278–287,290–423`，FairLedger/resource_guard/FixtureDriver | fake身份、分类计数；资源只观察；假服务cleanup | 不能直接作为真实HTTP/资源证明 |
| `live_driver.py:75–128,350–362,377–410,457–505`，authorization/runtime_files/RPC/worker | 旧授权白名单、固定身份、旧RPC入口 | 必须新独立schema/worker接入，旧文件不动 |
| 同上`639–742,744–895`，recover/attest/generate | 旧退出/render/usage安全语义可参考 | 只复用经审接口，不套旧授权/旧账本上限 |
| `client.py:187–298`，ControlledClient.generate | 冻结全输入、精确token与usage比较、无重试 | 新live允许后仍须完整绑定，不凭model名放行 |
| `scripts/hpc_ollama.py:25–89`，api/settings/ready/start | start有Driver外GET/60s循环 | 新持久生命周期计数必须覆盖，禁沿用漏账start |
| `experiments_ext/masbench_t2_live.py:39–106`，service/assert_idle/stop_idle/start_checked | 原空闲/身份/安全切换 | 仅参考，不实际调用stop/start |
| `experiments_ext/masbench_t3_live.py:24–69,79–179`，quota/HDD/profile/limits | 旧34800s/98请求/T3专用路径 | 不复用旧数或授权来承载新版 |

逐项事实、待验与释放条件见[准入矩阵](../logs/masbench-t3rv2-deployment-2026-11-26/admission_matrix.md)。配额/硬隔离不是用增大模型或换题解决的问题。当前2CPU硬限已存在，不将无cgroup写权误称完全没有CPU/RAM保护；缺的是新预算要求的单独子树及GPU保证。

## 资源与分阶段总账

当前SSD个人余6594560B，低于无模型16MiB工作cap；保留32MiB准入余量（16工作+16故障），真实预检另需64MiB（32+32）。HDD有足够剩余并不解除SSD管理元数据写入问题。3个wheel及manifest共35074439B，迁移申请完整保留HDD字节/读回SHA/回滚位置；只解锁首个无模型阶段，不承诺随后64MiB门一定满足。

真实预检候选为2个人工请求、16384/512、helper AS2GiB，每次准备150/生成180/清理40；总2000s/156HTTP，HDD128MiB、SSD32MiB、全量回传160MiB。新live入口和合同未完成，因此`approved:false`，source/receipt/现场PID绑定仍Pending，不提供可直接开跑命令。

后续任务阶段最多旧四家族×Full/No共8episode、48生成，另0合成；共享生成总50/输入793600/输出25600永久预留。若两阶段各自服务切换+回滚，生命周期GET必须由128增加到256，整体HTTP596，墙钟20360s而非原468/19100。此新增成本是分阶段安全验收代价，必须另批；不能通过重置run计数隐藏。两阶段间的人为审批等待不算计算性能，也不能延长已启动的parent deadline；若等待导致其失效，只能停止，不自动重建父账本。

**因此该两阶段方案目前还存在授权/时钟协调缺口**：真实预检2000s成功后若需人工审阅，剩余18360s不足以覆盖任意等待。建议预检与未来能力诊断采用独立单次授权、保留跨阶段累计计数，同时任务阶段deadline在其获批启动时另记；这是待审的显式时钟修订，不能声称不可重置的原19100/20360连续墙钟已解决。用户没有批准前仍保持原严格停止规则。

## 最终判断与反证

1. 任一quota、身份、输入/usage、IPC、清理/回滚或完整回传不明，部署不通过；不以环境有模型/历史T2成功替代。
2. 监测停止如获批，仍只支持观察合同；不能变成硬资源证明。采样间过冲与服务不可取消风险须保留。
3. 原四家族已曝光、未来能力筛查不作显著性检验；回答率提高、E自述或字面重合不能冒充L2/内容价值。未来配对F1/失败分母及原门不改。

**新版实现通过 ≠ 无模型合同通过 ≠ 真实部署通过 ≠ 科研能力成立。** 前两项仅v2-I既有支持域Go；本轮部署Blocked。没有进入T4、没有提交推送，静态准备完成后停止等待必要工程处理决定。
