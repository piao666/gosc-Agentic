# Research Task Report - ordered remaining reproduction (RUNNING)

- **Research Question / Hypothesis**: 逐阶段重新执行已公开的参数选择、matched-budget估值、现实链路、消融/理论诊断及LLM流程，区分公开材料缺口、实际仿真、缓存回放与live模型调用。
- **已核验前人工作**: [CODE/WEB] 论文源https://github.com/frezazadeh/gosc-agentic-teams，当前main/HEAD387b49389385b51c275dc5a22ec1672087edda1d，与本地保留上游基线一致。当前代码只有校准1000–1079声明，没有可执行校准搜索/过程记录；用户明确以此源仓库为材料边界，登记未提供，不再索取额外校准文件，不伪造原过程。
- **实际阅读源码**: AGENTS、总说明书、README、最近A1报告/issues、全部原实验生成器/选择函数/绘图matched函数、LLMClient/原LLM运行入口、Simulation/result与真实链路成本。
- **本轮新增或修改**: repro_remaining_inventory、repro_legacy、repro_selection、repro_ordered、repro_extra及tests_ext/test_repro_ordered；23阶段冻结计划和日志；本地仅管理回传器位于.local/ordered-follow/ordered_follow.py。原gosc/experiments/tests/results/LICENSE保持不变，未提交/推送。
- **实际运行**: HPC清点完成（新增科学mission0）；HPC35项测试通过，pytest5.54s；独立SSH会话之外启动hpc-ordered-queue-20261019，23个阶段自动依次登记。当前selection运行中，最近已完成3025/26700，这里只记录观察时刻，不冒称整阶段已完成。
- **测试与结果**: hpc-remaining-inventory-20261019、hpc-ordered-tests-20261019已完成并全部回传；原始Pool适配器35测试含并发<=2、超时/失败保留、worker回收、原模拟器等价性、共同世界和禁止fresh参与选择。生产进度由各run/status.json及pipeline_status.json为准。
- **失败/负面证据**: 原校准材料上游未提供；当前未发现Ollama可执行文件/本地11434服务。未来live阶段会再次探测并保留不可用状态，不允许HTTP失败后写成planner成功。当前生产阶段尚无失败记录；不提前解释未完成数据的性能。
- **与原GOSC的差异**: 外层改并行、超时和输出目录，不改算法；原脚本Pool4/8均被外层限制为2。原脚本被复制到本任务.local隔离目录，公共原数据/缓存只读。所有返回job及worker生命周期先写证据，再由原脚本写最终结果；指标不利不触发删seed或重跑。
- **公平性与泄露检查**: public选择0–99，之后冻结再跑3000–3099；原校准seed1000–1079未被自拟流程冒用。严格搜索37/救援38候选，补38搜索独立置后；LLM缓存只允许已有key且HTTP0，live另开空缓存并记录真实调用。
- **成本**: 清点选择26700条；现实候选124400条，不含其fresh、C/扫参/诊断/LLM和补充敏感性。实际2CPU/24GiB，2workers/数值线程1，阶段有单独任务与整阶段限时，全队列72h安全上限而非预测耗时。首阶段已有小批次真实成本，约小时级；整个队列尚未实测完成。无新方法训练和收费API；LLM仅在服务与指定模型就绪后执行。
- **可否进入下一阶段**: 当前第一科学阶段运行中；前序成功后自动进入下一阶段。对源码/超时/结构故障停止依赖阶段；缺失cached/live资源会显式失败记录，独立敏感性仍可继续。不能把本次启动记为已完成P1。
- **用户需要批准的下一步**: 已授权队列在后台实际运行，不需要逐阶段重复许可。当前无需额外校准资料；live服务信息仍待已有服务就绪。新方法训练未被授权或启动。

## 实时与同步证据

- 冻结计划：research/protocols/ordered_reproduction_v1.json。
- 启动：本任务launch_receipt.json；上游核查upstream_verification.json；启动前核验verification_before_launch.json。
- HPC运行：research/sync/runs/hpc-ordered-queue-20261019/outputs/pipeline_status.json。各阶段ordered-<stage>-20261019有独立manifest/status/raw Pool结果、生命周期、Config字典、原结果比较、input_integrity与stage_audit。
- 本地后台回传PID12720，状态.local/ordered-follow/status.json；当前元数据是HPC原字节快照，产物只回传已结束阶段并做SHA256；receipt回写HPC。在途产物不冒称全部同步，all_outputs_mirrored目前false。
- 科学源码在整个队列运行期间冻结；本地补充日志/当前指针在队列结束前不强行上行覆盖远端来源快照。
