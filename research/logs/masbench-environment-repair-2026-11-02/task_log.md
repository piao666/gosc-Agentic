# MASBench环境修复执行记录

用户授权：修复模型并安装依赖。此项覆盖必要的环境安装/模型恢复；不放行Reasoning任务、模型生成、训练、扩样本或Git提交。

## 根因与实施边界

[RUN] [diagnosis_stdout.json](diagnosis_stdout.json)确认Ollama进程PID8964、运行时0.11.11、服务配置与实际OLLAMA_MODELS一致。已知持久模型目录仅有空manifests，没有blobs；另外两个已知默认位置不存在。故不是已证实的路径错配，而是已知模型存储内容缺失；何时/为何缺失未核实，不把清单为空解释成模型能力失败，也未搜索整台服务器。

[CODE] [Reasoning依赖选择](../../benchmarks/masbench_reasoning_requirements_v1.in)取官方固定commit c0301a6的四项客户端版本；未安装其他任务/训练依赖。实际Reasoning主要入口为标准库与OpenAI客户端，requests/dotenv作为原依赖声明中的客户端辅助保留。不在原GOSC `.venv`内安装。

使用superpowers systematic-debugging流程先核查跨服务/路径边界。首个`hpc_runs.py launch`在本地Git bundle临时文件创建处被沙箱拒绝，未创建HPC计算run；经沙箱外授权机制以同一run ID重试成功。该失败不抹除，未更改SSH凭据/权限或临时目录来绕过限制。一次直接PowerShell SSH查询返回异常文本，未当作远端状态；改用Python subprocess参数列表成功只读查询。

## 登记运行与命令

1. `python research/logs/masbench-environment-repair-2026-11-02/diagnose_readonly.py`：只读元数据，未读权重。
2. `python scripts/hpc_runs.py launch --run-id hpc-masbench-repair-plan-20261102 --kind infrastructure --stage MASBENCH-ENV-PLAN --purpose 'Read official manifests and bound authorized model restoration and isolated Reasoning dependencies; no inference' -- '{python}' research/logs/masbench-environment-repair-2026-11-02/repair_environment.py plan`。HPC5.707142s、exit0；sync20261102T055233Z，716文件、SHA mismatch0。receipt20261102T055415Z-cc2d04回传21,858,839bytes、all_outputs_mirrored=true，其中包含早先尚未拉回的管理记录，不都是本次新运行数据。
3. 已同步同一源码后，调用`hpc_runs.remote_command`执行HPC `scripts/hpc_runs.py run --run-id hpc-masbench-dependencies-20261102 --kind infrastructure --stage MASBENCH-DEPENDENCIES ... -- '{python}' research/logs/masbench-environment-repair-2026-11-02/repair_environment.py dependencies`。HPC4.198572s、exit0；原GOSC包元数据前后相同。独立路径`.local/envs/masbench-reasoning-v1`；uv compile生成传递版本+hash锁，uv sync使用require-hashes/only-binary，uv pip check和四包导入通过；仅构造/关闭本地endpoint客户端，不发请求。
4. 同一登记入口执行`hpc-masbench-model-restore-20261102`，kind infrastructure、stage MASBENCH-MODEL-RESTORE，脚本action models。三个manifest事前按历史SHA核验一致，unique blob声明8,632,391,403bytes；预算10GiB、3600s，单模型顺序恢复。目标为通过官方API `/api/pull`恢复并校验所有blob SHA-256；没有generate/chat、模型加载或服务升级。此条登记启动与目标，完成状态以该run的status/outputs及最终报告为准。

所有执行命令、资源、基线与sync哈希以对应manifest为准。源码同步未覆盖远端专有结果；运行期间不更新远端源码。模型权重不回传、不入Git；只拉运行账本/锁/许可/校验元数据。

## 慢速下载与受控续传

[RUN] 首个qwen2.5:3b在Ollama校验后成功注册，随后llama3.2:3b尾段持续慢速。额外infrastructure run `hpc-masbench-download-probe-20261102`用官方registry读取64KiB指定range，2.740801s、exit0；HTTP206、65,536bytes、请求本身2.660857s。这只确认端点响应，不作持续吞吐推断。

[CODE] 固定[Ollama0.11.11下载实现](https://github.com/ollama/ollama/blob/v0.11.11/server/download.go)支持保留分片checkpoint与续传；相应slow/stall处理提示重新pull取得更快连接。本轮未改Ollama代码。GitHub连接器读取该文件遇到transport error，改用同版本官方raw只读阅读。

[RUN] 06:29:05Z核对status和`/proc/5358/cmdline`确为本轮models子进程后，SIGTERM停止该子进程，未停止PID8964服务。原run由登记器记为failed/exit-15，1912.014109s；这是真实的受控中止记录，保留其原始日志/partial/checkpoint/已完成模型。新脚本仅允许复用与历史digest一致的已完成项，并将重试alarm绑定到原始05:57:13Z开始后的同一个3600s截止，不重置预算。待无活动run后同步并以`hpc-masbench-model-restore-retry1-20261102`续传；不清空模型目录或删除partial。

## 不变的研究边界

## 配额失败、用户指定清理与新窗口

第二次受控停止retry1后，其终态为failed/exit-15、904.705078s。后续retry2因EDQUOT未能正常落盘最终状态；核对PID8900消失后，经`hpc-storage-reconcile-capacity-20261102`保留原status副本并标failed，退出码/结束时刻未知保留null，reconciled_at另记，未伪写completed。最初hai-study登记亦在manifest阶段失败，命令未启动；其失败元数据后补有明确reconciled说明。原回传receipt写回失败也保留，后续新receipt重新核全。

用户先选择增加配额，但普通账号无quota/setquota工具，未宣称管理员扩容完成。随后用户明确授权清理hai-study，并提供两个Laya模型精确路径。只删除：`/home/u202520081000097/jupyterlab/hai-study`、`/home/u202520081000097/NextWork/models/laya-multilingual`、`/home/u202520081000097/NextWork/models/laya-typed-decisions`，删除前allocated分别2,356,613,120、678,322,176、846,303,232bytes。精确路径/owner/无symlink/无嵌套挂载/进程边界通过；NextWork父目录、GOSC、模型及SSH目录存在检查通过。hai-study因配额连manifest都无法写，按用户明确删除授权在/tmp保存before/after并回传本地后执行，空间恢复后登记导入审计；这属于紧急文件维护，非未登记科学测试。

首容量探针O_WRONLY在该文件系统返回EBADF，不能解读为配额容量；改O_RDWR后真实5GiB申请遇EDQUOT，stdout flush又触发EDQUOT，run exit120，355byte结果文件仍保留。没有将其说成容量通过。用户随后明确批准删除完整官方安装包1,908,755,362bytes，SHA匹配1d2988c…；保留运行库和6,365,184byte旧失败partial。`hpc-authorized-installer-cleanup-20261102`exit0。

`hpc-storage-capacity-after-cleanup-20261102`用O_RDWR成功申请5,368,709,120bytes逻辑容量并释放临时文件，9.050564s/exit0。不是账户总配额测量，不把allocated旧文件大小当实际配额释放值。用户同时明确批准新的30分钟剩余模型维护窗口；开始07:14:11Z，绝对截止07:44:11Z，旧3600s记录不改写。续传run `hpc-masbench-model-restore-after-storage-20261102`显式带该deadline；不运行生成或任务。

截至此记录，依赖已验收，qwen2.5:3b已注册，其余模型及全blob/SDK最终验收以新run实际结果为准。科学No-Go不变。

本次环境修复不等于Reasoning能力、无线接口/零损伤合同、通信收益或发表性。维持原GOSC1024服务上下文配置，未偷偷扩上下文或测试题库；未来Reasoning配置容量仍需另审。G1、GP-ID科学No-Go及旧失败保留。完成环境验收后停止。

## 最终完成记录（替代上文Pending的当前状态，历史失败不改）

清理后run `hpc-masbench-model-restore-after-storage-20261102`最后Qwen7B尾段仍慢，07:27:15Z受控停止，failed/-15、548.690826s。后续`hpc-masbench-model-restore-after-storage-retry1-20261102`沿用07:44:11Z截止、复用已下载分片，07:29:11Z completed/exit0，109.357746s，全部模型manifest及唯一blob8,632,391,403bytes大小/SHA核完。该大小不是实测重试总流量，109s也不是所有历史下载耗时。

`hpc-masbench-environment-metadata-20261102`使用独立环境Python，以脚本完整字面量记录在manifest的`-c`参数，07:31:49Z completed/exit0，3.443414s。OpenAI SDK models.list读到三个模型，Ollama show metadata通过，ps无模型加载；未发chat/generate。HPC`.local/envs/masbench-reasoning-v1/gosc_readiness.json`记录端点/包/模型身份与能力Pending。

原恢复脚本的单模型license文件名对Llama多层许可产生覆盖歧义；保留原输出，`hpc-masbench-model-license-audit-20261102`逐层哈希并唯一命名归档4层，0.114711s/exit0；使用新license_layer_index，不假称旧索引完整。未来helper文件名已修正，本轮实际补审命令完整字面量在新manifest中。

回传曾因动态STATUS改变而失败，之后无活动维护run时重新拉取；第一次最终拉取受100MiB累计上限漏21,272,560byte source_changes.patch，第二次补齐。许可补审后最终receipt `20261102T074010Z-67b8fc.json`，21,944,790bytes新增下载、all_outputs_mirrored=true，receipt已回写HPC。权重不回传；旧失败/漏项receipt保留，不回写成过去成功。

`python research/logs/masbench-environment-repair-2026-11-02/verify_management.py`轻量管理检查通过，73冻结源码和保护报告不变、原GOSC包元数据不变；Linux锁副本SHA与HPC原件一致，模型/许可/结果artifact哈希与最终receipt核验。不是pytest或科学实验。之后停止，不提交Git、不启动模型/任务/训练。
