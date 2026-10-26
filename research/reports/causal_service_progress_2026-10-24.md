# Research Task Report

- **Research Question / Hypothesis**：[HYPOTHESIS] 统一task/summary反馈与CPU时钟、限制盲目历史重播后，真正收到的pose是否能在强简单对照及实际通信/CPU成本约束下改善任务？本轮完成实现和短探测，**独立校准因计算预算关卡停止，未验证任务收益**。响应用户依序推进要求；不是扩大旧校准N或自动训练。
- **已核验前人工作**：[PAPER] 沿用已有`research/logs/GOSC_paper_code_map.md`与总说明书；本轮没有新增论文阅读或作者结论核验。[RUN] GP-v1原12world校准No-Go、作者原校准/cache生成链及部分历史差异保持原判断，见2026-10-23校准/成本审查及2026-10-22总复现审计。新服务修订不能填补这些原复现缺口。
- **实际阅读源码**：[CODE] 基线`47389eba9c6e2838139df3aa47863ab88634e97a`；`paid_receiver_service.py`的CPU/tick/ACK/replay、`receiver_rtt_contract.py`的attempt/feedback、`native_paid_adapter.py`的局部接收/选包、`native_task_wire.py`的实际长度候选、`paired_paid_simulation.py`的CRN、原`schemes.py`的Option/Group/lagrangian_select。映射保持：本轮只修改extensions适配路径，原`gosc/realistic.py`和`gosc/schemes.py`两条原路径均未改。
- **本轮新增或修改**：[CODE] 详见下表；旧GP-v1默认服务保持，GP-v2独立标识。
- **实际运行**：[RUN] 仅HPC `n1`、UID8301880、Python3.11.15、单worker/数值线程1；配额2CPU/24GiB。5个登记run均正常退出；不是5个科学验收全部通过——probe的预算结果为blocked。命令和SHA详见各run manifest及本任务日志目录。
- **测试与结果**：[RUN] 187项主回归通过，28项补充合同通过（其中25项重复，不相加成215个独立测试；共190项不同测试）。两个16slot旧GP-v1 fixture与归档源码输出全部字段相等；只证明支持fixture未回归，不是全历史等价证明。42次短probe、31,280条事件账本独立核对通过，投影895.5021709203719秒，**预算门槛未通过**。没有计算校准任务收益CI；没有校准方差/正式N。
- **失败/负面证据**：[RUN] 本轮没有pytest失败或仿真软件异常。预算blocked证据不可删除；896s是2倍安全系数的短任务外推，不是实际校准耗时，也不能因为probe实际4.87s就断言完整校准可在600s内完成。合同保留接收丢失、CPU排队、未送达/mission末尾censor；有界catchup不能保证peer完整知识。旧科学No-Go不撤销。
- **与原GOSC的差异**：[CODE] GP-v2继续沿用原Planner、原非oracle ToM及原lagrangian_select，使用本项目GP语义wire/CRC与局部接收服务；非作者旧wire精确复现。统一有限服务协议改变了实验系统，因此GP-v1旧结果不能作为新版本效果复现或配对新样本。
- **公平性与泄露检查**：[CODE/RUN] 所有arm共用同一UL/DL/CPU/重试/catchup/CRN；摘要只用task剩余UL。paid-ignore真实付费而估值忽略；age只用本地已接收新摘要或native时间戳；shuffle只在当前本地有效条目之间重排pose，domain206独立于任务噪声。world从152份可发现登记目录/协议查重，冻结214指纹且无发现冲突；不保证未登记历史不存在重复。新test world仅构造初始指纹，任务执行0次。
- **成本**：[RUN] 0GPU、0新LLM、0token调用、0训练。主合同36.60s/子进程CPU36.64s/峰RSS59332KiB；补充2.93s；world冻结2.27s；probe4.87s；独立审计0.33s。runner子进程CPU/RSS含Git管理，不是模型独占性能。实际每次UL/DL/CPU账本与原始events保存在probe outputs。估值固定每次admission .001s为场景假设，另记录selection process_time、mission CPU/wall；投影/Planner/解释器开销未建成测量硬件服务模型，不声称部署净计算收益。
- **可否进入下一阶段**：时钟/有界catchup/消融接口合同Go；成本前沿及完整消融**仅实现、未验收效果**；独立校准**Pending（预算blocked）**；正式test/训练No-Go。新协议科学收益尚未知，不能把预算停止写成方法无效。
- **用户需要批准的下一步**：审阅`research/protocols/causal_calibration_budget_proposal_2026-10-24.md`，是否将投影门槛提高到1080s、校准上限1200s；保持原21候选×12新world×400slots，不增N、不换参数、不含test/训练。本提案非授权，原冻结协议不回写。用户不批准则在当前交付停止。

## 已完成与待验证

| 顺序 | 本轮状态 | 验收边界/下一步 |
|---|---|---|
| 1 反馈与CPU时钟 | 已实现、合同通过 | RTO下界`1+delay+ceil(decode_seconds/slot_seconds)`，当前2slot；只是无队列下界，不能预知排队/ACK丢失。每次估值工作先占共享CPU再排该批编码，未改变原规划代码。 |
| 2 有界catchup | 已实现、合同及短probe账本通过 | edge接收年龄<=20slot，每item最多重播2次，每refresh最多6帧，排队/部分服务中不重复入队。选择不查询receiver状态；初传、ACK重传和在途帧仍保留/计费。 |
| 3 公平比较与估值成本 | 实现和候选冻结完成，收益/前沿待测 | 10简单候选；public/pose/age各3价格；ignore/shuffle各1价格，共21。通信+CPU离散前沿、双成本±5%重叠支持规则预先写明，尚无完整mission前沿报告。 |
| 4 独立校准 | world/源码冻结，probe完成；校准未运行 | 2probe世界22000000–1；12calibration世界23000000–11；预留200test世界24000000–199。42probe不是252calibration，也不是独立校准N=12。预算修订需用户确认。 |
| 5 正式验证/训练 | 未运行 | 没有可执行正式test N/预算；先完成新校准和公平支持/六端点功效关卡，不能沿用旧15419规划值。 |
| 原作者复现缺口 | 未新增解决证据 | 作者1000–1079校准、作者cache生成链和部分历史数值差异仍单列，不由新协议合同冒充完成。 |

## 代码与证据

| 文件 | 作用 |
|---|---|
| extensions/paid_receiver_service.py | 增加默认等价job、task计时、重播扩展点；不改旧规则 |
| extensions/native_paid_adapter.py | 服务构造/估值视图扩展点；旧构造默认等价 |
| extensions/causal_paid_service.py | 因果RTO下界、task/summary统一重试、估值CPU队列、有界盲目重播 |
| extensions/causal_paid_simulation.py | 独立GP-v2标识，public/pose/ignore/age/shuffle；实际selection耗时 |
| tests_ext/test_causal_paid_service.py、test_causal_paid_simulation.py、test_causal_calibration_protocol.py | 服务、信息隔离、预算网格及归档源码默认等价合同 |
| scripts/repro_causal_service.py | HPC freeze/probe/calibration，逐任务原始结果、事件、离散前沿/六端点功效；无正式test入口 |
| scripts/audit_causal_service.py | 不调用分析器的原始账本、投影及统计复算；本轮只执行probe模式 |
| research/protocols/causal_service_stage_v2.json | 事前冻结协议，保持blocked预算原值 |

运行根目录`research/sync/runs/`：

1. `hpc-causal-contract-20261024`：187 passed in35.49s。注册config误沿用旧periodic JSON，**实际命令/源码/测试参数**见manifest与source snapshot；该config不能当新协议参数证据。随后补充run使用正确新config，未修改首轮历史。
2. `hpc-causal-protocol-contract-20261024`：28 passed in2.45s，含归档源码对比和新候选协议校验。
3. `hpc-causal-world-freeze-20261024`：214world/21case/152catalog/0发现冲突，`outputs/frozen.json`保存源码与世界SHA。
4. `hpc-causal-cost-probe-20261024`：42任务，`outputs/results.json`、42份原始结果和42份events JSONL；`budget.json`为blocked。
5. `hpc-causal-probe-audit-20261024`：`outputs/audit.json`确认31,280事件、最大重播2/每轮6、成本投影复算一致。

旧输出、失败记录和旧协议未覆盖。本轮Git起点47389eb；新增源码/报告**未提交、未push**。HPC原HEAD4ff4147是严格父版本：先验证上次447文件SHA、备份原索引/工作补丁，再快进Git引用与索引，随后单向SHA同步；原始结果和远端独有文件保留。远端管理工作树中的LF/历史运行通道差异按真实manifest记录，不能把当前HEAD当全部源码身份。

本地报告与源码同步交付及完整回传receipt见`research/logs/causal-service-2026-10-24/delivery.json`（交付时生成）；这是文件完整性证据，不更改上述科学关卡。

[RUN] 全部5项运行产物回传receipt为`research/sync/receipts/20261024T030434Z-c4580b.json`，all_outputs_mirrored=true，新增88,739,160bytes（包含运行快照/源码补丁，不等于仅42条raw数据大小）。实际展开命令和seed/config/sync身份已整理到`research/logs/causal-service-2026-10-24/actual_commands.json`。本地仅进行了Git、文件/哈希与同步管理；统计/合同/仿真均在HPC。
