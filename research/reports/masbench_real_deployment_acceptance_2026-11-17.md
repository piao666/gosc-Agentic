# Research Task Report

2026-11-17 Asia/Shanghai。**真实服务有限域检查已完成：32768窗口、两组完整渲染、长输入计数与自然结束、断连后的卸载清理通过；原生断连即时取消和生产Driver绑定仍Pending。** 服务默认配置已恢复1024，当前无驻留模型。不能将这次临时32768验收当作已永久部署32768。

- **Research Question / Hypothesis**：真实Ollama能否在配置窗口内保留完整合成输入，离线prompt计数是否与实际V1一致，断连后清理能否终止原runner？不检验任务收益或科学创新。
- **已核验前人工作**：[CODE] 固定Ollama v0.11.11源码中的ChatHandler、chatPrompt、`_debug_render_only`/`_debug_info`和空messages卸载路径；[PAPER] 本轮无新增论文结论。沿用既有GOSC/GP-ID/G1的科学No-Go，不因工程验收改变。
- **实际阅读源码**：[CODE] `scripts/hpc_ollama.py::settings/start`；固定 `server/routes.go::ChatHandler`、`api/types.go::DebugTemplateResponse/DebugInfo/ProcessModelResponse`；既有独立helper/离线入口。debug字段执行前按固定源码核对，避免误作生成。
- **本轮新增或修改**：独立 `experiments_ext/masbench_deployment_acceptance.py`；[任务Brief](../logs/masbench-deployment-2026-11-17/task_brief.md)；本报告及进度索引。算法、任务registry、原客户端及历史结果未改。原工作区已有本会话修改全部保留，无reset/checkout/clean或Git提交/push。
- **实际运行**：[RUN] 用户明确要求“进行真实部署验证”，按已有480s具体方案执行，未重复索要已给授权。HPC n1/UID8301880、2CPU/24GiB、L40；run `hpc-masbench-real-deployment-20261117`，2026-11-17 **11:18:48–11:19:27 +08:00**，外层39.725243s、exit0。Python为项目既有venv；manifest/template/system/helper摘要核验。qwen2.5:7b，manifest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`，无模型下载或真实题目。
- **测试与结果**：[RUN] 初始ps空/GPU0MiB；原服务PID8964/default1024。临时服务PID37337/default32768，实际驻留API报告 `context_length=32768`、固定digest匹配。两组debug渲染与离线完整字符串逐字节一致，含多轮长输入；长输入离线及V1 usage均 **2443 prompt tokens**，大于1024。正常请求max16，实测生成2 tokens、正文 `OK`、finish_reason=`stop`、total2445，未发现所测输入被裁剪。不是任意输入的普遍无截断证明。
- **失败/负面证据**：[RUN] 本轮run正常退出；启动前一次管理入口路径不存在，未执行HPC/模型，随后改为只读SSH核实；保留命令错误，不伪称首轮管理入口成功。`runner_context_args=[]`，未从命令行取得独立ctx-size证据；实际窗口依据驻留运行时API。没有活动sequence/原生idle直接观测接口，因此 `native_immediate_idle_verified=false`。取消流只保存动作观察与后续清理证据，未落盘原始SSE chunk，也无最终usage；不重构/编造取消请求的最终tokens。
- **与原 GOSC 的差异**：仅实验部署准入检查；无value估计器/调度器/信道/训练修改。两次真实生成均是合成部署检查，不能混入任务成功率或四题结果。
- **公平性与泄露检查**：D1保持，真实题目/任务0。所有输入均合成；第一组短输入，第二组长历史明确保存。已有2 debug/2 generate预算分开记账，不借用四题98次额度。尚未接入生产Driver，`production_driver_binding_verified=false`；独立token IDs全域等价也未证明。
- **成本**：[RUN] POST共5：debug2、generate2、unload1；run内GET10，前置/收尾管理额外GET各1，合计GET12≤40。正常输出2 tokens；取消请求预留max512不退款，实际生成数未知。进程树RSS采样峰值5,216,960,512bytes，GPU实际使用采样峰值8,680,112,128bytes，各低于16GiB采样门槛。驻留API的size_vram是8,905,867,264bytes，属于另一指标，非采样峰值。CPU配额2；采样不等于内核瞬时硬限制。执行39.73s低于480s；内部350s即停新测试派发，为原420s截止的更保守实现。
- **可否进入下一阶段**：所测临时32768窗口/完整渲染/正常计数 **Go（有限域）**；断连后**卸载栅栏Go**；**原生直接取消Pending**；真实B1/生产Driver、正式评价/训练均未放行。当前服务已恢复1024，不能直接发送这条2443-token请求。
- **用户需要批准的下一步**：下一实现关卡是把同源计数、服务身份和取消后卸载栅栏接到真实Driver，并形成其独立合同。若要让B1真正使用32768，需要明确持久服务配置及对应预算，不沿用本次临时设置冒充已生效；真实四题仍需独立范围与预算。该建议未自动启动新生成。

## 取消和恢复证据

[RUN] 暖模型后，第二个V1请求以stream方式开始合成整数列表，观察到content且未观察到结束标志后主动关闭连接。随后空messages/keep_alive=0卸载返回 `done=true, done_reason=unload`；ps空、原runner **37396**退出。这证明清理栅栏后的停止，**不证明卸载前仅断连即可立即idle**。

[RUN] finally恢复原环境中的服务默认1024、单并发1，恢复PID **37483**。随后独立只读核实：可执行文件仍为原0.11.11、`OLLAMA_CONTEXT_LENGTH=1024`、`OLLAMA_NUM_PARALLEL=1`、ps空，`/proc/37396`不存在。原环境仅在进程内用于恢复，没有把完整环境/凭据写入产物。只记录白名单服务元数据。

## 实际命令与原始证据

源码SHA同步 `20261117T031555Z`，1023文件、0差异。HPC执行：

```text
GIT_INDEX_FILE=/tmp/gosc-snapshot-index-916289b-20261116 .venv/bin/python scripts/hpc_runs.py run --run-id hpc-masbench-real-deployment-20261117 --kind test --stage real-context-cancel --purpose user-requested-synthetic-real-deployment-480s-temporary-context-rollback -- {python} experiments_ext/masbench_deployment_acceptance.py
```

[RUN] [运行状态](../sync/runs/hpc-masbench-real-deployment-20261117/status.json)、`outputs/acceptance.json`、`inputs-and-counts.json`、`debug-0.json`、`debug-1.json`、`loaded-model.json`、`normal-response.json`、`original-service-metadata.json`。后续只读核实见 `research/logs/masbench-cpp-vendor-2026-11-16/deployment_closeout_20261117.json`。生产绑定仍false；不能将fixture或这份结果布尔值直接当通用部署证书。

`python scripts/hpc_runs.py pull` 的[回执](../artifacts/context-deployment-20261117/receipt_index.json)表明已登记产物全部回传，新增24,059,045bytes（含源码快照），`all_outputs_mirrored=true`。4336是全历史通道文件清单数，不是本次实验数。
