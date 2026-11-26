# 实际命令与执行登记

2026-11-26 Asia/Shanghai。下列为本轮实际执行；所有测试/审计仅HPC，Windows只编辑、Git/轻量SHA/同步/回传。源码/运行身份见各manifest，未Git提交或推送。

## 启动与管理

- `git status --short`、`git rev-parse HEAD`、`git remote -v`、分支及GitHub只读核查；local/GitHub为c062。
- `ssh -o BatchMode=yes -o ConnectTimeout=10 hpc ...`：uid/n1、Python3.11.15、HPC路径/旧HEAD458、cpuset0-1、CPU200000/100000、24GiB及quota只读复核。
- 增量bundle传输：`.local/t3rv2t-delta.bundle` → `/tmp/gosc-t3rv2t-delta-20261126.bundle`；首个按分支名fetch失败（bundle只广告HEAD），按实际HEAD fetch成功。备份`.local/t3rv2t-git-align-20261126`，临时GIT_INDEX_FILE、read-tree/update-ref后只替换Git元数据，无checkout/reset/clean。1508工作文件SHA不变，见git_alignment.json。
- 每次源码上行：`python scripts/sync_hpc.py --exclude-untracked .workbuddy/memory/2026-11-25.md --exclude-untracked '11-17审阅任务安排.md' --exclude-untracked 'T3-R_科研失败归因与研究前提复核任务书.md'`。已核snapshot：20261126T073702Z、073948Z、074347Z、074535Z、074815Z，全部sha256_mismatches=[]。最后一项是r3及独立审计源身份；最终文档/模板同步单列，不回填历史run。

## 新合同（共同命令前缀）

HPC工作目录`/home/u202520081000097/jupyterlab/Paper/gosc`：

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m experiments_ext.masbench_t3rv2i_register run --run-id <ID> --kind test --stage T3-R-v2-T --purpose <PURPOSE> --gzip-source-patch -- {python} -m experiments_ext.masbench_t3rv2t_contract
```

| ID | PURPOSE | 结果 |
|---|---|---|
| hpc-t3rv2i-task-contract-20261126 | task_profile_artificial_8x6_no_model | exit1，23pass/1fail，原始cleanup事件失败保留 |
| hpc-t3rv2i-task-contract-r2-20261126 | task_cleanup_journal_fix_and_full_8x6_acceptance | exit0，24pass |
| hpc-t3rv2i-task-contract-r3-20261126 | final_source_receipt_binding_task_contract | exit0，25pass |

wrapper实际子命令是`.venv/bin/python -m pytest -q tests_ext/test_masbench_t3rv2t_task.py -p no:cacheprovider --basetemp /hdd/u202520081000097/gosc-t3rv2t-contracts/<ID>/pytest-tmp --junitxml <run>/outputs/pytest.xml`；PYTEST_DISABLE_PLUGIN_AUTOLOAD=1、PYTHONDONTWRITEBYTECODE=1，AS256MiB，120秒alarm/110秒pytest子进程。没有其他测试suite。每次HDD清单/压缩原件、contract.json、pytest.xml均保留。

## 独立审计

```text
PYTHONDONTWRITEBYTECODE=1 T3RVT_CONTRACT_RUN=hpc-t3rv2i-task-contract-r3-20261126 .venv/bin/python -m experiments_ext.masbench_t3rv2i_register run --run-id hpc-t3rv2i-task-audit-20261126 --kind analysis --stage T3-R-v2-T --purpose independent_task_fixture_journal_and_frozen_source_audit --gzip-source-patch -- {python} -m experiments_ext.masbench_t3rv2t_audit
```

exit0，登记0.383877秒，审计自身0.315649秒；不导入生产Parser/Scorer/TaskDriver，0真实模型/HTTP/helper/服务操作。

## 完整回传和结束只读核查

```text
python research/logs/masbench-t3rv2t-2026-11-26/collect_evidence.py hpc-t3rv2i-task-contract-20261126
python research/logs/masbench-t3rv2t-2026-11-26/collect_evidence.py hpc-t3rv2i-task-contract-r2-20261126 hpc-t3rv2i-task-contract-r3-20261126
python research/logs/masbench-t3rv2t-2026-11-26/collect_evidence.py hpc-t3rv2i-task-audit-20261126
```

三份完整双端receipt：fca11334f6、925e22a879、39cfb51354（完整名见README）。所有常规文件逐件SHA；pytest便利symlink明确不作为常规原件，无测试删除。

结束执行`.venv/bin/python research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py`，原始JSON见final_quota.json。只读cgroup v2文件不存在，命令exit1后未继续该串的服务核查；改读实际v1的`/sys/fs/cgroup/cpu/cpu.cfs_quota_us`、`cpu.cfs_period_us`、`memory/memory.limit_in_bytes`得到200000/100000/25769803776。`test ! -e .local/ollama/context_profile.json`成功；`wc -c .local/t1-service.lock`为0；`nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits`为0。未发服务metadata HTTP，不把无profile等同于新测有效1024窗口。

本地另做新增源码规范化LF SHA与r3 source_files逐件相等核查，用返回的contract/audit SHA填写**仍approved:false**的授权模板；不是项目测试、真实任务或数据统计。最后git diff检查只核文件/边界，不运行模型、重启服务、安装依赖或训练。

最终`git ls-remote origin refs/heads/research/progress-audit-2026-10-19`仍c062；无推送。原CRLF共享文件的普通diff --check把CR标为空白；保持原CRLF后以`git -c core.whitespace=cr-at-eol diff --check`通过，逻辑差异10增4删；规范化LF SHA仍与HPC r3完全一致。最终文档/未批准模板用同一sync命令上行；不回写r3/audit历史source身份。
