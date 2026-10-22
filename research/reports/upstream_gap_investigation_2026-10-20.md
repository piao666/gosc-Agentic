# frontier/where 历史差异与校准材料调查（2026-10-20）

结论：两项问题需要独立处理。近并列调度存在已定位的 1 ULP 敏感机制；作者保存轨迹的全部差异仍未闭环。公开材料中未恢复原 calibration seeds 1000–1079 的选参流程。不得将任一问题标为“复验完全通过”。

## 1. 范围、来源与执行边界

[CODE] 当前工作 HEAD `876fc523b113b3b65e19f0b730f1573ccc2ee17f`，作者上游 `387b49389385b51c275dc5a22ec1672087edda1d`。本轮静态核查 Git 历史、公开 API、源码，以及既有 HPC 诊断输出；没有新增仿真、科学测试、模型训练或作者联系。

[RUN] 新报告与取证文件仅写入本地。HPC 的完整队列使用冻结源码快照，运行中不上传新文档，不改调度器、不改依赖、不重写历史结果。旧分支证据以 Git blob 导出，未 checkout、合并或执行旧分支代码。

## 2. 校准流程公开材料缺口

[CODE] 作者 [公开仓库](https://github.com/frezazadeh/gosc-agentic-teams) README 声明参数在 seeds 1000–1079 固定，报告评估采用独立 seeds。此次 API 和 Git refs 检查覆盖公开 main 的三个提交：初始 `8a66e70`、图表 `9440859`、合并 `387b493`；最新递归 tree 为 89 个条目，未截断。检查时只有 main，无公开 tags/releases/issues/PR/Actions runs，仓库元数据未启用 wiki/discussions；API 原始响应与 refs 输出另存。

[CODE] 三个版本可读源码中找到校准声明与 frozen 参数注释，但未找到可执行的候选网格、选择目标、平局规则、80 个校准 seed 原始输出或选择过程记录。其他 `1000` 命中包括 bootstrap/格式化/队列阈值，不能作为校准脚本证据。此结论限于本轮已检查的公开材料，不推断私人或未发布文件不存在。

[CODE] `experiments/run_revision.py:26` 的 `experiments()` 从 `Config()` 构造固定配置，`:108` 的 `_job` 直接 `run_episode(cfg, scheme, seed)`；frontier/where 不载入校准产物。公开默认参数与原始选参过程是不同证据：前者可执行，后者仍缺失。已完成的公开参数选择与 fresh 验证不能改称恢复了作者校准过程。

因此：原校准缺失限制参数选择过程复现，不能直接解释固定配置下 seed 0 的 83→76 slots 差异。用户已明确该作者仓库为材料来源，本轮不重复索取其他校准路径。

## 3. 已定位的局部数值机制

[RUN] 既有 HPC 输出 `hpc-c-resume-20261020/outputs/trace_divergence.json` 的案例：`c-frontier / gosc_bits / W100/eta0.0 / seed0`。当前 Linux/NumPy 2.4.6 输出 completion=76、UL symbols=29565、bits=22201；作者保存记录为 83、31011、23468。当前输出不能表述为逐 seed 一致。

[RUN] 该案例当前实现与既有 scalar-exp 诊断的首次选择分歧在 decision_index=243：候选结构相同，只有 INTENT rate=1 的 value 从 `0x1.8c39fed9fd617p+2` 变成相邻的 `0x1.8c39fed9fd618p+2`。当前选择 99 symbols 的 EVID；变体选择 72 symbols 的 INTENT。完整候选摘录见 `existing_hpc_trace_excerpt.json`。这里比较的是两次本方诊断轨迹，不是作者逐时隙轨迹。

[CODE] `gosc/channel.py:60–73` 计算成功概率使用 `np.exp`。`gosc/schemes.py:266–305` 的 `lagrangian_select` 先进行严格 `u > best_u` 选择与二分，再按最大 value/symbols 用 Python `sorted` 排序补余量。bits 估值的某些同 rate 选项在实数运算下密度相同；浮点乘除与指数计算产生的细微差异可改变组排序。100 symbols 预算下，INTENT72 后余28，小于 EVID 最小29；EVID99 后余1，小于 INTENT 最小3，最终消息类型因此改变。这是离散决策变化，不能当作输出格式的舍入差。

[CODE] Python 的稳定排序只保证相等 key 保持先后顺序，不能消除相邻浮点 key 的优先级差异。[Python sorted 文档](https://docs.python.org/3.11/library/functions.html#sorted) NumPy 2.0 非稳定排序行为变化不能直接当作本例原因：这里调用 Python `sorted`，纯 Planner 路径也不同于 LLM 候选排序。

[RUN] 已完成、此次仅读取的诊断共36条 mission：24条 default重复/scalar-exp/禁SIMD，12条 NumPy1.26.4/2.2.6 隔离诊断。默认重复稳定，禁SIMD及2.2.6在这些案例中与当前结果相同；scalar-exp改变部分案例，只恢复一条 where/AoI 作者记录；1.26.4改变部分 bits 案例，未恢复相应作者结果。范围为六个案例，不外推到全部 seed。官方项目依赖与主队列保持不变。

## 4. 旧用户分支增加了什么证据

[CODE] 本地 `origin/codex/baseline-reproduction` 指向 `ca0580aaabcd337193b4f96d4d613b372c9b6916`，属于用户历史研究分支，不能冒称作者上游。其已提交的诊断报告、兼容矩阵、首分歧摘录和 manifest 已原样导出到本调查 `prior_branch/`，记录 Git blob 与 SHA-256。

[RUN：历史记录] 旧报告14个 Python/NumPy/操作系统与数值变体没有恢复作者 seed0=83。旧 Linux/NumPy2.4.6 为76/29565/22201，与当前 HPC 案例一致。旧报告也定位 decision_index243，并标记 t40/agent3；本轮 HPC 摘录没有 t/agent 字段，因此该时间/agent定位仅引用旧报告。旧 Windows/Linux 的相关候选 value 亦差1 ULP，支持同一局部机制跨两轮诊断出现。

[CODE] 旧原始目录 `E:/gosc-agentic-teams/.local/reproduction/2026-10-15-mismatch-v2` 及其项目根目录当前不存在，只能重读已提交证据，不能声称重审了所有旧原始 trace。旧分支还删除了两个 summary JSON，不能整体合并来“修复”当前结果；当前原作者结果未覆盖。

[RUN：历史记录] 旧统计报告记录5200条仿真、104项同时区间，其中100 equivalent、4 inconclusive、0 incompatible，整体关卡 Pending/NoGo。其 final_review 的 `status=passed` 指执行与校验成功，附注明确统计关卡证据不足。该修订协议的5%界限、Windows运行和100-seed参考不能追溯套用于本轮 HPC，不能将旧5200条与新运行合并计数，不能把增加 bootstrap 次数当作增加独立样本。

## 5. 源码历史核对的限制与修正

[CODE] 三个作者公开提交的 `schemes.py/channel.py/agent.py/simulator.py` 以及 `results/rev_frontier.json`、`rev_where_tom.json` blob 一致。原 `rev_frontier.json` SHA-256 为 `4c16e142322e66dd69ad22daa2121378e78de40bc0023294e6c2570150ef4302`。

[CODE] 不能据此声称全部核心文件不变：`gosc/config.py` 在最新合并增加25行、13个估值扰动/包开销/共享预算扩展字段；原字段未改，diff 保存在 `config_history.diff`。对上述基础四文件及 environment.py、run_revision.py 的新增字段引用检查均未命中；固定 frontier/where 调用基础 `run_episode`，不能将新增 realistic 字段直接当作这些基础案例差异的解释。

[CODE] 公开依赖只约束 NumPy>=1.24 等最低版本，未提供作者结果生成环境锁文件。README 的8核 Apple M1描述用于运行耗时，不能推断所有保存结果都在该平台生成。NumPy 官方随机兼容说明对可复现性要求相同调用序列、build、环境及机器；同一 seed 本身不是跨平台保证。[NumPy 兼容政策](https://numpy.org/doc/2.4/reference/random/compatibility.html) 这只能界定可能条件，不能证明本例由 RNG 引起。

[HYPOTHESIS] 极近并列的密度选择可能放大跨 build/架构的浮点差异；但尚无匹配作者的环境与逐时隙 trace，无法确认作者全部差异的初始原因、受影响 seed 或各指标影响。不得改为“所有差异均是1 ULP”“全部无害”或“已统计等价”。

## 6. 当前运行、回传与后续安排

[RUN] 2026-10-20 14:47:04北京时间直接 SSH 观察：父队列 `hpc-ordered-resume-20261020` 与 noise 子任务状态 running；noise完成20200/23400，workers=2，子任务 stderr 为空。此为当时观察，不是阶段最终验收。后续仍按冻结顺序推进 overhead、shared、fresh、其余扫描及 cached/live LLM，截止时间沿用原协议。

[RUN] 本地旧回传 PID15732 已退出，状态停留13:14；退出原因未确定。14:47:35以同一既有管理脚本恢复，PID31796；14:47:36状态重新更新。只镜像已结束运行的完整输出与活动任务状态，不获取未关闭的大型输出，不启动科学计算，不改远端源码。执行完成与回传完成分开记录。

当前可完成的公开调查已经收敛，继续维持官方环境与原顺序队列，保留差异，不盲目扩展版本试跑。下一阶段验收逐项检查：任务完成、匹配键覆盖、保存指标一致性、统计口径、输出哈希与回执。

若将来取得作者环境清单（Python/NumPy准确build、CPU/SIMD/系统、源码与配置哈希及未提交补丁）、seed0逐时隙候选/选择trace、原校准候选网格/目标/80seed过程记录，可针对首次分歧进一步定位。此清单只记录所需证据；未发送 issue、邮件或其他消息。

## 7. 本轮产物与检查

- 报告：`research/reports/upstream_gap_investigation_2026-10-20.md`。
- 调查原件：`research/logs/upstream-gap-2026-10-20/` 中的 API、Git历史、refs、旧分支provenance、源码diff、trace摘录、findings。
- 命令类型：`git show/ls-tree/grep/diff/ls-remote/status/rev-parse/remote`；公开GitHub API GET；本地只读文件/哈希核验；SSH只读状态查询；恢复已有回传管理脚本。
- 新仿真/科学测试：0；没有因文档修改追加测试。报告写入及字段检查采用轻量管理核验。历史测试记录不改写为本轮通过。
- 本轮已有未提交文件全部保留。没有提交、推送、修改受保护算法/原作者结果，也没有上传私人PDF或读取密钥。
