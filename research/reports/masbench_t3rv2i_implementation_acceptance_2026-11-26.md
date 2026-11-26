# Research Task Report — T3-R-v2-I 实现与HPC无模型验收

2026-11-26，Asia/Shanghai。**新版最小应用协议与本轮无模型工程验收 Go，支持域严格限固定人造数据、假后端及离线词表计数。真实部署未验收、真实能力未评价，仍不得运行能力实验。** 原11月25日Blocked报告保留历史含义。

## 1. 科研问题、授权和实际结果

- **Research Question / Hypothesis**：[HYPOTHESIS] 公平双本地终答及保护是否符合C01–C32，而非是否提高真实模型成绩。
- **已核验前人工作**：AGENTS、研究总说明书和四份v2冻结审查文档；未新增[PAPER]结论或外部任务/文献数据。
- **实际阅读源码**：[CODE] 审阅base `458a96f59b620a02e6872d038b87912eb39e92e4`；原PrivateView/ControlledClient/wire/Ledger/fixture_rpc、HPC登记/同步，以及新增独立协议、保护、评分和验收入口。Git base不等于新增未提交源码；每run另有同步SHA和未跟踪源码归档。
- **本轮新增或修改**：只新增`fair_final_v2*`独立应用/Prompt/保护/离线评分，专用tests、合同/压力/计数/独立审计/独立登记入口、预算/授权、报告及附件；旧应用默认与冻结源码没有修改。
- **实际运行**：[RUN] HPC n1，UID8301880，项目.venv Python3.11.15，实际2核/24GiB；九个新登记，5 completed、4 failed，失败均保留。命令/身份/资源见[run_index](../artifacts/masbench-t3rv2i-20261126/run_index.json)。本地只编辑/Git/文件SHA/同步管理，不跑pytest或研究计算。
- **测试与结果**：[RUN] 专用suite **54 passed**：C01–C32合计53个参数化call，另1项旧语义桥接检查；单独新跑旧synthetic adapter **67 passed**。不能把54或67当独立任务数量。独立审计通过46份journal、5个评分向量、39个冻结文件、完整输入/memory/CRC/uses/计数链。
- **失败/负面证据**：首合同53通过/1失败；压力三版分别遭写入OSError、虚构计数单位误用于窗口判断、1GiB AS下helper OOM；均保留源码快照/日志/原产物。第3版中JSON转义Full触发IPC安全拒绝不是隐藏删除的样本。
- **与原GOSC差异**：仅独立MASBench应用合同，不修改GOSC估值、调度、信道、缓存或训练。
- **公平性与泄露**：六机会、双条件相同公共时钟/模型预算、final不互传、无免费板/纠错；所有新输入为人造颜色/哨兵/压力字串。原四题正文/gold和剩余52条记录未读取；registry仅SHA核验，不解析/修改。
- **成本**：[RUN] 九登记command wall合计30.013862s；runner child user+system CPU合计16.883957s，最高child RSS73272KiB（包括Git管理，非模型专属）；管理/同步/撰稿另计且未仪器化。实际LLM调用、Ollama HTTP和推理tokens=0，词表计数尝试2次（1失败+1获批补验成功）；GPU峰值未测，无模型tensor context创建。wire为合同模拟，不是物理RF实测。
- **可否进入下一阶段**：最小实现及无模型合同Go；真实部署Pending；真实任务/内容价值/无线净收益未建立。T3/G1/GP-ID科学No-Go不变。
- **用户需要批准的下一步**：若继续，先独立审查真实执行适配器/服务身份窗口/硬资源与回滚，不自动放行原四题能力诊断、T4、校准/test/训练。Git提交推送另批。

## 2. 独立实现与异常语义

[CODE] `extensions/masbench_reasoning/fair_final_v2.py`：`system_prompt/public_clock/parse_output`（37–130行）、`Agent`（133行起）、`run_episode`（173行起）。固定四exchange、双local_final，显式role及Prompt SHA；仅本地原始历史与实际送达peer消息，没有共享板。只接受明确的FixtureDriver类型，无真实后端放行开关。

`fair_final_v2_guard.py`：`PacketBudget/CountProof`、`FairLedger`、`FixtureDriver`、`verify_receipt`；复用原持久Ledger、ControlledClient、fixture_rpc及ContractTransport。生成前fsync唯一token预留与HTTP分类计数；unknown usage、崩溃、存储/身份等失败永久停发，不退款、不重放。cleanup单次、1前置GET+最多6poll的语义由假服务验证；真实外部server退出仍未验证。C25另有真实自有fixture进程SIGTERM/SIGKILL退出与崩溃journal核验。

`fair_final_v2_scoring.py`：离线双本地答案评分；原normalize/F1数学口径，独立家族配对汇总、有效/格式/弃答/未答及joint00/01/10/11，started双方固定分母2，未启动条件NA。不导入在线应用，不改旧evaluation。

字面Prompt资产与已审规格SHA一致：模板`00c91af181b4bcedf62acbfee2ab77b8555392d07a52196d3878936d4a375fb4`；角色System2553/2549 UTF-8 bytes。字节不是token数，真实词表另核。

null与空串分别留证；null只在己方字符串历史显式表示为空串，原响应JSON保持null。全串解析不修名字/标签、不抢救片段；非法E/未收turn/乱序或重复来源、空或占位A均失败，U语法有效但得分零。规范化只做CRLF→LF与外侧ASCII空白剥除；原始UTF-8>65536B/编码或封装越界停发，规范化文本>4096B不传、不截断历史，下一输入仍须完整检查。早期A不终止，known usage空/异形答消耗slot继续。

## 3. HPC版本阻断的可审计解决

[RUN/管理] 用户11月26日明确授权备份后仅修元数据。先保存HPC HEAD/index/refs/status，确认origin不变；全量bundle fetch因SSD quota失败，HEAD/index未改，失败pack原字节及SHA保留。改用497599B增量bundle，验证b05ea73是458a96f祖先后，`read-tree`仅建候选index、`update-ref`快进ref，没有checkout/reset/clean或新commit。

前后1320个现有工作文件SHA全部相同。随后标准sync通过：1428→1429→1434文件，各次SHA差异0，用户三项untracked排除，旧结果/缓存/LICENSE保留。历史T3仍b05ea73+20261125T034132Z，不回填新HEAD。

个人quota再次影响同步/压力持久化。仅对本轮临时树和人造压力前缀逐文件核SHA后无损归档，保留SSD归档、tmpfs原副本及storage receipt；逐字节相同的本轮source snapshot以硬链接去重，不改任何内容。没有删测试、旧结果或失败run。登记器递归收集HPC运行数据差异造成重复大补丁，故新增`masbench_t3rv2i_register.py`：复用原runner，仅在新manifest声明排除HPC-owned runs/receipts/dashboard/STATUS通道，完整源码diff与同步快照仍保留；原runner文件未改。

管理备份/失败/保全记录见[任务目录](../logs/masbench-t3rv2i-2026-11-25/README.md)。未测个人quota的持续余量，不能将共享df或逻辑bytes写成SSD硬保证。

## 4. 实际验收、压力及补验边界

[逐项矩阵](../logs/masbench-t3rv2i-2026-11-25/acceptance_matrix.md)列C01–C32实际call数、函数和run。首轮C08误把offered候选字节也要求为0；修为wire/UL/DL零且offered>0，C03加强无frame；没有放宽科学门。第二轮54通过后不重复刷结果。

[RUN] 合成结构35份请求，最大72929B，转义Full t4被64KiB IPC合同拒绝；其余5组完成，原始前缀保留。default bytes/4是假计数，压力器改为固定合成单位只驱动字节路径，真实窗口可行性只用独立词表结果，不能把假计数当qwen tokens。

唯一原helper批次在AS1GiB下OOM。用户单独批准同一输入额外1次、AS2GiB、helper20s，不增加原累计时间/存储；[授权](../protocols/masbench_t3rv2i_counter_authorization_2026-11-26.json)严格冻结输入SHA。补验成功：35份同一输入，最大15046 input tokens，加512为15558≤16384。helper wall2.036730s、观测RSS75030528B；无tensor context、无新消息生成、无服务请求。原失败仍在，不能把v1资源合同写成通过。

## 5. 独立审计、回传与最终决定

[RUN] `hpc-t3rv2i-audit-20261126` stdlib工具不导入生产parser/scorer，重建双条件请求、来源、局部memory、journal哈希链、CRC/uses、人工向量、冻结源码及实际counter输入/render/token_ids SHA，并单列67项新跑旧回归。`acceptance_passed=true`只支持本轮model-free工程域。

9个run定向回传119个当前文件、21131910B；从无损归档恢复218个原文件至受控本地原路径，逐项验证全部259项原artifacts SHA。双端receipt为`20261126-t3rv2i-206d68da03.json`，执行与同步完成分列。pytest临时树按官方通道排除，但完整regular记录归档已回传。原始HPC/run副本不入公开Git；小型非私有摘要有逐字节provenance。

**最终：新版最小实现Go；无模型工程合同Go；真实部署Pending；科研能力未建立。** 相同协议额度不代表实际成本匹配，精确离线词表计数不代表服务有效窗口/usage绑定；四题未来仅开发诊断，独立N未增加。本轮不启动后续实验、不提交推送，交付后停止。
