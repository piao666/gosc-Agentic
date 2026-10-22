# GOSC HPC 最小复现协议（2026-10-19）

## 范围与来源

[CODE] 工作 HEAD `876fc523b113b3b65e19f0b730f1573ccc2ee17f`，上游基线标签 `upstream-gosc-387b493`。原算法、原实验脚本、原测试、原结果与缓存保持不变。未提交源码/文档通过每次 run 的 source_snapshot、source_changes.patch、source_untracked.tar.gz 固化。

本协议覆盖用户已授权的 HPC 环境准备、R1、R2、R3。实际完成状态以 `research/sync/runs/` 为准，不能用本协议代替运行证据。P1 全阶段仍包括多 seed、校准、cached/live LLM 与论文逐表图核对，本轮不覆盖这些完整关卡。

## 地点、环境与资源

所有计算在 `ssh hpc` 的 `/home/u202520081000097/jupyterlab/Paper/gosc`。UID 8301880、主机 n1，当前容器 2 核 CPU、24 GiB RAM；线程上限 2。仅使用 CPU，不要求 GPU、不下载模型、不调用付费 API。

基于已有 uv CPython 3.11.15 新建项目 `.venv`，仅解析/安装二进制依赖。`requirements-linux.lock.txt` 保存固定版本及哈希，freeze 和 environment.json 保存实际安装结果；运行前确认项目解释器路径与依赖一致。Windows lock 仅作为历史记录，不用作 Linux 成绩。

## R1：原测试收集与回归

在 HPC 用 `.venv/bin/python -m pytest --collect-only -q tests -p no:cacheprovider` 收集实际数量，再运行完整 tests。测试不修改、不跳过或删减。JUnit 写入当前 run 的 outputs/pytest.xml；临时目录为 run/pytest-tmp，日志为 outputs/pytest.stdout.log 与 stderr.log。原测试的假传输 LLM 客户端测试不代表 live LLM。

通过标准：退出 0，JUnit failures=0、errors=0，并明确报告 collected/总数/skipped；对预期之外的跳过解释。测试进程上限 600s。

## R2：已保存结果重分析与重绘

只复制 gosc、experiments、results 到 `.local/reproduction-workspaces/<run-id>/`，调用复制的原始模块，不修改模块实现。仅在该副本解压 noise/overhead/shared JSONL；原压缩包、原 results/summary 和缓存不写入。

按顺序执行 `python -m experiments.plot`、`python -m experiments.plot_revision`、`python -m experiments.plot_realistic`，随后在同一隔离副本执行 `python -m experiments.run_belief_divergence --table` 补齐 TableVI 的5个belief-divergence单元。此补表不运行新仿真；2026-10-19 的原R2三模块与后续补表分别保存在独立run。生成的 figures 与三个 summary JSON 复制到当前 run 的 outputs。保存输入 SHA-256；禁止把重分析称作重新仿真或 live LLM。

执行验收：三个模块退出 0；未出现跳过分支；预期汇总、PDF 与 TeX 文件存在。数值核对优先使用当前 results/summary.json，另两个已删除的 summary 使用 `git show upstream-gosc-387b493:results/<name>` 只读获取参考。数值比较相对/绝对容差 1e-10；JSON 结构/非数值项须一致。PDF 字节差异不能直接解释为实验数值差异。统计公式与 seed 配对沿用原脚本，不在此轮重定义。

边界：执行完与原 summary 数值匹配不等于原论文 PDF 每张图/表已逐项审阅。论文定位、版式、caption、公式与 CI 口径核对仍需独立交付。

## R3：单 mission 新执行

预先固定 `scheme=gosc`、`seed=3000`、默认 `Config()`，调用原 `run_episode(..., record_traj=True)`。保存完整 config、curve、trajectory、victims 与所有返回指标为 outputs/mission.json，另留 stdout/stderr 与命令记录。该 seed 属于作者既有 fresh-validation 划分，不能宣称是未见过的新 seed；本轮是重新执行单条仿真，未读取缓存替代运行。

验收：命令退出 0；曲线长度等于 max_steps；0<completion_time<=max_steps；found 与资源数值有效；任务完成/未完成、false_declarations 均按实际结果报告。超时 180s。N=1，不估计 CI，不比较方法优劣，不调参或训练。

## 每阶段的证据与保护

必须使用 `scripts/hpc_runs.py launch/run`，保存命令、解释器、Git/sync、资源限额、开始结束、退出码、日志与 outputs 的 SHA-256。每阶段对 gosc/experiments/tests/results/LICENSE 做前后完整性核验。失败与中断保留；停止依赖该失败关卡的下一阶段，先诊断原因。

任务状态与文件镜像状态分别记录：status.json 与 receipts/*.json。HPC 为事实源；本地仅编辑、传输、哈希与阅读。源码上传排除运行数据；拉回结果不删除 HPC 文件。默认新增下载上限 100 MiB，超限必须明确标记，不能声称同步完整。

## 后续关卡

本轮后优先完成 P0 论文—代码—图表映射与 R2 逐图核对，再设计 R4 成本匹配 paired seeds 与独立校准/评估。完整 campaign、模型下载、live LLM 或 M0/M1 训练不由本协议自动触发。

## 纸码/图表审计后的补充

完整定位见 research/logs/GOSC_paper_code_map.md；405单元格与表VI补全证据、37/38候选族差异、Fig2显示问题见 figure_table_audit_2026-10-19.md。后续多seed协议为 research/protocols/r4_protocol_v1.md，状态未执行。Genie为理想通信参考，不是任务最优上界。
