# Research Task Log — deployment admission

2026-11-26，Asia/Shanghai。用户授权继续“真实部署准入补齐，完成后再申请有界T3能力诊断”。无Git提交/推送授权。既有v2-I未提交文件和三项用户untracked保持原样，沿用此前保留授权；不reset/checkout/clean/覆盖/改名。

## 阅读、规划与版本

重读AGENTS、总说明书、README、v2-I任务日志、HPC sync README/project_status/plans/next_steps和v2四文档；大段输出有截断后按文件/行范围补读。审查独立v2-I应用/guard和旧live/client/生命周期/launcher路径；不读registry记录或真实题文/gold。先写task_brief，冻结最多240s、16MiB SSD的无模型检查预算。

本地只读`git status --short`、`rev-parse HEAD`、`remote -v`、`branch --show-current`、`diff --name-only`与cached diff；GitHub用`git -c http.proxy=http://127.0.0.1:7897 ls-remote --exit-code origin refs/heads/research/progress-audit-2026-10-19`。本地/HPC/GitHub均458a96f59b620a02e6872d038b87912eb39e92e4，无tracked/staged修改。

## 实际HPC行政只读命令

使用`ssh -o BatchMode=yes -o ConnectTimeout=10 hpc`；固定`cd /home/u202520081000097/jupyterlab/Paper/gosc`。

1. `id; hostname; git rev-parse HEAD; .venv/bin/python --version; git diff --name-only -- extensions/masbench_reasoning scripts/hpc_ollama.py; df -B1 ...`（实际工具命令用&&，此处按项目列举）。身份正确，shared df仅辅助，不作个人容量。
2. `.venv/bin/python research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py`、`cat /proc/self/cgroup`、指定cgroup quota/period/RAM文件、`test ! -w .../tasks`。发现SSD余6594560B<16MiB预算，明确停依赖同步/测试；CPU/memory控制文件不可写。
3. 新`readonly_inventory.py`作为UTF8 SSH stdin交给`.venv/bin/python -`，只读独立行政核验、无远端写入。保存完整stdout为hpc_readonly_inventory.json，SSH退出0。主collector wall0.367943645s；调用3个GET，generation/render/unload/helper/start/stop=0；没有声明为registered test。
4. `stat -c ... .local/ollama/downloads/ollama-linux-amd64-0.11.11.tgz`失败No such file；保留该负发现，没有移不存在的归档。`ls -ld`/readlink查cgroup控制目录。
5. `find .local/hpc-sync .local/t3rv2i-git-meta-20261126 .local/t3rv2i-git-meta-20261126-delta -maxdepth 2 -type f -size +1M ...`无候选；限定项目maxdepth2大文件查询排除results和.git，未找到可直接处理大文件。仅列.local一级目录名。
6. `find .local/diagnostic-wheels -maxdepth 1 -type f ...`查见2 wheel+manifest，后以明确三路径`sha256sum`冻结SHA。`find .local/masbench-exact-context -maxdepth 2 -type f -size +8M ...`无其他候选。没有全home扫描、第三方项目清理、路径移动、依赖安装或wheel执行。

全部为管理/只读身份/文件哈希，不跑研究计算、pytest、统计或压力。无新hpc_runs测试，因此无新测试receipt，不能伪称已完整完成部署验收。因quota gate失败也没有同步本轮文档至HPC。

## 本地编辑及保护

仅新增本目录、部署合同/未批准计划/修复申请和报告。手工按既有字面规格序列化2个人工消息输入资产，不导入/执行Agent，不作模型或精确计数；未来需在HPC合同中对比Agent.request(t0)。本地Python仅文件编写、JSON序列化和轻量SHA核对；非测试/分析替代运行。字面资产SHA9a1c1191f1a41a70f24c787f8698cec354ea78fbc0afc9d6366b2f2188cb104a。

按v2-I delivery_manifest逐项复核48份前序交付，全部原字节SHA不变。旧T3结果、旧授权、旧身份、D1及科学No-Go不动。新任务brief原拟新增live代码/合同，在quota阻断后延期；只完成其具体差距映射，不把新文档当成实现已完成。

## 新预算候选与尚缺决定

恢复quota的具体申请只迁3个下载缓存原字节到新HDD目录；含copy/fsync/SHA/receipt后才去源副本，120s/64MiB HDD，**未批准、未执行**。约33.45MiB空间预计只能满足无模型32MiB准入，不承诺真实64MiB阈值。

另需明确严格硬隔离还是监测停止合同，不能把无cgroup写权/GPU采样当硬限通过。纯合成真实预检候选2生成/156HTTP/2000s、16384/512、AS2GiB；仍approved:false且入口/source/receipt/当前PID绑定不齐。不沿旧T3授权启动服务或任务。

两阶段真实候选若各自切换/回滚，必须多计管理：合计生成50不变，但HTTP596/活动阶段时间20360s候选超原468/19100。阶段间等待与全局deadline协调仍待审，原不可重置规则不擅自改。当前不请求签发真实T3任务授权；先解决工程前置问题。

结果：身份若干项通过；SSD/独立live入口/资源硬边界/真实window/render/usage/清理回滚均未齐，真实部署Blocked，有界T3申请不释放。没有真实模型、没有新能力成绩、没有T4/训练/校准/封存test、没有Git提交推送。完整静态交付后停止，等待具体工程处理决定。
