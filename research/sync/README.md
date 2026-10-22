# 本地与 HPC 的运行状态和输出同步

本地：`E:\gosc\research\sync`；HPC：`/home/u202520081000097/jupyterlab/Paper/gosc/research/sync`。

## 内容与权威来源

- `config.json`：已核验 Python 3.11 路径、端点、下载上限等配置；本地维护后上行。
- `environment/hpc_python.json`：Python/依赖实测快照，不能与测试通过混淆。
- `project_status.json`、`plans/next_steps.md`：研究阶段判断和本地/HPC 工作计划。
- `templates/`：未执行的模板，不计入运行次数。
- `runs/<run-id>/`：HPC 权威运行记录；manifest、source_snapshot、status、stdout/stderr、artifacts 索引、`outputs/` 实际输出。
- `dashboard.json`、`STATUS.md`：HPC 生成的汇总，包含失败和中断；只统计有实际记录的任务。
- `receipts/<sync-id>.json`：每次回传的逐文件哈希/完成情况，两端均保存。

运行记录额外保存 tracked 修改补丁和同步快照内的 untracked 源码归档，以便恢复未提交源码。资源记录中的 child CPU/RSS 包含 runner 的 Git 元数据子进程，不用作模型独占性能；未测 GPU 峰值保留 null。

每次项目测试、训练、仿真、分析必须通过 `scripts/hpc_runs.py` 登记。一次多 seed campaign 可以作为一条运行记录，但每个 seed 的原始结果必须保留并列入产物。手工绕过入口的命令不会被自动探测成已完成任务。

## 状态规则

`planned -> running -> completed / failed / interrupted`。仅退出码 0 标记 completed；失败/中断与 stdout/stderr 不删除。任务完成与本地输出同步完成分开：receipt 的 `all_outputs_mirrored` 为 false 时，不能说全部输出已下载。进程外异常断连可能留下 running，此时先检查远端进程并核实，不能擅自改成 completed。

## 使用方式（本地 PowerShell）

同步代码和本地维护的计划：

```powershell
cd E:\gosc
python scripts/sync_hpc.py
```

拉回 HPC 状态、日志和输出，并将回传 receipt 写回 HPC：

```powershell
python scripts/sync_hpc.py --pull-runs
```

默认每次新增下载上限 100 MiB；超过部分保留在 HPC，并在 receipt 标明 skipped_size_limit。所有运行产物都有远端哈希索引。需要完整大文件时显式扩大上限：

```powershell
python scripts/hpc_runs.py pull --max-bytes 1073741824
```

启动已授权的 HPC 任务，结束后自动回传（下例为通用 R1 命令模板；2026-10-19 的实际执行证据见 runs/hpc-r1-20261019）：

```powershell
python scripts/hpc_runs.py launch --kind test --stage R1 --purpose 'HPC upstream regression validation' -- '{python}' -m pytest -q tests -p no:cacheprovider --basetemp '{run_dir}/pytest-tmp' --junitxml '{output_dir}/pytest.xml'
```

launch 先同步源码，在 HPC 执行命令，成功或失败都尝试回传。HPC 直接启动时可用同一脚本的 `run` 子命令；结束后本地需执行 pull。`{python}`、`{run_dir}`、`{output_dir}` 会在 HPC 替换；也提供环境变量 `GOSC_RUN_DIR`/`GOSC_OUTPUT_DIR`。新的结果写入 outputs，禁止使用会覆盖上游 results/cache 的默认输出路径。

## 保护与边界

- 代码同步永不推送 `runs/`、`receipts/`、dashboard/STATUS 到 HPC，防止本地旧镜像覆盖运行记录；这些内容单独从 HPC 下行，receipt 单独写回。
- 有 running 任务时拒绝更新远端源码；先 pull 查看状态，待完成/核验中断后再同步。
- 回传时对旧本地文件备份，按 SHA-256 核验；不删除远端输出。持续变化的日志导致哈希变化时应稍后重拉。
- 大型 outputs 和 pytest 临时目录不纳入 Git；源码/协议与小型证据文件可另行审核提交。
- 本地不跑项目测试/训练；uv Python 的可用性不代表 numpy/matplotlib/pytest 已安装。
- 不自动安装依赖/下载模型，不自动开始下一阶段；不覆盖历史 2026-10-12 的 Windows 测试证据。

- 回传排除各 run 的 `pytest-tmp/` 一次性测试目录（pytest 会在其中创建临时符号链接），仍严格拒绝正式状态、日志和 outputs 内的符号链接。JUnit 与测试日志照常回传。

## 当前进度更新

HPC 项目 .venv（Python 3.11.15）及 R1、R2 重绘、R3 单 mission 已实际完成，详见 plans/next_steps.md 和 research/reproduction/repro_report.md。environment/hpc_python.json 保留此前只读裸解释器快照；当前已安装环境以 environment/project_environment.json 为准。runtime_python 现指向项目 .venv，而非系统或裸解释器。
