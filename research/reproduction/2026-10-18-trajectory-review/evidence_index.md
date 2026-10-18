# Evidence index — saved trajectory review

全部路径以E:\gosc-agentic-teams为根；原始源码387b493、本轮启动ef78565，旧执行48404fd/83338a3；本轮新增源码版本按experiment_manifest.json的SHA固定。本地归档commit见Git和.local输出closure.json。没有新增仿真。

|断言/材料|证据锚点|边界|
|---|---|---|
|本轮授权和先写brief|research/logs/2026-10-18_saved_trajectory_task_brief.md；../2026-10-18-cf-precision/next_stage_plan.md|仅已有轨迹，不含新观测回放|
|原Planner history/旧目标/到达例外|gosc/agent.py:28–43|score含1e−12 jitter；不能只看无jitter margin断定所有动作|
|trajectory索引和运动方向|gosc/agent.py:24,45–55|index k在slot k−1运动后|
|ToM softmax及sender/shared/privileged信念|gosc/voi.py:30–57,88–103|代理expected utility，不是未来task reward；原oracle也不含history策略|
|EVID同时更新共享belief及sender公开位置|gosc/simulator.py:130–146|不能把EVID干预解释为单纯belief改变|
|先sensing/plan后UL，融合后运动；终止slot不运动|gosc/simulator.py:214–294|next plan在t+1，不是fusion即时重规划|
|ACK/queue mutation及estimate clipping/ps|gosc/schemes.py:363–395,407–497|尝试成本相同不代表delivery/DL/未来成本相同|
|当前attempt tape与shadow|extensions/counterfactual.py:76–132,135–210|shadow拷贝plan RNG且只诊断，不更改当前target|
|next context/trajectories/result保存粒度|experiments_ext/run_receiver_cf.py:90–135|仅next-plan有context，之后没有完整逐slottarget/belief/packet流|
|只读review/无pickle与无simulator调用|experiments_ext/review_saved_receiver_trajectories.py:1–20,155–278|只用stdlib，输出全新.local目录|
|轨迹重叠比较、receiver ID对齐、到达例外、attempt成本|同文件:36–130；tests_ext/test_saved_receiver_trajectories.py|7项合成日志契约实际通过，不是仿真复测|
|全部点/配对完整与旧R32回归|同文件:183–216；point_matrix.csv、paired_chain.csv|14点/448对/8world，非448独立世界|
|94集合不一致、118无目标差但任务差、36路径差但任务相同|summary.json；independent_audit.json|事后描述，不是中介因果/显著性检验|
|案例规则及三条具体证据链|同文件:134–145,228–242；cases.json|事后极值点及最近均值rep；正点rep为零效果仍保留|
|首版误比较delivered/DL成本失败及修复|failed-review.log；implementation_repairs.json；contracts-v2.log|检查器错误，不是旧仿真公平性失败|
|原R32均值/CI与原严格R4状态|../2026-10-18-cf-precision/report.md、statistics_by_R.json|只引用历史结果，不当本轮新增推断|
|文献边界|../2026-10-16-mechanism/prior_art.md|GOSC p5/p9、ToM2C p5–6、BANDMAS p3–4；本轮未重读PDF/查新|

## 可重建方式

保存原两个raw根及其hash索引；在本机**尚不存在**的独立目录执行review_saved_receiver_trajectories（具体命令见command_ledger.json）。review只读JSON，不需要加载pickle或调用任何Simulation。新review的输出先用output_hashes.json核验；数值可用independent_check.py独立复核（该脚本的固定路径面向本次输出，迁移时仅改root/run路径并另存新审计，不能覆盖旧审计）。

独立核查脚本不导入review函数，不调用仿真；逐448对重建receiver ID集合和轨迹首差，以不同循环方式复核统计及14点均值。它不验证未记录中介，也不将总条件效应拆解为hysteresis/private/time的独立效应。保留exact source hashes与全部失败/零/负结果，不靠手工修改表格重建。
