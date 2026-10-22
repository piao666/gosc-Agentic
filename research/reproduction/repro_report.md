# Research Task Report — HPC environment and R1–R3 (2026-10-19)

- **Research Question / Hypothesis**: 原 GOSC 能否在用户指定 HPC 的 Python 3.11 隔离环境通过完整测试、重建作者数据图表，并执行固定 seed 的单任务？不验证新方法优越性。
- **已核验前人工作**: [CODE] HEAD 876fc523b113b3b65e19f0b730f1573ccc2ee17f；上游整合基线 upstream-gosc-387b493。作者原始结果/缓存用于 R2，非本课题新仿真数据。
- **实际阅读源码**: AGENTS、README、总说明书、requirements、三份 experiments/plot*.py 的输入/输出与 bootstrap、validate_realistic/run_realistic、gosc/simulator/config 与 tests 的文件写入行为。
- **本轮新增或修改**: scripts/hpc_reproduce.py（HPC-only 有界环境/R1/R2/R3 入口）；hpc_runs.py 的 pytest-tmp 回传排除；Linux lock/freeze、repro_protocol、研究日志、进度与环境配置。保持原算法/实验/测试/结果不变。
- **实际运行**: [RUN] 四个独立 run：hpc-env-20261019、hpc-r1-20261019、hpc-r2-20261019、hpc-r3-20261019，全部在 n1。每次真实 argv、解释器、cwd、sync/commit、日志、输出哈希见 runs/<id>/。

## 实测结果

| 阶段 | 结果 | 证据（research/sync/runs/ 下） |
|---|---|---|
| Environment | CPython 3.11.15 项目 .venv，15 依赖包；uv pip check 与导入通过；numpy 2.4.6、matplotlib 3.11.2、pytest 9.1.1 | hpc-env-20261019/outputs/environment.json、requirements-linux.lock.txt、commands.json |
| R1 | 85 collected，85 passed，0 failures/errors/skips；pytest 33.64s，登记总用时 35.36s | hpc-r1-20261019/outputs/test_summary.json、pytest.xml、pytest.stdout.log |
| R2 | 三个原绘图模块退出 0、无跳过；17 PDF + 18 TeX；三个 summary 数值均与基线在 1e-10 内一致；总用时 280.17s，修订脚本 267.25s | hpc-r2-20261019/outputs/replot_summary.json、figures/、summaries/、commands.json |
| R3 | 默认 Config、GOSC、seed 3000、非 LLM planner；completed=true，113 slots，8/8 found，false=0；uplink symbols=19051，bits=19623；dl_symbols=5560（原模拟器口径）；仿真主体 1.04s | hpc-r3-20261019/outputs/mission.json、single-mission.stdout.log |

[RUN] 环境包解析、venv 创建、带哈希同步、依赖检查均在 HPC，未改变系统 Python。Linux 精确依赖已复制至 research/reproduction/requirements-linux.lock.txt 与 freeze 文件。运行记录保留原始输出与源码变更归档；Windows 仅编辑、Git、传输和哈希核验。

## 命令与可复现性

本地统一发起：`python scripts/hpc_runs.py launch --run-id <id> --kind <kind> --stage <stage> --purpose <purpose> -- '{python}' scripts/hpc_reproduce.py <environment|r1|r2|r3>`，R3 同时记录 `--seed 3000`。真实完整命令保存在各 manifest.json 和 outputs/commands.json；不以示例代替实际 argv。

R1 在 HPC 执行 `.venv/bin/python -m pytest --collect-only -q tests -p no:cacheprovider` 及完整 pytest（JUnit 与临时目录隔离）。R2 在独立 `.local/reproduction-workspaces/hpc-r2-20261019` 执行三个原模块，不修改模块内容；只在副本解压数据。summary_revision/realistic 参考值从上游 Git object 只读获取，未恢复/覆盖用户删除的原目录文件。

## 失败、保护与科学边界

- **失败/负面证据**: R1 测试成功，但首次自动回传被 pytest 临时目录的符号链接保护检查阻断。已将明确的一次性 pytest-tmp 排除，正式 outputs/状态/日志仍拒绝符号链接；重试回传通过，未重跑或修改测试。详细见 issues.md。HPC 登录 .bashrc 的历史目录警告仍存在，与本次计算成功无关。
- **完整性**: 每阶段 input_integrity.json 保存 gosc/experiments/tests/results/LICENSE 的全部文件前后 SHA-256，unchanged=true；原结果和 LLM cache 未写入，未删改失败记录。
- **公平性与泄露检查**: R2 是作者保存数据重分析，不是 fresh 全 campaign，也不是 live LLM 或 cache replay。R3 seed 3000 来自作者既有验证划分，单次重新执行，未训练、调参、挑 seed，N=1 不提供 CI 或方法优劣结论。
- **成本**: CPU线程<=2，24 GiB配额；未使用模型/GPU任务或付费 API。环境登记约8.99s、R1约35.36s、R2约280.17s、R3约1.54s（不含同步）；runner 子进程最大 RSS 对应 R2 454104 KiB，包含管理子进程，不解释为独占算法性能；GPU 峰值未测量/null。
- **剩余不确定性**: R2 对历史 summary 数值一致，但尚未对原论文 PDF 逐表/图/caption 做最终人工审阅；完整 paper-code-map、成本匹配 R4、多 seed CI、独立校准、R5 cached/live LLM 和 R6 全图表验收尚未完成。P1 整体仍为部分完成，P3–P5 未启动。
- **可否进入下一阶段**: 当前授权的 HPC 环境/R1/R2计算/R3 已完成。下一步先补 P0 纸码映射与论文图表核对，再固定 R4 成本/seed/校准协议。现有证据不足以启动新方法训练或宣称研究创新有效。
- **用户需要批准的下一步**: 本轮已授权工作全部完成，无待批准交付。完整 campaign、live 模型与新方法属于后续任务范围，不自动启动。

## 两端同步

每阶段均已拉回状态、stdout/stderr、全部正式 outputs 和产物哈希，并将 receipt 回写 HPC。最终镜像完成情况以最新 receipts/*.json 与最终只读 verification.json 为准；执行成功与传输成功分别记录。

## 后续纸码与图表审计更新（2026-10-19）

[RUN] 已完成本地D01 v1全编号映射：5式/5图/13表/Algorithm1。HPC审计9数值表405单元，原8表一致，表VI5格通过原table-only helper补齐后一致；25默认字段与6冻结点一致。37/38候选口径、图2minor标签显示差异、Genie定义与bootstrap次数均在审计报告显式记录。当前P0纸码映射已具备；R4协议已定但未执行，P1整体与P2关卡未完成。见 research/logs/GOSC_paper_code_map.md、research/reproduction/figure_table_audit_2026-10-19.md、research/protocols/r4_protocol_v1.md。

## 后续R4-A0实际执行更新（2026-10-19）

[RUN] 两场景×三方案×10seeds（9000–9009）共60条真实mission已完成，9项执行器测试及独立原始记录审计通过；首次0mission导入失败保留。主运行墙钟20.11s，最大并发2、每worker线程1。Search时间均值GOSC70.2/periodic75.4slots；Rescue saved均值98.75%/85.00%，periodic未达到原冻结目标。仅N10 pilot，不升级为正式优势或完整P1验收。完整证据、失败修复与成本外推边界见research/reproduction/r4_a0_report_2026-10-19.md；A1/B/C和训练未启动。


## 四场景成本探测完成（2026-10-19）

[RUN] search-K10、search-clustered、rescue-W50、rescue-snr-5各GOSC/冻结periodic、seeds9010–9012共24条完成，17项测试/独立审计通过。六场景1200条A1预计575.8s，建议硬上限1860s、单条120s、并发2，每worker线程1；预算为小样本外推，不含可选Genie/B/C/LLM/训练。下一计算地点为HPC；完整A1待范围确认后准备执行器，未自动启动。报告：research/reproduction/r4_cost_probe_report_2026-10-19.md；预算：research/protocols/r4_a1_budget_proposal_2026-10-19.json。P1整体仍未验收。


## 完整R4-A1执行更新（2026-10-19）

[RUN] 已执行六场景两方案seeds3000–3099共1200条、600配对；28项测试及独立统计/数据审计通过。登记墙钟574.586676s，0程序失败/超时/中断。1200条主指标/上行symbols逐seed与作者保存值一致；不宣称全部轨迹历史比对或新方法贡献。periodic Search-W100/K10均值略未达冻结目标；所有search时间差CI及rescue-snr-5获救差CI跨0，负结果保留。报告research/reproduction/r4_a1_report_2026-10-19.md，实际状态research/protocols/r4_a1_execution_2026-10-19.json。B/C、独立校准与R5LLM/P2关卡仍待推进，完整P1未验收，未启动训练。
