# Research Task Report

日期2026-11-03。用户批准按顺序执行P0分组复核、P1开发曝光清单、P2受控客户端及无模型验收，并整理上下文/资源预算；真实四题Full/No-A2A仍须单独批准。本轮没有运行它。

- **Research Question / Hypothesis**：[HYPOTHESIS] 去除无效分组键是否改变既有大组；可否无成绩筛题地登记开发问题，并提供对身份、上下文、费用和失败语义可审计的客户端？不检验新方法收益。
- **已核验前人工作**：[CODE] GOSC014b85d、MASBench c0301a6，沿用此前原生源码/模板/许可和300行正文身份；本轮不新增文献效果主张。
- **实际阅读源码**：[CODE] 旧data_audit/followup、原prompts/agents/conversation活动路径、hpc_ollama配置和环境记录；新增registry/client及对应HPC入口。受控HTTP复用已安装httpx，不修改依赖。
- **本轮新增或修改**：`extensions/masbench_reasoning/registry.py/client.py`；`tests_ext/test_masbench_reasoning_preparation.py`；四个独立HPC准备/验收入口；[实施说明](../benchmarks/masbench_reasoning_controlled_client_spec_v1.md)、[预算书](../benchmarks/masbench_reasoning_context_resource_budget_v1.md)、[机器可读提案](../protocols/masbench_reasoning_minimal_capability_proposal_v1.json)与本轮日志。原GOSC/旧扩展、原始300行/旧分组报告和失败不改。
- **实际运行**：[RUN] 7个登记HPC run，详下表；UID8301880、n1、HEAD014b85d、实际2CPU/24GiB，无GPU任务。Windows仅编辑、Git/文件哈希/同步，不本地跑项目测试或统计。
- **测试与结果**：[RUN] 最终147pytest合同通过（旧67＋80新case），另独立Reasoning环境实际httpx0.28.1 MockTransport的5项unittest通过，全部无真实网络/模型。较早119/123通过记录保留，不将两轮重复数相加。确定性合同/完整题库盘点不作抽样CI。
- **失败/负面证据**：首次SSH预检超时，用户恢复连接后继续；无本轮红测试。修正14个空支持键后仍38组/最大242，不能用“修bug”消除数据独立性问题。默认1024配置、缺精确tokenizer和有效context核验、248预留后仅52未预留均保留为限制。
- **与原 GOSC 的差异**：新包/入口独立；不改旧FIFO/source filter/BF/价值函数/无线默认，也不借Search真实位置、Lc或奖励。仅实现受控请求/数据注册，不构成新估值贡献。
- **公平性与泄露检查**：分组选择不读取gold/score/模型结果/文本长度；同题跨难度仍一族；两异常家族事前排除pilot但不删原件。客户端只接本agent已构造请求；本地板仅own与delivered peer；No-A2A可本地答。进程内可信controller接口，不作恶意Python沙箱保证。
- **成本**：2个已有数据/模板分析、5个合同run；无模型下载/依赖安装/付费API、实际LLM调用0/任务episodes0/训练0；实际秒数与产物见manifest。源码同步/runner快照是管理通道，非任务通信字节。
- **可否进入下一阶段**：P0/P1已完成，P2在替身/实际httpx mock支持域工程Go；资源上界提案已交付。**真实诊断仍Blocked/Pending：精确部署tokenizer与有效context、运行许可及后续独立池充分性未核验。** 不把budget算术完成写成实际上下文已足够。
- **用户需要批准的下一步**：先审阅本清单曝光代价、tokenizer/context核验方式及6000s/256MiB预算提案，再决定实际调用。若需新依赖或服务配置，先给具体方案；本轮不自动安装、改context或运行模型。G1/GP-ID科学No-Go保持，不提交Git，交付后停止。

## 1. P0：修正结果与归因

数据仍为原SHA `ce65640b566e70098c540b9c814768c9ff5d8544a4cb25162a3872ac9c3bb331`，300行/200规范化问题，不新增数据。新版保留legacy重算并核对旧38组/最大242，防止比较对象错位；旧脚本和旧输出均未覆盖。

| 图/核验 | 本轮HPC结果 |
|---|---|
| legacy完整图 | 38分量，最大242 |
| corrected完整图 | 38分量，最大242 |
| 旧新任意行对同组关系变化 | 0 |
| 空键拒绝 | 14次空支持键实例，非14个独立问题 |
| 只按问题/ID | 200分量，最大2 |
| 只按共享context文章 | 38分量，最大242 |
| 问题＋context文章 | 38分量，最大242 |
| 绑定文章的非空support图 | 200分量，最大2 |

[RUN/有限归因] 在该固定数据和连边定义内，共享context文章的图本身足以产生相同分区，修正空句/文本-only键未改变同组关系。不能进一步声称共享distractor已被证明是任务性能的因果原因，或这些分量等价真实统计独立源任务。原9/17/274不冻结，不靠改hash种子找更好比例。

## 2. P1：开发预留清单已冻结，尚无模型曝光

| 原行index | record ID | 记录级难度 | corrected分量 |
|---|---|---|---|
| 25 | sample_251_f128c587 | easy | 7 |
| 124 | sample_153_1d14c5cc | easy | 0 |
| 294 | sample_278_79ddf47b | hard | 35 |
| 259 | sample_152_1d4d49b1 | hard | 1 |

四个不同问题家族，实际也来自四个不同保守分量；记录级难度不作为在线输入。选择基于事前固定VERSION/数据SHA/规范化问题/ID的SHA排序与分量覆盖偏好，没有查看模型表现或答案是否出现在context。

原indices244/245两条support异常及同题家族未入选，原件与异常标记都保留。保守开发预留248条，未预留52条；目前`actual_model_exposure=false`。这些是保守的未来曝光管理，不代表已经向模型喂入248条，也不将52行冒称52个独立测试问题。未来独立校准/封存/功效仍Pending，应在真实调用前审阅这一明显代价。

registry内容SHA `94b20ff4e199f8e6dc9eeeae8b0a8f91767c00576906f5589387a1266f4a4f1a`；完整文件SHA `6d14229ae0dd85a5b3c88b9309fcf86e54fab2523a3701914a7f7ebc06500a86`，两者序列化定义不同，不混用。引用原run文件即可；本轮不手工重写另一个“相同”清单。

## 3. P2：客户端工程验收与尚缺能力证据

实现精确回环端点、无proxy/.env/云端回退、无自动retry；逐调用前核验model digest与ContextBinding，冻结并哈希请求/响应/payload，检测输入溢出和输出length截断。缺usage明确null，不虚构tokens；不合法usage或prompt计数不符则失败，不能将可能静默截断的结果作为有效任务答案。

审计日志exclusive新建，逐phase落盘；失败请求/首请求超时同样在已启动任务分母中计0，不在异常后跳题。60s为metadata和生成共享的操作期限，超时晚到响应不可作为答案。未来实际模型调用需要单独获批协议/registry permit和已核验tokenizer/context；本轮只测试fake backend/HTTP MockTransport，没有实调服务。

最终147组合合同在原GOSC venv运行；5项实际httpx MockTransport合同使用独立Reasoning venv，记录实际Python和httpx0.28.1。没有为运行pytest往独立env装依赖，亦未向原GOSC venv安装httpx。实际httpx timeout异常类已纳入受控分类，与纯替身的TimeoutError分开核验。

## 4. 上下文与资源：上界明确，能力不冒充

[RUN] 16个原模板初始请求已生成bytes/哈希，最大system content为16,423bytes；不是模型token数。独立env未找到精确tokenizer相关模块。现有启动脚本固定1024，模型metadata宣称32768不等于服务有效32768；本轮未修改或试验该配置。

提案固定一个现有qwen2.5:7b候选、base主/protocol辅助、4题×2提示族×2通信设置=16episodes；6turn，每请求512输出tokens，任务96次＋合成预检2次=98，输出上界50,176tokens；候选32768context下输入理论上界3,161,088tokens。建议总墙钟6000s、产物256MiB、一次1模型调用、2CPU；全部是提案硬上界，真实耗时/显存投影未测。

通过工程合同不能证明实际chat兼容、长context不截断、512输出足够、多轮能力或通信增益。当前部署绑定仍未核验，因此客户端会拒绝真实请求；不能手工把fixture证据填成已verified来绕过。剩余52行与科学独立评价空间也未通过审阅。

## 5. 真实运行与证据

| run | 状态/秒数 | 内容 |
|---|---|---|
| hpc-masbench-registry-v2-20261103 | completed/0.794674s | 分组复核＋开发预留，原始数据只读 |
| hpc-masbench-client-contract-20261103 | completed/2.191897s | 首轮119合同通过 |
| hpc-masbench-context-budget-20261103 | completed/0.236796s | 模板初始bytes/哈希与独立环境只读检查 |
| hpc-masbench-client-contract-v2-20261103 | completed/0.784098s | 阶段123pytest通过，pytest0.40s |
| hpc-masbench-httpx-mock-20261103 | completed/0.296490s | 独立env5项实际httpx MockTransport通过 |
| hpc-masbench-client-contract-v3-20261103 | completed/0.924613s | 最终147通过，新增24个新driver对原等价fixture，pytest0.51s |
| hpc-masbench-httpx-mock-v2-20261103 | completed/0.190794s | 最终源码下独立env5项再次通过 |

完整命令/资源/sync/dirty与输出SHA在各run manifest/status/artifacts和[本轮执行索引](../logs/masbench-client-preparation-2026-11-03/experiment_manifest.json)。数据图与registry在首run的`grouping_review_v2.json/development_registry_v1.json/preparation_summary.json`；合同XML/纯替身审计、context_budget_preflight与httpx_mock_contract各在对应outputs。

HPC运行完成和本地回传/最后文档上行分别核验，见本轮task_log与执行索引；不回写旧运行身份。最后完成文件核验后停止，真实模型、正式测试/训练、Git提交/推送均不执行。


补充支持域：新driver对两提示族×12组已与原源码核对的fixture逐request/memory/transcript/答案/终止再次一致；API有效null/空完成沿用原生`content or ""`后处理并留empty标记，不误作新终止条件。严格的请求强制中断/总campaign存储与墙钟watchdog仍应由未来获批执行driver实施；当前客户端的HTTP超时和晚响应拒绝不是OS级强制中断证明。预算6000s/256MiB仍是需审阅的硬cap提案，不是已经测得所有任务会在其内完成。


最终产物回传receipt `20261103T072351Z-cbea65.json` 全部mirrored并写回HPC；本地轻量文件核验通过，73冻结源码/旧审阅保护源不变，最终Python代码与147项HPC执行snapshot逐文件一致。文档上行20261103T072635Z已核793文件、SHA mismatch0；最后完成说明再同步，实际最终源快照见HPC latest_manifest/同步stdout，不改旧运行身份。模型调用、任务episodes、训练和Git提交仍为0。
