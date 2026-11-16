# B1-pre evidence index — 2026-11-10

- [RUN] A/B原件：`research/sync/runs/hpc-masbench-b1-preflight-20261110`，manifest/source_snapshot/status/artifacts与outputs/preflight.json；模型manifest/metadata/实际serve环境/包元数据、冻结registry的D1/D2只读汇总。
- [RUN] C原件：`research/sync/runs/hpc-masbench-b1-safety-20261110`，同结构及outputs/safety_contract.json，stderr保留17个测试逐项结果。无真实HTTP/model。
- [RUN] 两receipt：20261110T030625Z-0a4021、20261110T030748Z-00d31d；执行和回传完成分开记录。
- [RUN] 本地管理：本目录preflight_stdout/stderr及retry、archive_comparison、archive_fast_forward_stdout/stderr、runtime_binary_inventory；management_verification与experiment_manifest不替代HPC原件。
- [CODE] 新源码：extensions/masbench_reasoning/execution_safety.py；experiments_ext/masbench_b1_preflight.py与masbench_b1_safety_contract.py；tests_ext/test_masbench_b1_safety.py。最终代码与安全run源码快照核对，文档在其后完成，不冒充已运行新版本算法。
- [CODE] 旧接口：client.py LivePermit/ContextBinding/ControlledClient/JsonlAuditSink/run_controlled；application.py PrivateView/LocalAgent；wire.py ContractTransport；registry.py graph/build_registry。旧源码未改。
- [CODE] 官方Ollama固定v0.11.11源码及GGUF格式链接见Tokenizer报告；不新造论文引文。本轮未新核验任何论文效果数字。
- [RUN，历史] 11月3日registry/数据/147+5合同与11月2日权重全SHA；10月30日G1 Shadow和10月27日GP-ID负结果。保留版本，不计为本轮重跑。
- [HYPOTHESIS] D1/D2主张、独立统计设计、第二数据集建议、服务配置/计数器/Driver剩余修复均非已验证研究贡献；见四交付。
