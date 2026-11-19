# Research Task Report — T1-A 接线与无模型验收

2026-11-18 Asia/Shanghai。**T1-A 受测合成支持域 Go。** 最终 40 项无网络合同和独立原始证据审计通过。T1 整体仍待 T1-B 真实合成验收和审查。

- **Research Question / Hypothesis**　[HYPOTHESIS] 真实 Driver 的客户端、持久预算、拒绝派发、进程监督和清理恢复接口能否在可控合成故障下共同工作？窗口与计数证据须绑定当次完整消息。服务清理证据不足时应阻断后续派发。
- **已核验前人工作**　[PAPER] 本轮无新增文献主张。此前 24 项 fixture 合同、同源离线 14/36/6/4 合同与临时 32768 服务检查沿用原记录。没有重建 helper 或重跑这些历史合同。
- **实际阅读源码**　[CODE] 本地基线 `d5f5522f99872d7453ef54cce06c9ae941846877`。复用 `client.py::ControlledClient/ContextBinding/run_controlled`、`fixture_driver.py::CampaignLedger/_sandbox`、`execution_safety.py::Ledger/Limits`、`application.py::LocalAgent` 和 `wire.py::ContractTransport`。客户端、历史 fixture 和原应用/传输源与 HEAD 无差异。
- **本轮修改**　[CODE] `extensions/masbench_reasoning/live_driver.py` 接入完整计数、运行身份与证据绑定、预算与清理日志、协作锁和跨 campaign 恢复标记。应用子进程复用旧无网络规则，计数/HTTP 工作进程由外层监督，真实 RPC 需要另行授权。新增 T1-A 合同、独立读档审计和运行记录。
- **实际运行**　[RUN] HPC n1、UID 8301880、CPU quota 2、RAM 24 GiB。HPC Git 从 `916289b` 条件更新为 `d5f5522`。73 份冻结源核验通过，真实 Git index SHA 保持，工作树未被 Git 操作改写。源同步使用临时索引记录管理快照。现存 helper 文件 SHA 为 `e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5`，与已验收身份一致。[对齐记录](../logs/masbench-t1-driver-2026-11-17/reconcile_hpc.json)
- **测试与结果**　[RUN] 首轮 31 项通过，登记因测试自建 symlink 产物而失败。v2 36 项通过并成功登记，加入两提示族路径、配对拒绝和中断后预算恢复。v3 39 项通过，独立审计 v2 通过。审查发现测试以替换模块常量来隔离虚构身份，未由 Driver 自行约束。修正后 Driver 强制虚构模型与 tokenizer 身份，且只接受全零虚构 manifest。最终 v4 **40 项通过**，unittest 5.445s，登记 5.746508s、exit 0，fixture 产物 4,863,881 bytes。独立审计 v3 **0.239605s、exit 0**，核验 400 份产物及六个场景。这属于工程合同，任务效果 N、CI 不适用。
- **失败与负面证据**　[RUN] 首轮 symlink 自建用例确认拒绝后，原失败运行保持 failed。该测试链接移至 `/tmp/gosc-t1a-first-run-symlink` 后恢复回传，后续用例自行清理其测试链接。独立审计首轮产出 `audit.json`，收尾遇 EDQUOT，原 running 状态另存后补记 failed，结束时间、耗时和退出码为 null。四份本轮管理 patch 无损转存，释放 90,647,857 bytes（不含侧车开销），临时原件、HPC 原目录 gzip 和经 SHA 校验的本地 gzip 副本并存。[转存证据](../logs/masbench-t1-driver-2026-11-17/snapshot_reconcile.json)
- **与原 GOSC 的差异**　[CODE] 本轮为 MASBench 安全执行接线。研究算法、任务数据与统计设计无新增结论。D1 标记和既有 G1/GP-ID 科学 No-Go 继续适用。
- **公平性与泄露检查**　[RUN] 测试父进程及子进程继承内核网络禁用，全部使用虚构输入和身份。真实 HTTP/生成/helper 执行及真实题目均为 0。验证 Full 的可见消息进入接收方下一轮，而 No-A2A 的对应请求中缺少该消息。T1-A 的模拟窗口、usage 和卸载回执仅用于检验接线规则。
- **成本**　[RUN] 最终合同与审计各记录 runner 子进程最大 RSS 53,388 KiB，均含登记器子进程。GPU 未使用。单合同入口限制 90s，独立审计 45s。最终合并实验产物低于 16 MiB。不同版本的验证产物单独保留。早期审计收尾失败的时长未知。
- **下一阶段**　T1-A Go 限已实测的工程支持域。真实 1024、真实完整渲染及 usage、服务独占、资源采样和异常清理仍待 T1-B。当前协作锁不单独证明其他客户端排他。控制器退出已测，整个 broker 突然失联后的真实服务恢复尚未验收。原生即时取消未独立验证。
- **用户批准项**　按单独 [T1-B 预算提案](../protocols/masbench_t1b_synthetic_budget_proposal_2026-11-18.md) 审批现有服务的合成调用和本次模型卸载。4 次生成上限、1088 输出 tokens 保守预留、480s。不提前进入 T2 或真实四题。

## 验收矩阵

| 合同 | 证据及结果 | 范围 |
|---|---|---|
| 当前身份和新运行授权 | 真实授权文件缺失拒绝。虚构 transport 只能生成独立的全零模型身份。模型、窗口、render 漂移拒绝。服务协作锁拒绝第二写者 | 合成路径和静态接线 |
| 完整消息与窗口 | C−1/C 允许，C+1 在 HTTP 前拒绝，非法 schema 在计数前拒绝 | 虚构计数和窗口。已验收旧 helper 只核哈希 |
| 账本与额度 | 已持久预留后才调用 provider 接线。重复 ID 拒绝。重新打开保持 deadline 和成本。跨 campaign 恢复标记阻断绕行 | 合成请求 |
| 异常响应 | 模拟 HTTP 失败、length、usage 缺失/不一致保存失败及保守预留。空应答保留原客户端标记 | 合成响应 |
| 取消与恢复 | 自有真实工作进程超时，记录 SIGTERM/SIGKILL。合成服务卸载顺序与 ledger tip 对账。卸载失败保留 fence。未知 usage 保持 null | 工作进程信号真实，模型完成/卸载/runner 观察为 fixture |
| 崩溃与存储 | 应用进程退出保留已开始状态。残留 inflight 在恢复前拒绝。无凭证布尔、重复锁、截断日志、符号链接、配额/审计写入故障均受检查 | 完整 broker SIGKILL、真实服务恢复仍待现场验收 |
| 私有输入与消息交付 | 两提示族的 Full/No-A2A 后继请求不同，配对身份变化拒绝 | synthetic application，真实任务未曝光 |
| 独立证据 | 文件 SHA、两条哈希链与六个选定场景单独重算，校验信号、卸载和令牌额度关联 | 独立实现的证据审计，后续人审仍可复查 |

运行入口分别为：

```text
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --run-id hpc-masbench-t1a-contract-v4-20261118 --kind test --stage T1-A --purpose no-model-contract-fixture-binding-isolation -- /usr/bin/timeout -k 3 90 {python} experiments_ext/masbench_t1a_contract.py
GIT_INDEX_FILE=/tmp/gosc-t1-d5-index .venv/bin/python scripts/hpc_runs.py run --run-id hpc-masbench-t1a-evidence-audit-v3-20261118 --kind analysis --stage T1-A --purpose independent-replay-final-fixture-binding-isolation -- /usr/bin/timeout -k 3 45 {python} experiments_ext/masbench_t1a_evidence_audit.py hpc-masbench-t1a-contract-v4-20261118
```

原始记录均在 `research/sync/runs/`，分别以 `hpc-masbench-t1a-contract[-v2|-v3|-v4]-20261118`、`hpc-masbench-t1a-evidence-audit[-v2|-v3]-20261118` 为目录名。状态、命令、日志及 SHA 各自在 manifest/status/artifacts/source_snapshot 中保存。最终代码快照同步 ID `20261118T034914Z`，1081 文件、SHA 差异 0。

[最终双端回执](../sync/receipts/20261118T035327Z-9a4792.json)记录 5804 份全历史通道清单，`all_outputs_mirrored=true`。逐文件回传较慢，先对本轮七个 run 批量转运并核验 1470 份文件，再由标准 pull 重验全部受管路径和回执。这些数字分别是文件数和工程合同数。

报告首次同步在备份写入处再次出现 EDQUOT。已按上述回执核对本地保留的三份原 patch，再无损转存 HPC 后续管理快照，释放 67,995,945 bytes（侧车另计）。三个 run 的原始管理补丁在本地和隔离临时盘留存，HPC 长期目录保留可恢复 gzip。科学产物与验收结论沿用原始运行记录。见[收尾转存记录](../logs/masbench-t1-driver-2026-11-17/snapshot_closeout.json)。
