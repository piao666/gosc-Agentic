# Evidence index

- [PAPER] D01 exact v1：PDF path/hash/page labels in GOSC_paper_code_map.md；原文只读，本轮无出版状态新断言。
- [CODE] 5式/Algorithm/双构造路径与5图13表：research/logs/GOSC_paper_code_map.md，HEAD876fc52。
- [RUN] 405个印刷单元/原8表匹配/补VI匹配：research/sync/runs/hpc-paper-audit-20261019/outputs/audit_summary.json 与 *_comparison.json；原始参照为research/reproduction/paper_table_references.json。
- [RUN] 25默认字段、消息长度与6冻结点：同一run outputs/static_and_frozen_checks.json。
- [RUN] 37/38候选与100个eval seed：research/sync/runs/hpc-r4-preflight-20261019/outputs/r4_preflight.json。
- [HYPOTHESIS/PLAN] 60条pilot与完整R4：research/protocols/r4_protocol_v1.md、r4_plan_v1.json，未执行。
- [RUN] 文件完整性：两个run outputs/input_integrity.json、artifacts.json与最新receipts；最终管理核验verification.json。
- 版式与科学解释差异：research/reproduction/figure_table_audit_2026-10-19.md。
