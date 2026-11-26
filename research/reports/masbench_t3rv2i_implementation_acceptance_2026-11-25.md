# Research Task Report — T3-R-v2-I 独立实现与验收状态

2026-11-25，Asia/Shanghai；审阅基线458a96f59b620a02e6872d038b87912eb39e92e4。**独立实现已新增但尚未验收；HPC合同执行Blocked，不能给新版工程Go。** 本报告不将源码存在、旧测试或静态检查当成新版测试通过。

## 1. 问题、授权与证据

- **Research Question / Hypothesis**：[HYPOTHESIS] 六机会、双本地final协议与必要保护能否满足C01–C32？本轮不研究真实推理成绩。
- **已核验前人工作**：基线四份v2静态文档、AGENTS和研究总说明书；旧MASBench/GOSC行为仅作为保护基线，无新增[PAPER]结论。
- **实际阅读源码**：[CODE] 原application/private_view、client/ControlledClient、wire、execution_safety/Ledger、fixture_driver/fixture_rpc、hpc_runs/sync_hpc及相应合成测试；新源码见下表。
- **本轮新增**：独立版本协议/Prompt、fake-only执行保护、离线双final评分、C01–C32测试、HPC合同/压力/独立审计入口、预算与本目录报告日志。没有修改旧模块或冻结文档。
- **实际运行**：只有Windows编辑、文本/Git/SHA管理及SSH只读环境核验；HPC测试、tokenizer、压力、独立审计和回传均**未运行**。
- **测试与结果**：无新pytest通过/失败结果；实际矩阵全为Blocked/未运行，详见[矩阵](../logs/masbench-t3rv2i-2026-11-25/acceptance_matrix.md)。不存在可供引用的新测试run ID。
- **失败/负面证据**：[RUN/管理] 初次SSH在受限环境permission denied；授权连接可达。cgroup v2路径不存在，按v1只读核实CPU quota200000/100000、cpuset0-1、内存25769803776B。HPC HEAD=b05ea73，索引大量暂存删除，当前无running登记；版本/未提交状态阻断同步。保护原状态，不reset/checkout/clean。
- **与原GOSC差异**：仅新增MASBench独立命名路径，无GOSC调度、信道、训练或历史成绩修改。
- **公平性与泄露**：只用人造颜色/哨兵；原四题和剩余52记录正文、gold均未读取，registry只作文件SHA，不解析；新应用不导入离线评分域。
- **成本**：新增实际模型调用、推理tokens、真实无线uses、GPU计算、服务请求均0。管理和撰稿未仪器化；测试预算不是实耗。
- **可否进入下一阶段**：实现待验收；无模型合同Blocked；真实部署Pending/未运行；科研能力未评价，T3/G1/GP-ID科学No-Go不变。
- **用户需要批准的下一步**：已提出仅备份/对齐HPC Git元数据的处理方案；未收到答复前不更改HPC源码或启动测试。Git提交推送亦未授权。

## 2. 独立新增入口和变更清单

| 新文件/函数 | 实现范围 | 当前验证层次 |
|---|---|---|
| `extensions/masbench_reasoning/fair_final_v2.py:37–130`，system_prompt/public_clock/parse_output | 固定模板和角色SHA、公共五字段时钟、MESSAGE/FINAL全串语法、E来源、A/U与异常 | 静态新增；动态未运行 |
| 同上 `133–171`，Agent | PrivateView精确类型、显式role、原始己方历史、原样peer/source哈希，无累计板 | 同上 |
| 同上 `173`起，run_episode | 六slot、禁止early-A终止、No保留final、双方final隔离；只接受明确的FixtureDriver类型 | 同上 |
| `fair_final_v2_prompt.txt` | 字面模板SHA `00c91af181b4bcedf62acbfee2ab77b8555392d07a52196d3878936d4a375fb4`，与已审规格一致 | 本地文件SHA核实；角色替换断言未运行 |
| `fair_final_v2_guard.py`，FairLedger/FixtureDriver/CountProof/PacketBudget | 复用原持久Ledger、ControlledClient、seccomp fixture_rpc和wire；统一计数/不可退款/崩溃栅栏/字节保护/假的服务退出观察 | 实现存在；不代表真实服务退出验证 |
| `fair_final_v2_scoring.py`，score_episode/paired_summary | 离线双final F1/EM、joint正确模式、回答/格式率、家族配对NA及条件汇总 | 不改旧evaluation.py；固定向量未执行 |
| `tests_ext/test_masbench_fair_final_v2.py` | C01–C32及旧解析/默认语义的小型回归，所有内容人为合成 | 全部未运行 |
| `experiments_ext/masbench_t3r_v2_contract.py` | HPC专用pytest入口、禁网络/任务文件审计hook、AS/CPU限制、JUnit/逐合同结果、失败夹具journal归档；`--legacy`单列旧合成回归 | 未运行，不借用旧通过记录 |
| `experiments_ext/masbench_t3r_v2_pressure.py` | ASCII/多字节/JSON转义完整输入压力，逐请求字节和可选pinned词表计数；不导入旧development_inputs | 未运行 |
| `experiments_ext/masbench_t3r_v2_audit.py` | stdlib独立重建请求/局部memory、journal、CRC/uses及评分向量，不导入生产parser/scorer | 未运行，不能称独立审计通过 |

实现的公共入口没有真实模型开关或旧授权文件路径。FixtureDriver自身只使用固定人造输出及假后端；ControlledClient仍做输入冻结、身份、窗口、usage和长度检查。生成模拟请求之前持久预留token和计数，实际模型HTTP为0。未来真实适配器仍须另批，不通过改一个布尔参数开放。

## 3. 已固定异常判定

null以`empty_null`保存原始JSON null，只在己方字符串历史明确表示为`""`；空串或仅外侧ASCII空白为`empty_response`。两者在known usage/stop下消费slot，不补请求。格式异常、未知E/引用未收到或错误角色turn、重复/乱序引用、空/占位A均全串拒绝，不能截取有效片段。

规范化只做CRLF→LF和外侧ASCII空格/TAB/CR/LF剥除；不改内部空格、字词、名字、事实或大小写。标签内容拒绝C0、DEL及Unicode换行符U+0085/U+2028/U+2029。A经原数学normalize为空，或外侧空白/大小写处理后等于answer/your answer/final answer，均不作有效答案。U语法有效但未答、得分0。

原始UTF-8>65536B、非法Unicode编码、HTTP/IPC封装越界为安全失败并停止；规范化文本>4096B为格式失败，不发送、不截断己方原始历史，后续完整输入越界则停止。64KiB针对实际序列化packet另有约束，不能保证任意65536B字符串在加JSON封装后仍可发送。截断、unknown usage、超时、身份/预算/配额/清理异常持久停发，未知用量不记0、不退款，未派发slot保留状态。已启动双方final固定分母2，未启动条件单列NA。

## 4. HPC阻断及继续条件

本地和GitHub均458a96f；HPC仍b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0，并有MM及大量D暂存记录。此为既有HPC元数据状态，不是本轮删除。`sync_hpc.py`明确在HEAD/origin不一致时拒绝覆盖，AGENTS A.3/J要求保护未提交和核对版本，故不绕过、不伪造同步成功。

处理请求是：先备份HEAD、索引与状态，仅对齐Git元数据至458a96f；不覆盖工作文件、原运行目录或结果，不用reset/checkout/clean；复核保护后才按标准同步新增源，排除三项用户未跟踪文件。**该处理仍等待用户答复**。时间过去不等于授权。

获准且通过核验后，按冻结[无模型预算](../protocols/masbench_t3rv2i_model_free_budget_v1_2026-11-25.json)经hpc_runs新登记执行，失败原样保留；不得本地回退或直接运行真实Ollama。不在本轮自动进入能力诊断/T4/校准/test/训练。

## 5. 最终分层决定

| 层次 | 当前结论 |
|---|---|
| 新版实现通过 | **尚不能称通过**：实现已新增，等待HPC动态验收 |
| 无模型合同通过 | **Blocked/未运行**：C01–C32无实际通过证据 |
| 真实部署通过 | **Pending/未运行**：无服务/模型/真实资源现场核查 |
| 科研能力成立 | **未评价/未建立**：无真实任务，旧科学No-Go保持 |

本轮没有Git提交或推送，未修改任何历史No-Go或成绩。当前可审阅新增代码和具体验收设计；工程Go必须等实际合同、独立审计与完整回传证据。
