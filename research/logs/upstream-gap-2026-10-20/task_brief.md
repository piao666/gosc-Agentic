# Research Task Brief — 上游缺口与C历史差异并行核查

用户2026-10-20授权：等待现有全阶段队列时并行查询frontier/where历史差异及1000–1079校准材料缺口。

科学问题：公开材料是否包含遗漏的校准脚本/候选/过程，历史版本/平台/依赖/随机流是否能解释既有差异？
方法：只读检查官方GitHub当前branch/commits/tree/releases/issues/Actions及全部可达历史的文本；查论文与NumPy/Python官方兼容契约；精读既有受控诊断的闭合证据和代码路径。使用现有已完成run证据，不在本地运行仿真/统计，不新增HPC worker挤占现有2CPU队列；无需重复整批复验或更换环境。
文件：仅本地research/logs/upstream-gap-2026-10-20新证据及research/reports/upstream_gap_investigation_2026-10-20.md，必要的后续诊断设计单列，不修改gosc/experiments/results/原失败或运行源码。所有新增研究文件暂留本地；有running队列时不得源码上行。
成本：网络与轻量文档/文件/Git哈希读取，无新模型/依赖/收费API/训练或GPU任务。
验收：每条结论带来源/日期/范围；明确负检索范围与接口限制；浮点敏感性不冒充全部历史根因，作者平台的计时说明不冒充完整数据环境清单；缺失校准不以自创脚本补称原作者流程。保留现有队列继续运行。
