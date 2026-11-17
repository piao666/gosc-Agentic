# Research Task Report

2026-11-17 Asia/Shanghai。当前结论：隔离C++17/CGO及词表helper构建通过；最终离线合成合同通过，前两失败保留。真实部署绑定仍未验收。本报告优先于11月16日较早的“helper尚未构建”快照。

- **Research Question / Hypothesis**：[HYPOTHESIS] 固定部署版本的模板与词表能否构成可审计的离线计数候选，并使现有客户端在派发前拒绝窗口溢出或不支持的消息结构？本轮不检验任务收益。
- **已核验前人工作**：[CODE] Ollama v0.11.11/commit `92b96d54efd6b49322b7cf046f9a0dc16b00cd0a`，词表only与 `Tokenize(false,true)` 路径、模板执行、ChatHandler默认system插入规则；[PAPER] 本轮无新增论文结论，原GOSC科学复现缺口及G1/GP-ID No-Go保持。
- **实际阅读源码**：[CODE] 固定 `llama/llama.go`、`template/template.go`、`server/prompt.go`、`server/routes.go::ChatHandler`；后者固定源码SHA为 `12d2889140fc0c84162bf7fe9fd84848670aed34caf1c1200631349cfbab3c8c`。现有 `extensions/masbench_reasoning/client.py::ControlledClient.generate` 只支持首条system，后续只能user/assistant；本地对HEAD的文件差异检查为0。
- **本轮新增或修改**：`experiments_ext/masbench_cpp_vendor_prepare.py` 固定vendor与编译器归档；`masbench_cpp_vendor_build.py` 隔离工具链/ABI/helper；`masbench_context_counter/main.go` 词表模板候选；`masbench_context_offline_contract.py` 默认system、独立renderer、实际客户端fixture准入与资源约束；`research/protocols/masbench_cpp_vendor_*` 保存具体范围与用户授权；日志目录 `research/logs/masbench-cpp-vendor-2026-11-16/` 保存失败、恢复、源码参考和无损压缩证据。`.gitignore` 排除管理patch的gzip原始产物。
- **实际运行**：[RUN] 全部项目构建/合同在HPC n1登记。本地只编辑、Git/文件哈希与同步。恢复后核UID8301880、2CPU/24GiB，helper SHA仍为 `e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5`。新源码同步 `20261117T024911Z`，1020文件、0 SHA差异。命令见下表；无mission/seed/真实题目。
- **测试与结果**：[RUN] vendor目录4文件5,268,882bytes，4个Git blob/3个tree一致。官方Zig0.17.1归档57,411,036bytes、SHA `3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a` 校验通过，展开常规文件374,407,381bytes；9份显式许可证文件保存，完整原声明保留。C++17 filesystem/string与Go CGO合同及helper构建200.900348s、exit0。最终离线run **1.005240s、exit0**：14渲染、36窗口边界、6schema拒绝、4special-token锚点；这是有界工程合同，非60个pytest项目或统计独立样本，CI不适用。
- **失败/负面证据**：[RUN] 原5次Go/helper失败保留；C++归档准备前4次失败/主动中断、v5成功。离线首轮0.190880s在默认system manifest的摘要前缀格式处失败：应为 `sha256:`，误用了文件名的 `sha256-`；仅修正前缀，摘要与模型不换。第二轮0.778828s在错误的fixture期望处失败：多system属于renderer域，但不属于受控客户端schema。保留14个渲染用例，把2个越域用例×3组合明确统计为6个schema拒绝；不修改客户端来放行，也不把它们计为窗口通过。日志和原始输入/输出均保留。11月17日恢复曾三次SSH超时，用户恢复连接后核身份再继续。
- **与原 GOSC 的差异**：仅实验准入/计数基础设施，无value estimator、调度器、信道或新方法训练改动；不增加科学收益主张。
- **公平性与泄露检查**：D1文章隔离决定保留，registry/真实题目未改。全部合成；仅固定GGUF词表加载，日志 `vocab only - skipping tensors`；无tensor推理context、无GPU/HTTP/真实模型生成。窗口测试使用明确虚构的内存backend/零manifest fixture；真实Qwen `ContextBinding.verified` 仍false。独立renderer不是独立tokenizer，两个helper输出的比较也不冒称部署独立等价。
- **成本**：[RUN] 新构建采样临时文件峰值1,468,595,060bytes、进程组RSS670,670,848bytes、临时文件与进程合计2,011,885,643bytes，低于批准上限；采样不是瞬时硬限制证明。三次离线登记执行合计1.974948s，低于120s执行额度；三次之间有人工诊断间隔，不是连续120s自然时间窗。离线产物及采样RSS见最终contract与回执。CPU最多2，模型生成tokens/channel uses均无新增。用户批准后7份管理patch无损压缩释放366,419,761bytes，7份本地未压缩原件及HPC恢复侧车保留；真实Git索引未改，后续使用独立临时索引。
- **可否进入下一阶段**：离线候选 **Go（限已测合成域）**；真实部署/有效context/无截断/服务取消/空闲恢复 **Pending**；B1真实任务仍Blocked，正式test/训练及原科学No-Go保持。
- **用户需要批准的下一步**：若继续模型部署验收，按已有[具体部署提案](../benchmarks/masbench_real_deployment_acceptance_plan_2026-11-16.md)另核服务配置/模型加载/合成生成权限。当前构建授权不包含这些操作；1024是此前服务核验值，32768仍是未验证候选。临时目录在/tmp，复用前重核存在和SHA，不擅自重下载。

## 实际登记入口与证据

以下命令在HPC项目根目录执行，环境 `GIT_INDEX_FILE=/tmp/gosc-snapshot-index-916289b-20261116`；标准运行清单保存完整命令/同步/Git/资源字段。

| run目录（research/sync/runs/下） | 实际入口 | 结果 |
|---|---|---|
| hpc-masbench-cpp-vendor-prepare-v5-20261116 | `scripts/hpc_runs.py run ... -- {python} experiments_ext/masbench_cpp_vendor_prepare.py` | 216.098090s完成，仅归档检查 |
| hpc-masbench-cpp17-helper-build-20261116 | `scripts/hpc_runs.py run ... -- {python} experiments_ext/masbench_cpp_vendor_build.py` | 200.900348s完成 |
| hpc-masbench-context-offline-contract-20261116 | `scripts/hpc_runs.py run ... -- {python} experiments_ext/masbench_context_offline_contract.py hpc-masbench-cpp17-helper-build-20261116` | 0.190880s失败 |
| hpc-masbench-context-offline-contract-v2-20261116 | 同入口，独立run ID | 0.778828s失败 |
| hpc-masbench-context-offline-contract-v3-20261117 | 同入口，独立run ID | 1.005240s完成 |

最终证据：[状态](../sync/runs/hpc-masbench-context-offline-contract-v3-20261117/status.json)、`outputs/contract.json`、`outputs/synthetic-counts.json`、`outputs/synthetic-effective-inputs.json`、`outputs/client-boundaries.json`、`outputs/helper-stderr.log`。构建证据为对应run的 `outputs/build.json`、`abi-run.log`、helper/deployed build-info；一个弃用警告保留，不写成无警告。标准 `python scripts/hpc_runs.py pull` 校验回传内容，最终回执另见本报告完成记录。

## 完成记录

[RUN] 最终[回执](../artifacts/context-deployment-20261117/receipt_index.json)：4320份运行通道文件清单，新增下载24,003,800bytes，`all_outputs_mirrored=true`；该4320是全历史通道清单，不是本次新实验数。最终合同采样进程树RSS77,983,744bytes，helper合同内部0.682568s，外层登记1.005240s，两者作用域不同。默认system补入用例为8、10、13（零起始）。

[CODE / 本地管理] `git diff --check` 检查本轮已跟踪修改通过，仅有Git自动换行提示；project_status.json可解析；实际客户端与HEAD无差异。源码/文档已更新，未Git提交/push。模型/服务验收没有因本轮成功自动放行。
