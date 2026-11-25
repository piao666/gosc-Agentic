# T3-R-v2 静态审查任务入口

2026-11-25，Asia/Shanghai。本目录仅新任务文档/非私有元信息，没有真实题目正文或新实验结果。

| 交付 | 内容 |
|---|---|
| [公平终答规格](../../protocols/masbench_t3r_v2_fair_final_spec_v1.md) | 字面Prompt、输入、六slot、全串MESSAGE/FINAL、异常、信息边界与评分向量 |
| [D1与预算审查](../../reports/masbench_t3r_v2_d1_budget_review_2026-11-25.md) | 数据方案代价、模型pin、token/468 HTTP/19100s与资源/回滚/回传候选 |
| [合同矩阵](../../protocols/masbench_t3r_v2_contract_matrix_v1.md) | 现行函数/行范围、32项未来无模型合同、停止门风险；未执行 |
| [实施前决定](../../reports/masbench_t3r_v2_preimplementation_decision_2026-11-25.md) | Conditional Go的支持域、运行Blocked与科研层次 |

| 附件 | 来源/解释 |
|---|---|
| task_brief.md / task_log.md | 授权、科学问题、命令与失败、变更和停止 |
| source_inventory.json | 指定输入与实际执行源码SHA；历史T3快照身份及九项LF源码绑定 |
| git_identity_check.json | 本地HEAD、GitHub只读ref比较；CLI网络失败与连接器fallback，未push |
| d1_existing_aggregates.json | 既有HPC preflight的data字段投影；无新分组计算/排序/选题/正文读取 |
| prompt_contract_hashes.json | 仅规格内System字面模板、两角色替换与公共六项时钟的UTF-8/SHA；不实例化题目、不计token |
| closeout_checks.json | 本地轻量路径、Markdown引用、源SHA与tracked文件保护检查；不是研究测试 |
| delivery_manifest.json | 本轮新增文件逻辑大小/SHA，清单本身不回填自哈希 |

历史证据入口仍是[旧T3-R审计目录](../masbench-t3r-2026-11-25/README.md)，684原件仍在HPC原目录。本轮不重新扫描684正文、不下载私有读稿、不生成新CI/统计结果；旧四题曝光及原No-Go保持。所有新版固定向量仅人工给预期，不能以附件完整性检查代替无模型验收。

最终停在文档审阅。未执行新模型调用/测试/部署/实验/训练，未提交或推送Git。
