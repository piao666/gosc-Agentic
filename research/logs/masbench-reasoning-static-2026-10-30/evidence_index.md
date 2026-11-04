# MASBench Reasoning证据索引

外部源码固定为`BUPT-GAMMA/MASBench@c0301a650db95958924bb080192c09fef39389a5`，访问日期2026-10-30。已读文件的blob SHA、bytes、行数/链接见source_index.json及source_index_supplement.json；源码只读，未下载/集成第三方代码目录。补充读取的包入口只有docstring，首次临时读取失败后重试成功。

| 断言 | 源码/证据 | 类型/范围 |
|---|---|---|
| 私有context/gold与raw的边界 | Reasoning/src/data_loader_v4_mas.py:69–150；run_asymmetric_agents.py:243–282 | CODE；初始化不传gold但controller日志持有它，不保证公共数据绝无捷径 |
| self/peer不同memory、chat roles | Reasoning/src/agents.py:123–187 | CODE；活动实现，不采信注释掉的旧实现 |
| base与protocol交换/首答案 | Reasoning/src/conversation.py:39–215；prompts.py:25–50,115–151 | CODE；truthy parser、MESSAGE fallback、global R板均核查 |
| 共享板不计入原通信word数 | conversation.py:185–202；run_asymmetric_agents.py:26–69 | CODE；不是本轮测得的节省或泄漏发生率 |
| active F1与None分母 | metrics.py:99–174；run_asymmetric_agents.py:313–401 | CODE；无本轮统计运行 |
| first-answer辅助脚本没有修复分母 | Reasoning/script/analyze_first_answer_protocol.py:102–172 | CODE；empty/is-not-None与会话truthy的差异也保留 |
| dataset seed/CLI/resume/覆盖 | run_asymmetric_agents.py:90–241,404–481 | CODE；没有独立split，有放回抽样，输出路径不含mode/seed |
| 默认云端/无显式timeout和retry | Reasoning/api_key_loader.py:119–149；agents.py:169–177 | CODE；未读取用户.env，不泄露凭据，不调用实际模型 |
| 代码/数据许可声明 | 根LICENSE、根README、Reasoning/README:19–27 | CODE/官方声明；模型具体许可尚无当前权重身份可核 |
| 原始数据身份 | Git tree reasoning.json blob9cfc774f5828bb7b811612a16d0f7d209db627d7、11,996,959bytes | CODE metadata；正文、实际题数/唯一性/SHA256未核验，读取失败不冒充空数据 |
| 原文Reasoning范围/评价轨道 | arxiv.org/html/2610.04672v1，4.2/4.3、D.1/E.1、C.3/C.4 | PAPER；C是framework-level，不实施该框架/其他任务 |
| 当前HPC身份/包/服务/配额 | environment_inventory.json、hpc_inventory_stdout.json | RUN只读盘点，2026-10-30T10:13Z；没有HPC科研作业/LLM请求 |
| 历史三个模型manifest当前未见 | model_storage_stdout.json | RUN只读，10:16Z；只查已知路径，不断言服务器不存在其他权重 |
| G1/GP-ID No-Go与保护 | 原native_information_shadow_results、information_calibration_results及冻结73文件 | 历史事实保留，verification.json仅轻量哈希核验 |
| 新传输/本地板/指标/诊断规则 | 三份research/benchmarks/masbench_reasoning_*文档 | HYPOTHESIS设计；无工程验收/能力/效果证据 |

未核验项：全数据schema/来源/重复分组/划分、模型恢复方式/许可/context、独立依赖环境、端点参数/超时、CRC/ACK/CPU与零损伤合同、任务能力/信息依赖/功效N/实际完整预算。不得用上述静态索引替代运行证据。
