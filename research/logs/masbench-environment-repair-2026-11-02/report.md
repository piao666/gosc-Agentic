# Research Task Report

- **Research Question / Hypothesis**：无新科学实验。本轮处理用户所指“模型清单为空、openai/httpx等依赖缺失”，恢复可审计基础环境，不检验Reasoning能力或任务信息价值。
- **已核验前人工作**：[CODE] MASBench固定c0301a650db95958924bb080192c09fef39389a5官方requirements与Reasoning入口导入；[官方输入](https://github.com/BUPT-GAMMA/MASBench/blob/c0301a650db95958924bb080192c09fef39389a5/requirements.txt)。固定Ollama0.11.11下载代码的原生断点续传机制只用于环境维护，不作研究贡献。[源码](https://github.com/ollama/ollama/blob/v0.11.11/server/download.go)。
- **实际阅读源码**：[CODE] 原有`scripts/hpc_ollama.py`、`scripts/hpc_runs.py`、`scripts/sync_hpc.py`；上述官方依赖与agents/runner/api_key_loader导入边界。未改GOSC方法、无线/selector或任务接口。
- **本轮新增或修改**：本目录管理/修复/清理/验收脚本及原始记录；Reasoning专用requirements输入、Linux hash锁、环境说明；三份静态交付与研究入口补当前环境状态。环境部署在HPC`.local/envs/masbench-reasoning-v1`，模型在原models/ollama-gosc，不入Git/不回传权重。
- **实际运行**：[RUN] 均为infrastructure或轻量只读管理，详见[task_log.md](task_log.md)。HPC基线014b85dfc472c45d8ea5f15e83e0c1ed8e938daf、n1/UID8301880、2CPU/24GiB；同步20261102T055233Z、20261102T063036Z、20261102T071710Z均SHA mismatch0。执行/模型与源码快照以各run manifest为准。
- **测试与结果**：[RUN] 独立环境4.198572s安装/uv pip check/导入通过，20包精确锁；三个本项目历史manifest SHA相等、全部blob SHA通过；最后续传109.357746s完成，SDK GET模型清单/metadata验收3.443414s通过。**109s仅最后一次续传，不是全部下载总耗时。** 项目pytest、仿真、Reasoning题目、LLM生成、训练均未运行，任务N0。
- **失败/负面证据**：初次同步受本地沙箱临时Git bundle权限阻断；多次网络尾段慢速，3个run受控中止保留exit-15；retry2 EDQUOT导致终态丢失，核对进程消失后标failed并保留exit/end=null与reconciled_at；hai-study首次登记写manifest失败未启动。O_WRONLY容量探针EBADF、O_RDWR探针EDQUOT/exit120保留，后续正确容量核验另立run通过。回传曾receipt写回EDQUOT、动态STATUS哈希变化及100MiB累计上限未回全；最终回传完成状态以新receipt/verification为准。未删红记录或改为成功。
- **许可归档补审**：原模型恢复脚本以每模型单文件名保存license，Llama实际有两层许可，造成新产物中同名覆盖及旧索引歧义。原成功run输出不改写；`hpc-masbench-model-license-audit-20261102`独立从真实manifest/blob逐层校验，以digest唯一命名归档全部4层。今后使用其license_layer_index，原问题及修正保留；这不影响权重哈希、模型注册或SDK验收，不当作许可适用性已获法律审定。
- **与原 GOSC 的差异**：独立安装4项Reasoning客户端直接依赖；原GOSC `.venv`包元数据前后不变，Ollama0.11.11/驱动/默认context1024不变。模型manifest与本项目2026-10-20记录一致；不声称与原论文作者模型快照完全等价。
- **公平性与泄露检查**：未读.env/私钥、未使用收费key或云端回退；SDK显式loopback地址/公开占位key，max_retries0；仅GET models和show metadata，没有chat/generate、数据题目/gold或模型加载。无需注册新科研样本，不改变原数据split与负结果。
- **成本**：恢复唯一blob8,632,391,403bytes（HPC端）；最后成功续传109.357746s、元数据验收3.443414s，另有前序下载/等待/失败与清理，详见下表。未测实际推理吞吐/tokens/GPU峰值；不是算法开销实验。模型不回传；维护日志/锁/许可/校验信息按receipt核验回传。
- **可否进入下一阶段**：**Go：文件完整性、独立依赖、metadata客户端链路。Pending：模型加载、chat参数/context/usage/timeout兼容、Reasoning能力、数据正文/分组、权限/无损/wire合同。任务实验与训练未放行。** G1和GP-ID科学No-Go保留。
- **用户需要批准的下一步**：本次已授权环境修复与精确清理完成后停止。若继续，需另行确定数据核验与无模型工程合同，能力诊断再按完整预算授权；不会自动调用模型。

## 精确清理边界与结果

用户逐项批准后，仅删除下表目标；目录无symlink/嵌套挂载、owner及路径边界核对，运行库和旧失败partial保留。清理前allocated值**不是实际释放的账户配额测量**；未调用管理员setquota，也不声称账户总配额已增加。

| 已删除目标 | 删除前allocated bytes |
|---|---:|
| `/home/u202520081000097/jupyterlab/hai-study` | 2,356,613,120 |
| `/home/u202520081000097/NextWork/models/laya-multilingual` | 678,322,176 |
| `/home/u202520081000097/NextWork/models/laya-typed-decisions` | 846,303,232 |
| GOSC `.local/ollama/downloads/ollama-linux-amd64-0.11.11.tgz` | 1,908,760,576 |

NextWork父目录、GOSC、研究结果、现有模型与SSH目录保持；完整安装包删除前SHA等于官方1d2988c…，旧6,365,184byte失败partial未删。hai-study在配额无法写manifest时，审计先存/tmp并回传本地，后登记补入before/after。uv缓存未清理，初步单链接估计与实际多链接约束保留于[配额阻断记录](storage_blockage.md)。

最终`hpc-storage-capacity-after-cleanup-20261102`成功申请5GiB逻辑容量并释放，9.050564s/exit0；不是长期独占容量保证。新30分钟维护窗口由用户明确批准，07:14:11Z–07:44:11Z，三个模型在07:29:11Z完整恢复，metadata在07:31:49Z完成，没有越过该窗口继续下载。

## 运行证据入口

| Run | 结果/用途 |
|---|---|
| hpc-masbench-repair-plan-20261102 | completed，官方manifest与8.63GB预算 |
| hpc-masbench-dependencies-20261102 | completed，独立环境/hash锁/导入/check |
| hpc-masbench-model-restore-20261102 | failed/-15，1912.014109s，慢速连接受控停止 |
| hpc-masbench-download-probe-20261102 | completed，64KiB range诊断，不代表持续吞吐 |
| hpc-masbench-model-restore-retry1-20261102 | failed/-15，904.705078s，受控停止 |
| hpc-masbench-model-restore-retry2-20261102 | failed/reconciled，EDQUOT，未知exit/end保留null |
| hpc-hai-study-cleanup-20261102 | failed/reconciled，初始manifest写失败，命令未启动 |
| hpc-storage-reconcile-capacity-20261102 | completed，失败台账修复/导入清理证据；内含EBADF容量结果，不能当通过 |
| hpc-storage-capacity-rdwr-20261102 | failed/120，EDQUOT结果及stdout flush错误 |
| hpc-laya-authorized-cleanup-20261102 | completed，用户精确指定两个模型目录 |
| hpc-authorized-installer-cleanup-20261102 | completed，官方SHA核对后删完整安装包 |
| hpc-storage-capacity-after-cleanup-20261102 | completed，5GiB容量核验并释放 |
| hpc-masbench-model-restore-after-storage-20261102 | failed/-15，548.690826s，最后模型尾段重连 |
| hpc-masbench-model-restore-after-storage-retry1-20261102 | completed，109.357746s，全部blob验证 |
| hpc-masbench-environment-metadata-20261102 | completed，3.443414s，独立SDK模型清单/metadata，无推理 |
| hpc-masbench-model-license-audit-20261102 | completed，0.114711s，4层许可唯一命名/哈希补审，保留原歧义产物 |

原始状态、stdout/stderr、manifest、artifact哈希位于`research/sync/runs/<run-id>/`；最终文件管理核验见[verification.json](verification.json)。锁与用法见[环境说明](../../benchmarks/masbench_reasoning_environment_v1.md)。

最终回传receipt为`research/sync/receipts/20261102T074010Z-67b8fc.json`，all_outputs_mirrored=true且已回写HPC；先前上限漏项、哈希变化及receipt失败记录保留。本轮权重仅存HPC，未下载到Windows或纳入Git。轻量管理核验通过；任务/模型能力仍未运行，交付后停止。
