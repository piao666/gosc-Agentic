# T3-R 审计附件与复核入口

本目录为2026-11-25新建审计产物；不含684份历史原文、完整私有请求/响应或gold正文。报告顺序：[A](../../reports/masbench_t3_trace_diagnosis_2026-11-25.md) → [B](../../reports/masbench_t3_failure_attribution_review_2026-11-25.md) → [条件C](../../protocols/masbench_t3_revision_gate_review_v1.md) → [D](../../reports/masbench_t3_research_decision_2026-11-25.md)。历史结果和No-Go未改。

## 文件、生成方式与schema

| 文件 | 来源与字段解释 |
|---|---|
| task_brief.md / task_log.md | 范围、授权、竞争解释、实际命令、失败、host、版本与开销 |
| evidence_inventory.json | schema_version=1；HPC inventory登记的逐字节副本。files每项记录期望/实测path、size、SHA、regular/readable、内容类型、时间戳保护；anomalies单列，不能只看总数 |
| episode_trace_index.json | schema_version=1；最终bindings登记的逐字节副本。episodes按原计划顺序；turn从0计；provider_source/response_source/source指原始相对路径、文件SHA和ledger_seq；wire_event_indices为对应wire JSON.events的0基偏移；模型时间与wire slot分属各自时钟 |
| verification_summary.json | schema_version=1；最终bindings登记的逐字节副本。16条旧评分/请求/wire/next-input逐项比较、8组配对、51用量/计数渲染窗口绑定、835/2733链、18栅栏、source bindings、support句覆盖、空响应与终答消息成本；无新增问题N |
| audit_t3r.py | 最终stdlib离线工具。只处理HPC上已有本地文件，不导入应用/客户端、不发网络请求、不执行Prompt脚本；AST读取模板常量；写入仅限新的GOSC_OUTPUT_DIR，O_NOATIME/O_NOFOLLOW保护历史源 |
| hpc_scripts/ + audit_script_provenance.json | 四个登记真实使用的不同脚本逐字节副本，SHA绑定/tmp路径；早期版本不被最终工具覆盖，修订只补审计字段/核对范围 |
| hpc/<run-id>/ | 四次新登记的manifest/status/artifacts/stdout/stderr和选择性非私有outputs。source_snapshot/patch/untracked archive留在HPC原登记目录；不谎称整run全部回传 |
| scoped_receipt.json / bindings_receipt.json | 21+7个非私有登记/产物逐项远端SHA与本地核验，all_run_outputs_mirrored=false为有意不镜像私有读稿及源码包；不是运行失败 |
| receipt_publication.json | 两份receipt在HPC新路径存档并读回SHA核对的双端凭证 |
| local_source_bindings.json | 本地当前九份源码LF规范化SHA与T3执行snapshot一致；不改历史git identity |
| archive_copy_checks.json | Git归档16份小摘要与既有provenance的SHA一致；不是新生成任务数据 |
| collect_t3r.ps1 | 一次性定向回传前三次新登记的管理脚本；拒绝覆盖既有目标。最后bindings使用日志所记等效精确七文件流程 |
| acceptance_matrix.md | A→B→条件C→D逐条支持域、结果、缺口及停止门 |
| closeout_checks.json / delivery_manifest.json | 本地轻量交付完整性核查与新增文件SHA清单；不作为科学实验或pytest结果 |

## 缺项、独立性与隐私

独立性指新工具未导入生产parser/评分/传输优化器，并从同一批原始字节独立复算字符串解析、逐帧CRC/长度/uses与重组、局部memory/board、normalize/F1和账本哈希。**它不是独立实验、独立数据、外部审稿或另一个模型的盲审**；代码事实和主观语义归因仍需用户审阅。

raw response与provider均在原始HDD；索引只存SHA、长度、标签类型、数值用量及定位。`controlled_read_aid.private.json` 只在新HPC traces/context/bindings登记的outputs中，包含四个已曝光家族必要支持句及Q/R/A；没有下载、纳入Git或公开报告。受控语义审阅使用了该摘录，不等于通读所有684文件里的全部重复正文。

support_coverage是“标注句是否逐字存在于本方context”，不是语义蕴涵求解器或信息互补性的证明。L2利用判断和H1–H5结论在报告中人工以证据/反证方式表达，不通过字符串重合率自动宣称因果。未知模型内部理解、空响应根因、通用独立重复性、资源匹配净收益均保持未建立。

本轮模型调用0，原任务/源码/评分/历史结果未改；未Git提交/推送。审阅完成前不执行候选实验。
