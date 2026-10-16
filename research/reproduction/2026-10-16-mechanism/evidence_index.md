# 证据定位与重建

本轮工作目录 `E:\gosc-agentic-teams`；Obsidian `E:\Obsidian\Papers`只读。client date2026-10-16。base及Python/OS/lock等见experiment_manifest.json；完整关键命令/读操作错误与未执行项见command_ledger.json。报告涉及的论文出版状态没有外部核验。

| 结论/材料 | 证据位置 | 类型 |
|---|---|---|
| Planner/proxy/时序/源码行映射 | code_map.csv；gosc源码原commit387b49389385b51c275dc5a22ec1672087edda1d | CODE |
| 四篇相关章节 | prior_art.md；paper_evidence_index.json；PDF hash/页锚点 | PAPER |
| 4页公式视觉核对/全文提取 | `.local/reproduction/2026-10-16-mechanism-v1/papers/` | 本机辅助材料；不提交全文/PDF/页图 |
| 构造反例/复制/队列/RNG/tie契约 | tests_ext/test_counterfactual_semantics.py；完整测试日志 | RUN，不是总体任务性能 |
| 完整测试113通过/99.18s | `.local/reproduction/2026-10-16-mechanism-v1/full-tests.log` | RUN |
| 914条saved诊断的指标语义/秩敏感性 | saved_diagnostic_audit.json；experiments_ext/review_receiver_mechanisms.py | RUN：原结果重分析，不是重仿真 |
| 76项受保护输入原SHA及本轮新代码hash | input_hashes.json | RUN provenance |
| 旧Receiver-D1的23个归档产物/原raw未变 | input_hashes.json；旧`.local/...receiver-v1/closure.json` | RUN保护检查 |
| 新干预/抽样/统计/计费/否证条件 | counterfactual_protocol_v1.md；pilot_proposal.json | HYPOTHESIS/计划，未运行 |
| 旧失败/未定准入 | ../2026-10-15-receiver/report_v2.md；../2026-10-15-statistical/report.md；../2026-10-15-mismatch/diagnosis_report.md | 历史RUN，未改判 |

## 重建（以下为复查步骤，不能冒充本轮新增运行）

既有`.venv`按requirements-windows.lock.txt，repo根运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests_ext/test_counterfactual_semantics.py -q
.\.venv\Scripts\python.exe -m experiments_ext.review_receiver_mechanisms --output-dir .local/reproduction/mechanism-review-replay-NEW-ID
```

第二条要求新目录，存在即拒绝，保护本报告。读取repo内作者saved `results/rev_value_fidelity.json`（或.gz），**不运行** diagnose_value 的 main/point/rollout。审计器还依赖先前baseline盘点的 `.local/reproduction/2026-10-15-baseline-v1/protected_checkout_inputs.json`；本工作站已有。fresh clone缺该本机manifest时，可从本目录已归档 `input_hashes.json` 的 `protected_checkout_inputs` 字段恢复这份纯hash表到该新本机路径（存在时先比对，不覆盖）；这不需要PDF/私有轨迹。正式共享前可把hash输入显式参数化；当前工具的本机先决条件在此披露。

比较新输出与 saved_diagnostic_audit.json 的 records/missions/kinds/protected_inputs；输出路径不同不改变输入。当前 audit 只有点相关和计数，**没有新CI**。CSV/report所示E/I/EI比例和rho均从该JSON读取，未手改实验点。

若需核对文献，使用paper_evidence_index.json的本地路径/hash和物理页；本机bundledPython的pypdf及现有Poppler可解析/渲染。不安装新包，不上传到文档服务。不能把metadata中的arXiv DOI当出版社出版核验。新counterfactual runner尚不存在，pilot不能按本索引误执行。
