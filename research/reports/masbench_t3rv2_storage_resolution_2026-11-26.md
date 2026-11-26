# Research Task Report — HDD复用与SSD阻断解除

2026-11-26 Asia/Shanghai。**本轮存储迁移/当前容量准入Go；真实部署仍Pending/Blocked。** 用户允许HDD复用及部分文档迁移，不包含GPU/RSS监测替代硬隔离、真实生成、服务切换或Git提交推送。

- **Research Question / Hypothesis**：[HYPOTHESIS] 能否在不更改源码、历史结果和运行身份的前提下保全归档并恢复SSD准入空间？本轮是文件管理，不验证模型能力。
- **已核验前人工作**：[RUN/既有] 前序只读SSD余6594560B、HDD余517812883456B；原54/67测试及科学No-Go不重标。本轮没有[PAPER]新结论。
- **实际阅读源码**：[CODE] `scripts/sync_hpc.py:45–70,118`显示覆盖前备份与HPC数据通道排除；只迁其`.local/sync-backups`副本，不改工作文件。新增`relocate_archives.py`的路径白名单、先复制读回再去源、19项保护SHA及quota前后记录；独立`verify_archive.py`逐件重新读SHA。
- **本轮新增或修改**：[存储布局策略](../protocols/masbench_t3rv2_hdd_storage_policy_v1_2026-11-26.md)、本报告、[任务与审计附件](../logs/masbench-storage-hdd-2026-11-26/README.md)；HPC仅迁移3类已确认非活动管理文件，原目录新增3个恢复索引。不改旧研究说明、实验数据、模型、.venv、服务、Git对象或旧run manifest。
- **实际运行**：[RUN/管理] 本地SSH发起、HPC n1/UID8301880/.venv3.11.15执行文件清点/迁移/独立SHA管理；三端已知base458a96f，当前本地/HPC HEAD未变。非测试、非科学分析，不伪造hpc_runs登记或测试结果。
- **测试与结果**：没有新增pytest/科学测试。实际迁移634常规文件/87764721B，全部HDD读回SHA通过；独立再核634项通过；保护19个当前源码/Prompt/registry/Git元数据SHA未变。本地回传5份管理原件逐字节SHA一致；前序48+14交付SHA保持。
- **失败/负面证据**：未发现迁移/读回失败。安全白名单不足以恢复理想1GiB余量，故不动环境/模型/实验结果凑数。SSD当前仍较紧，未来大文件须放HDD；采样quota可能延迟反映，与逻辑文件大小不完全相同。
- **与原GOSC差异**：无算法/通信/调度/评分变化，只调整非活动管理归档位置。
- **公平性与泄露检查**：没有选题、解析registry或读取正文/gold，不新增模型输入或成绩；只回传文件路径/大小/SHA/恢复映射，HDD历史归档内容不公开Git。
- **成本**：迁移管理12.237842s，独立读回0.221276s；顺序1CPU affinity、普通进程AS256MiB。模型/helper/HTTP/服务操作均0；GPU未调用/未测新峰值。HDD实际quota增约88.62MiB（含目录/manifest等，非仅逻辑字节），在4GiB管理上限内；无新增依赖或模型下载。SSH/管理目录清点开销另计未仪器化。
- **可否进入下一阶段**：SSD个人当前余95662080B=91.23MiB，超过无模型32MiB/真实候选64MiB的空间门。**只解除存储阻断**；独立live入口/D01–D12、资源保证选择、16384逐请求render/usage及服务退出/回滚未通过，不能直接运行能力诊断或T4。
- **用户需要批准的下一步**：存储迁移已获授权并执行，无须再批同一迁移。GPU/RSS监测候选尚未批准，严格硬隔离缺口仍保留；真实合成部署与后续T3生成各需具体独立批准。当前不申请或执行真实能力实验。

## 迁移范围与结果

源根为`/home/u202520081000097/jupyterlab/Paper/gosc/.local/`，目标根为`/hdd/u202520081000097/gosc-admin-archives/20261126-deployment-admission/`。

| 目录 | 内容 | 处理 |
|---|---|---|
| diagnostic-wheels | 两份NumPy下载wheel与其manifest | 原字节HDD保存；已安装环境不动 |
| git-checkpoints | 旧操作前保存的patch/index/status/proof副本 | 原字节HDD保存；当前.git不动 |
| sync-backups | 历次同步覆盖前副本 | 原字节HDD保存；活动checkout与历史run不动 |

每个目标文件均独立读回SHA、fsync并落完整manifest后，才复核源inode/mtime/size/SHA并移除SSD副本；没有递归清空，没有符号链接。旧源目录仍在，并留`ARCHIVED_HDD_20261126.json`指向完整路径映射。原字节全部在HPC HDD保留，不是删除历史证据。

SSD个人quota读数：迁移前6.29MiB；首次完成89.38MiB；独立读回时91.23MiB。读数变动只报告观测，不将差额全部写成固定逻辑释放量。HDD剩余约482GiB，执行前仍应重新查询。

## 后续存储纪律与回滚

活动源码/环境留SSD，下一新run的大型原始证据与测试临时树应显式绑定HDD独立目录，SSD只保留登记、短日志和索引；新入口尚未接入时不得声称此策略已自动执行。原sync脚本未改，今后少量新sync-backups可按同等核验协议另批次归档，不自动重跑本次一次性脚本。

恢复任一旧文件：按migration_plan定位HDD原件，核SHA并确认SSD原路径不存在，空间足够后复制回、恢复mode/mtime、fsync和SHA读回；已有新文件时不覆盖。HDD副本保持不删。无需回滚时，不把归档全复制回SSD。

**存储Go不等于真实部署Go，更不等于任务能力或科研收益成立。** 本轮无真实生成、无服务变更、无Git提交推送；T3/G1/GP-ID科学No-Go保留。
