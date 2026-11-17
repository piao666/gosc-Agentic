# 三项准入工作实际记录

日期2026-11-16 Asia/Shanghai。本地HEAD916289ba20fd9808a3673af0aebf175bfc830ccc；旧未提交报告均为本会话此前成果，保留。

## 用户决定/授权

1. 用户要求推进评价主张与数据隔离、精确计数准备、真实部署三项。
2. 用户异步明确选择“保留D1，优先保证文章隔离”；形成独立决策，不改registry。
3. 用户异步明确允许Go1.26.11隔离安装/固定Ollama源码与锁定模块构建：1800s/2CPU/进程树RAM4GiB/下载≤1GiB/新增磁盘≤4GiB，离线合同120s/2GiB/16MiB；无模型/GPU/服务变化。
4. 没有新增C++工具链安装、真实模型/服务配置/四题、正式评价/训练、Git提交push授权。

## 实际命令与环境管理

- 本地`git status --short`、`git rev-parse HEAD`、`git branch --show-current`、`git remote -v`；Get-Content读取AGENTS、研究说明书的本会话先前内容、README/当前计划、client/hpc_runs/sync_hpc/hpc_ollama与已验收规格。
- `ssh -o BatchMode=yes -o ConnectTimeout=12 hpc <只读命令>`：首次沙箱Permission denied后升级连接；查UID/hostname/Git/cgroup/工具/df/quota。v2 cgroup路径不可用、quota命令缺失、旧Git不支持branch --show-current均保留，随后读v1和symbolic-ref。
- `python research/logs/masbench-context-deployment-2026-11-16/run_readonly_inventory.py`：UTF-8/LF stdin只读脚本，GET version/ps，无POST/权重/题目；输出readonly_inventory.json。
- `python .../reconcile_archive.py`：增量Git bundle；核远端901源SHA、无running、origin、ancestor，atomic update-ref4754bed→916289b；不改worktree/index或历史run。输出archive_reconcile_stdout.json。
- `python .../probe_module_transport.py`：四固定公共metadata端点各5s、每响应≤64KiB。Google官方proxy/sumdb不可达；可达镜像记录签名数据库信息。没有通过关闭GOSUMDB修网络。
- `python .../release_own_failed_reservation.py`：仅回收已核UID/路径/failed状态/0下载的自有v2占位，336011264实际字节→0；文件与失败记录保留。
- 只读`stat`、`nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader`；各≤15s的du/目录元数据检查。全home和部分环境du到时未完成，不报全账户总占用；大量source_untracked路径输出截断，不作为清理清单，不删除任何历史文件。
- `gcc --version`、`g++ --version`、command -v、getconf：GCC7.5.0/glibc2.27，无已定位的替代C++17工具链。没有安装GCC/Clang或变更系统库。

## 登记执行

每次实际入口：

```text
python scripts/hpc_runs.py launch --run-id <下列ID> --kind infrastructure --stage MASBench-context-build --purpose <原manifest中的说明> -- /usr/bin/timeout --signal=TERM --kill-after=5s <秒数> {python} experiments_ext/masbench_context_build.py
```

run ID / wrapper秒数：

```text
hpc-masbench-context-build-20261116       1800
hpc-masbench-context-build-v2-20261116    1790
hpc-masbench-context-build-v3-20261116    1775
hpc-masbench-context-build-v4-20261116    1730
hpc-masbench-context-build-v5-20261116    1715
```

每次不是把1800s预算从头用满，实际累计runner90.154489s；短失败先结束，后续只在已定位原因/明确修改后新run。五次均failed且完整回传。构建字节计数继承前轮，最后81272231bytes，原始manifest记录每轮source sync ID/SHA、argv、dirty与资源。

v1自有fallocate只写模式错误；v2EDQUOT；v3Go成功但Google网络不可达；v4模块/7源码校验成功但复制目录只读；v5最终C++17/vendor缺失。实现遗漏如实承认，不甩给作者算法。构建源码快照保留各自版本；最后新停止门是结果后的安全控制，不能冒充已执行代码。

## 文档与未执行项

新增D1决策、Go helper/构建/离线合同代码、授权与临时盘/停止状态、部署具体提案和报告/日志。project_status/next_steps/researchREADME新增本轮判断；dashboard/STATUS变化来自标准pull，不手改历史run。

离线合同、模型加载/生成、服务修改、真实题目、正式划分/power/评价/训练未运行。原GOSC/Native/GP-ID/BF/原client/wire/registry不改。一次导航patch因字段顺序不匹配未应用，检查后按原顺序补充；没有部分覆盖用户文件。

最后仅做本地JSON/Markdown链接/空白/身份与产物轻量核验，然后标准source/doc同步；结果见management_verification.json和final_source_sync_stdout.txt。本轮无Git提交push，已授权构建因为新增C++17/完整vendor前置条件未满足而停止。
