# Research Task Brief — T3-R-v2-I

2026-11-25，Asia/Shanghai。基线458a96f59b620a02e6872d038b87912eb39e92e4；research/progress-audit-2026-10-19。用户已接受静态候选、D1余池保护及探索门槛，本轮明确授权独立最小实现、HPC无模型验收，不授权真实生成/题目/部署/新数据/Git提交推送。

- 科学问题：[HYPOTHESIS] 公平终答的应用及执行保护是否符合C01–C32工程合同？不评价模型能力、内容收益或无线净收益。
- 前提：四份v2审查文档及AGENTS完整阅读；旧源码/默认行为/评分、registry和历史No-Go保持。
- 修改：仅新增fair_final_v2协议/保护/评分模块及固定Prompt资产、专用tests、合成压力/合同/独立审计入口、新预算/验收报告/日志。复用PrivateView、ControlledClient、wire和持久Ledger；不修改旧模块。
- 信息：夹具只用red/blue/人为哨兵，不读原四题正文/gold，也不读取或选择余52记录。registry只可核SHA，不解析其内容。
- 实施前语义：null与空文本分别记empty_null/empty_response；null仅在己方字符串历史显式表示为空串，原始JSON保留null。全串格式失败含非法E/占位A都不修复；known usage正常结束消费slot继续。原始UTF-8输出>65536B或HTTP封装>512KiB为安全失败，停发；规范化（仅CRLF→LF、外侧ASCII空白）>4096B为格式失败，原始文本不截断并保留己方历史，下一输入超64KiB则停发。Unicode编码异常停发。占位A依原规格三个字面词及离线normalize为空判定。格式不合格不借标签修复或增请求。
- 合同：逐项C01–C32，边界、崩溃、usage、时间、quota、回传、来源/终答旁路及冻结字节；独立审计不得通过导入生产parser/评分自证。
- 成本：见先冻结的model-free budget；所有项目测试/压力/审计仅HPC，GPU/真实HTTP/实际模型调用均0。失败run保留，不超过累计预算。
- 当前阻断：HPC HEAD b05ea73且索引大量旧暂存删除；本地458a96f。已请求备份后仅对齐Git元数据的处理方案，未获答复前不改HPC Git/源码、不开始测试。本地三项用户untracked原样保留，既有授权继续有效。
- 验收：实现支持域、32项实际断言/结果、压力/持久计量、原行为/源SHA、每run日志/失败/独立审计/完整回传；区分实现、无模型验收、真实部署、科研能力。结束后停止，Git另批。
