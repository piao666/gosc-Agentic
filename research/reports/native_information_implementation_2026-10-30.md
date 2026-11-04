# Native-Information最小Shadow实施报告

后续合同状态（2026-10-30，单独授权任务）：[最终519项HPC回归通过](native_information_contract_acceptance_2026-10-30.md)，工程合同Go、最小机制诊断仍未授权。以下为本报告撰写时的实施快照，其“未运行/Pending”保留历史时点含义；生产实现未改，仅补3个测试边界后另立run完整复测。

基线：`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`；日期2026-10-30。用户授权“开始进一步的实施”，本轮落实代码与合同定义，保留此前“诊断不自动批准运行”的边界。**实现已写入，全部新增项目测试/prepare/Shadow/审计/计时均未运行，不能称工程验收通过。** 已验收静态规格和审查报告保持原字节。

## 本轮实际实现

| 文件 | 实施内容 |
|---|---|
| [native_information_value.py](../../extensions/native_information_value.py) | 不可变局部Context；严格字段/记录身份/传感窗口/数值检查；G0、固定β1/2区域核G1、确定性空间打乱；仅EVID估值钩子。不可通过Context读取world/peer私有状态/随机事件 |
| [native_information_observer.py](../../extensions/native_information_observer.py) | 从初始化开始的自身生成/自收到证据账本、真实admission守卫、独立Public-ToM/BF被动宿主、每sender前8个EVID入口、稳定catalog/原始值/成功率/实际payload/本地历史SHA绑定。没有安装G1在线控制器 |
| [native_information_shadow.py](../../extensions/native_information_shadow.py) | 宿主结束后同快照重选；G0/G1/打乱/同次EVID统一尺度、原生age/显式price、EVID-age/周期门控、单prefix限制、独立WirePeriodic参照；三层排序与最终选择分解；独立重建/候选+BF计时 |
| [audit_native_information_shadow.py](../../scripts/audit_native_information_shadow.py) | 不调用生产评分函数的scalar G0/G1/打乱复算；原始行SHA、确定性first-eight覆盖、独立整数预算/组/成员/payload签名检查；另外重放既有BF与生产rank逻辑，不冒称独立优化器 |
| [repro_native_information_shadow.py](../../scripts/repro_native_information_shadow.py) | HPC UID/绝对路径/hpc_runs登记守卫；已通过合同与源码/配置SHA冻结；单独授权文件绑定；120s alarm/32MiB cap/产物排他写入；失败原件保留；无自动运行入口 |
| [native_information_shadow_v1.json](../protocols/native_information_shadow_v1.json) | 明确implementation_authorized=true、diagnostic_execution_authorized=false；两已曝光cost world、24slot、最大96快照、6个有限price点；无校准/效果N/训练/正式test |
| [test_native_information_shadow.py](../../tests_ext/test_native_information_shadow.py) | G0原TV、只读输入、字段越权/非法值、回退/界限/抵消/饱和溢出、证据身份/观察中性/零DL/同wire/标量审计篡改拒绝/运行授权/冻结身份/输出上限等合同定义，**未运行** |

[CODE] 新增文件隔离于旧GOSC、native、GP-ID/BF及默认策略；原`gosc/voi.py`、`schemes.py`、`realistic.py`、native wire/适配/服务、BF-selector等既有文件不改。仅定义新估值器与纯Shadow重选，宿主仍执行原Public-ToM/BF。

## 科研与权限边界

1. [CODE] G0/G1仅以局部Lc为基准，加入原FIFO前缀增量；不把pending_llr或queued_llr叠入。真实入口还要通过own-history不相交检查；未知、重复、冲突与outstanding均拒绝，不扣Lc/删FIFO修复。
2. [CODE] 主轴只改EVID值，CONF/INTENT值与结构验证保持。全组Native-Age与全局price是明确的强门槛参照，原WirePeriodic是独立选择器参照，不能宣传它们与纯EVID主轴所有控制完全相同。
3. [CODE] 诊断主问题限定为固定菜单中、**声明的有限price/尺度对照**下能否产生内容级选择差异。G1非比例且有相关prefix排序翻转、最终双方都选EVID但prefix不同，仍需排除声明控制复现选择；不能证明所有动态price函数均无法等效。
4. [CODE/HYPOTHESIS] 当前不做C_norm/C_select，G0/G1只按原始共同单位、alpha1诊断。跨ToM的替代选择明确标未校准，不比较任务优越性。未来任何任务效用验证仍须单独校准/冻结/授权。
5. [CODE] 正反宿主先完成，再处理Shadow；观测中性核对完整非计时result、服务事件、物理随机场指纹与最终局部/自身队列状态，选择process_time单列。外层全状态哈希只用于审计，不传评分器。
6. [CODE] 任何正向输出都不放行训练/正式test/任务效果。机制区别否定或覆盖不足按No-Go/Pending输出，不扩大world、slot或模型挽救。

## 将来执行入口的关卡（本轮没有执行）

首先单独获准并在HPC经hpc_runs运行新合同与旧回归；runner的prepare要求完整无failure/error/skipped的JUnit、至少485项、关键新旧合同名称与每个源/配置的测试时SHA匹配。现有旧485运行不含新代码，不能直接复用为通过证据。

prepare只冻结身份，不运行仿真，也不是运行授权。run必须显式提供frozen文件与**另行批准**的授权JSON：scope、approved=true、frozen/config SHA、120s/32MiB及human_authorization_record全部匹配。仓库没有创建已批准授权文件，不通过修改计划中的false绕过关卡。本轮不连接HPC、不源码同步，也未生成freeze或任何run ID。

未来运行需要先按AGENTS核验远端Git身份/配额/环境、同步SHA/活动任务；HPC上次归档身份不能自动假定已更新为014b85d。本报告给出的120s/32MiB仍是未经实测的提案，预算不够就停止，不自动扩大。

## 当前验证与尚未消除的不确定性

[RUN，本地管理] 已做源码文本阅读、Git差异/受保护路径、接受文档SHA、JSON/文件链接及行尾空白的管理检查。结果见[本轮verification.json](../logs/native-information-implementation-2026-10-30/verification.json)。**未导入/编译/运行新Python代码，未运行pytest、Shadow、统计或CPU/GPU计算。** 所以语法/运行正确性、原结果逐位相等、实际成本、覆盖度和诊断判决均尚未获得运行证据。

[CODE/限制] 计时实现报告restore、完整candidate-build（含TeamModel/wire/评分/成功率）、BF及总process/wall，冷首次与3次重复分开；不是实际部署时钟，也不是完全拆分每个kernel的硬件计时。context_copy另计，per-method peak memory尚未测；最终可从HPC runner取得child RSS。现有.001s CPU预留完全不因本实现调整，不把更快的Shadow混合计算当部署省费。只记录base饱和cell数，不把其冒称每个后验prefix的饱和全量分析。

[CODE/限制] 标量审计独立计算G0/G1及整数约束，但selector和复杂rank/机制判决另用既有生产逻辑重放。它不是第二个完全独立决策论实现，也不能代替真实任务收益/文献新颖性验证。

## Research Task Report

- **Research Question / Hypothesis**：固定候选下G1是否有超出声明调价/统一尺度的内容级差异；本轮仅实施，答案未获得。
- **已核验前人工作**：[PAPER]沿用既有GOSC纸码映射与静态审稿报告，本轮不新增文献/首次主张。G0是原TV类思想。
- **实际阅读源码**：[CODE] baseline014b85d的native/GP-ID/BF、原EVID value/prefix/codec、HPC登记与合同冻结模式；已验收规格和验收记录。
- **本轮新增或修改**：上述3个extensions、2个scripts、1个测试文件、1个运行计划JSON、本报告与本轮日志；更新研究入口/进度指向实现待验收，保留已验收正文/历史记录。
- **实际运行**：[RUN] 本地git status/rev-parse/remote/diff、rg/Get-Content、apply_patch及PowerShell轻量文档/JSON/哈希管理；具体命令类与身份见任务日志/manifest。没有科研run、seed执行或模型调用。
- **测试与结果**：所有新测试/prepare/Shadow/审计/计时均**未运行**，不存在通过数量；旧485与GP-ID结果保留其原范围。
- **失败/负面证据**：GP-ID科学No-Go与7辅助预算违规、原失败均保持；本轮没有运行失败可冒称消除。静态审阅修正了传感参数比较的括号表达、相关prefix witness约束和确定性捕获覆盖检查；这些不是已通过回归。
- **与原 GOSC 的差异**：独立pure proxy/Shadow及被动观测，不改原算法/default/服务/候选，不新增同步或在线G1部署。
- **公平性与泄露检查**：不可变局部Context、自己接收账本、真实入口、原结构/wire/P_s/非EVID值、独立scalar；无reward、receiver私有/edge真值/未来随机字段进入代理。
- **成本**：本轮仅编辑/文件管理，新增任务N0、无测试/仿真/统计/训练/收费API。新代码实际耗时/内存未知，助手token与管理wall未测。
- **可否进入下一阶段**：代码写入完成；工程验收Pending；原科学No-Go保持。未来HPC合同和最小诊断需各自在明确执行范围/预算内进行，不自动放行效果/训练。
- **用户需要批准的下一步**：待单独明确执行授权后先跑HPC工程合同，合同冻结通过后才可依匹配授权启动最小Shadow。本轮交付代码与可审阅入口，不主动创建批准文件或提交GitHub。
