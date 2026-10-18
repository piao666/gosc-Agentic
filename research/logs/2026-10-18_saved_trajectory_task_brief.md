# Research Task Brief — 已有轨迹机制断点审查

- 授权：用户批准2026-10-18精度报告next_stage_plan.md，仅分析已有14点/448对轨迹；不新增仿真、checkpoint回放、world、模型或数据划分。启动HEAD ef78565f78ac095d4bb11c1f6dcb8b4c21752a42，工作区clean；AGENTS、说明书、README、最近日志及未决风险已读取。
- RQ：[HYPOTHESIS] 原生已选消息的代理估值与真实下一次receiver目标变化、后续轨迹分叉及任务/成本的联系，能否从现有日志中识别？不能识别的中介变量明确缺失。
- 前人成果：[PAPER] 沿用2026-10-16文献证据卡中GOSC p5 Eq4、p9 §V-D已有代理估值/反事实诊断；[RUN] R32共896 branches/448 pairs、8开发world，任务均值+.63867且探索CI跨零，标签精度与稳定缺陷仍Pending。
- 文件：只新增experiments_ext/review_saved_receiver_trajectories.py、必要的tests_ext契约、独立research/reproduction/2026-10-18-trajectory-review目录及本任务日志。不写旧raw/报告/core/results/cache/Obsidian。
- 设计：先核验旧/新raw与保护文件SHA及日志schema；只用JSON/JSONL/CSV，不反序列化pickle、不调用Simulation/Planner/Channel。全14点矩阵与448对审计保持。比较shadow/真实next-target、每agent轨迹首分叉、配对完成时间/false declarations/记录无线uses；“目标未变”不等于无信息效应。
- 案例规则：数据已曝光，明示事后illustration；正例选R32均值最大、负例最小、近零例绝对均值最小，平局按point_id字典序。每点选择配对DeltaT最接近该点均值的rep，平局取小rep；不是置信标签/代表性检验，所有点保留。无对应符号时报告缺失，不换规则。
- 边界：已有日志未逐时隙保存目标/动作分数/消息/信念/随机流draw，不能推断后续第一个目标变化时刻、迟滞/私有信念/后续信道的独立因果贡献。先核验再报告具体可识别程度。
- 成本：单进程只读JSON和统计，预计数秒至1分钟；契约测试仅合成小数组，不跑完整仿真测试。无GPU/LLM/API/安装/下载；助手tokens未计量。新机制回放、参数消融、训练或增加数据均超范围。
- 反例/验收：消息可改变目标但任务不变/变差，也可当下目标不变而后续轨迹改变；两者均保留。输出可重建全点矩阵、案例证据链、可观测/同步/oracle变量清单、简单对照与可证伪条件、精确缺失项和下一步协议建议；不把相关/事后分组称因果机制检验。完成后停止。
