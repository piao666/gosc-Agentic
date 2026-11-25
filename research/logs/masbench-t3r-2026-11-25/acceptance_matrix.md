# T3-R 验收矩阵

日期2026-11-25。Go均注明支持域，不构成下一阶段授权。

| 阶段/要求 | 本轮事实及证据 | 结论/缺口 |
|---|---|---|
| 0 规范/权限/来源 | 三份指定文件完整读；用户确认未跟踪文档保护；本地bda/远端b05+T3 snapshot九源码SHA匹配 | Go；远端旧索引不修复，不同步覆盖 |
| A0 684文件存在/类型/路径/SHA/bytes | evidence_inventory每项实际读、类型、SHA、时间戳保护；异常0 | Go；不宣称人工通读684份重复正文 |
| A0 控制链/51请求/18栅栏 | verification_summary，835/2733链、51usage/渲染/窗口/身份、18绑定退出证明 | Go；非新服务验证，原生即时取消仍未建立 |
| A1 16episode/49任务请求 | episode_trace_index中每turn原始provider/client路径/SHA/ledger_seq/帧索引/输入角色/板/终止/评分 | Go；模型隐藏理解/跨时钟精确物理时间不可见 |
| A2 三题早答 | 六条raw有真实A；原生parser即时接受；生效base Prompt要求先交流 | Go；未发现这些A的parser误检，资格门缺失与模型违规并存 |
| A2 有传输无消费 | base4/5、52216/61560bytes；protocol4/15、23876/55680bytes | Go；只能说无本episode后续请求，非内容无价值 |
| A3 Q/R/局部board | Full11条protocol+1条base进入next request；标准R精确去重/来源；F03错误板复用；No-A2A8空响应 | Go；空响应因果根源未识别，非确定性投递bug |
| A4 L0–L4 | A报告区分传输/输入/利用/配对；L4未达 | Go；内容因果及净收益Not established |
| B H1–H5及失败类别 | B报告4家族×5假设支持/反证/未建立/不可识别；七前提表 | 审查交付Go，机制识别Partial；不强推单一解释 |
| 条件C触发 | B已完成，实际存在公共时钟/终答机会与整合风险 | 静态Conditional Go；单一候选，数据/字面Prompt/完整预算待审；未实施运行 |
| D 十问与路线决定 | D报告十问、路线B/A边界及固定状态模板 | 完成；原T3/G1/GP-ID科学No-Go保留 |
| 数据/公平/保密 | gold离线，D1不动，四题保持曝光开发；原文不入Git；定向镜像receipt | Go；不宣称新独立N、CI/显著性或许可扩展 |
| 原件保护及停止 | Git tracked无改动、原684SHA不变、模型0；最终文件核验见closeout_checks | 完成后停止；T4/test/训练/Git仍未授权 |

复核方式：依task_log中的四个登记manifest定位真实命令及原始HDD，再从索引SHA/ledger_seq/帧偏移回溯；工具仅作离线审计，不含模型任务启动入口。再次执行审计也必须新run ID，不能覆盖现有输出。
