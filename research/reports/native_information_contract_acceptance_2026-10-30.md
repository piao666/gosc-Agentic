# Native-Information HPC合同检查与工程验收

日期：2026-10-30（Asia/Shanghai）。基线`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`，实际执行源码为该HEAD上的未提交工作区，以各run的source_snapshot/patch/untracked归档标识，不把dirty源码冒称已在该commit内。

**结论：最终完整519项HPC测试通过，支持已检查范围内的工程合同Go；最小有界Shadow机制诊断仍未获运行授权。** 不改变GP-ID科学No-Go，不证明G1有内容级差异、任务收益或发表价值。执行索引见[native_information_contract_execution_2026-10-30.json](../protocols/native_information_contract_execution_2026-10-30.json)。

## 1. 执行授权、身份与环境

[RUN] 用户明确授权“HPC合同检查”。本轮仅定向合同、完整旧回归和必要边界合同补齐；没有调用`repro_native_information_shadow.py --mode prepare/run`，没有执行两cost world×24slot的机制诊断、校准、正式test、训练或LLM/收费API。

[RUN] 只读预检核验：host n1、UID8301880，项目`/home/u202520081000097/jupyterlab/Paper/gosc`；cgroup quota200000/100000、cpuset0-1（2CPU），RAM25769803776bytes（24GiB）；项目.venv Python3.11.15、NumPy2.4.6、pytest9.1.1；无running run，上次同步584文件0差异。证据：[preflight.json](../logs/native-information-contract-2026-10-30/preflight.json)。

[CODE/RUN] 远端原HEAD253a14b是当前014b85d的严格祖先。已核对原origin/分支、无活动任务、原同步字节一致，先备份远端index/working.patch/status，再只推进分支ref与index，没有checkout/reset/clean或改动工作文件。证明：[reconcile.json](../logs/native-information-contract-2026-10-30/reconcile.json)。备份留在HPC `.local/git-checkpoints/20261030-before-native-contract/`。随后标准源码同步核验637文件、0SHA差异；运行数据通道未上行覆盖。

## 2. 实际测试与结果

[RUN] 所有测试均经`hpc_runs.py launch`在HPC登记，GNU timeout每次240s，单pytest进程，OMP/OPENBLAS/MKL/NUMEXPR线程显式1。没有在本地导入/编译/执行科研Python或pytest。真实完整参数见[actual_commands.json](../logs/native-information-contract-2026-10-30/actual_commands.json)及各run manifest。

| run | 范围 | 实际结果 | runner elapsed | child max RSS |
|---|---|---|---:|---:|
| hpc-native-information-contract-20261030 | 首轮新增合同 | 31 passed，0失败/错误/跳过；pytest0.64s | 1.126562s | 50,544KiB |
| hpc-native-information-regression-20261030 | 首次tests+tests_ext | 516 passed，含31个新case；pytest51.05s | 51.379726s | 87,756KiB |
| hpc-native-information-regression-v2-20261030 | 补齐3个边界case后完整tests+tests_ext | **519 passed，含34个新case，0失败/错误/跳过；pytest50.66s** | 50.966930s | 85,660KiB |

CPU/RSS是runner所有子进程口径，含Git管理，不是估值器独占成本；没有测GPU峰值，也没有运行GPU训练。三个run都正常退出；31、516、519有重复覆盖，不能相加当独立测试数。最终完整519才是本版总回归证据。

原件：

- [最终JUnit](../sync/runs/hpc-native-information-regression-v2-20261030/outputs/pytest.xml)、[stdout](../sync/runs/hpc-native-information-regression-v2-20261030/stdout.log)、[status](../sync/runs/hpc-native-information-regression-v2-20261030/status.json)、[manifest](../sync/runs/hpc-native-information-regression-v2-20261030/manifest.json)、[source_snapshot](../sync/runs/hpc-native-information-regression-v2-20261030/source_snapshot.json)。
- 首轮与首完整run均在各自run目录保留，未覆盖或替换。

## 3. 合同覆盖与本轮改动

[CODE/RUN] 已通过合同覆盖：G0对原TV的数值一致、不可变输入/未知字段拒绝、区域意图/位置/均匀回退、权重界与打乱、证据正负抵消/零live/饱和与溢出、未来/私有/重复记录拒绝、本地身份账本、观察中性、零DL、固定wire结构/非EVID保持、独立标量复算、输入/payload/评分篡改拒绝、运行权限/源码身份/文件覆盖和上限。

[CODE/RUN] 首完整通过后，按已验收规格补齐3个明确缺口：

1. 自己task广播先于ACK：队列仍含已融合记录时，outstanding和identity guard均拒绝估值；重复同task不再融合；原ACK路径最终移除记录。
2. ACK先于自己广播：原ACK清队列时不提前融合本地Lc或清private；收到自己task后才融合/抵消pending。
3. 同时删去input/output快照：独立first-eight覆盖检查仍拒绝，不因双方列表长度一致放行。

前两项是**明确的适配器记账状态夹具**，用注入ACK列表/直接本地接收调用构造顺序，不冒称实测物理RTT、CRC完整传输或新的任务结果；实际服务/wire仍有已有回归及新同wire合同覆盖。第3项是合成覆盖拒绝合同。补充只修改新测试文件，生产模块/旧算法未为测试放宽，之后用新runID完整复测519通过。

[CODE] 原`gosc/`、native wire/适配/服务、GP-ID/BF默认和旧测试未改。34个新增case在本轮最终测试文件中；已验收静态规格/可行性审查SHA保持。最终测试snapshot绑定的新3个extension、2个script、测试/计划/规格与当前本地LF规范化SHA均相同（8文件0差异），见执行索引source_bindings。

## 4. 回传与复现边界

[RUN] 三轮均自动回传完成。最终receipt：[20261030T082923Z-bd7a09](../sync/receipts/20261030T082923Z-bd7a09.json)，`all_outputs_mirrored=true`，本次新增下载21,751,377bytes（含源码/管理证据，不是单独科研数据体量）。最终测试源sync `20261030T082704Z`，637文件、0差异；只比前轮更新一个新测试文件。后续报告/索引同步另列管理记录，不能倒填为测试时的源码身份。

[RUN/限制] 工程合同内部执行了合成/4slot短fixture、纯snapshot Shadow函数和计时函数的调用/不变性检查；这不等于已运行预定两world×24slot、最多96快照的机制诊断，不用这些fixture输出回答G1的研究问题，不计入独立收益N。没有C_norm/C_select、功效、收益CI或任务优越性检验。

[HYPOTHESIS/边界] 519通过仅支持已检查输入和时序范围，不是任意浮点输入/任意长mission/所有状态的正确性证明。完整prepare→授权→两world诊断链及120s/32MiB真实费用仍未实测；本轮不生成已批准授权文件、不自动prepare或启动诊断。未来先冻结测试身份并取得匹配的明确执行授权，再运行最小诊断；正向诊断也不自动解封任务效用验证/训练。

## Research Task Report

- **Research Question / Hypothesis**：检验新最小Shadow实现的工程合同与旧回归；不检验G1优于GOSC或不可调价解释的机制命题。
- **已核验前人工作**：[PAPER]沿用既有纸码映射/静态审查，本轮无新增文献事实或新颖性断言。
- **实际阅读源码**：[CODE] 014b85d+dirty独立扩展、native/GP-ID/BF时序与HPC同步/登记、已验收规格和新增合同；执行时身份由各run snapshot保存。
- **本轮新增或修改**：新测试补3个ACK/漏项状态合同；新增本报告、执行索引、管理preflight/reconcile/实际命令/证据记录；更新研究进度。生产算法及已验收文档原样保持。
- **实际运行**：[RUN] 预检/严格后代Git核对与备份、标准源码同步、3次HPC pytest（上述run）；环境/命令/原件/receipt见链接。无科研计算本地回退、模型下载/安装或额外高资源任务。
- **测试与结果**：最终519完整通过，34新case；首次31及516通过保留。没有运行最小机制诊断、正式test或训练。
- **失败/负面证据**：本轮项目测试无失败；历史GP-ID No-Go/7辅助违规/BF早期失败完整保持。HPC初始HEAD落后已核验并安全协调，不覆盖旧原件；本地初次查找推测的scripts/hpc_receive.py不存在，无据其报已核验。
- **与原 GOSC 的差异**：独立扩展/观测/Shadow仅获工程合同证据，原ToM/FIFO/filter/服务/选择器默认不变。
- **公平性与泄露检查**：自身局部证据身份与guard、同catalog/非EVID/wire/P_s约束、独立标量和覆盖拒绝已按合同测试；不能外推所有不可见receiver状态或真实任务收益。
- **成本**：3次runner耗时与RSS分别列出，单worker/数值线程1；0新研究LLM/API/训练，收益N0。助手tokens和GPU峰值未测。
- **可否进入下一阶段**：**工程合同Go（已测支持域）**；等待最小机制诊断单独授权，原科学No-Go保持。
- **用户需要批准的下一步**：本轮授权的合同检查已完成。未获得Shadow运行授权，不自动启动prepare/诊断/任务效用试验、扩N、训练或Git提交推送。
