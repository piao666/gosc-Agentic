# Research Task Report

日期：2026-11-03（Asia/Shanghai）。本轮：数据核验＋最小无模型适配实施与HPC合同验收；用户已明确批准。本报告区分工程验收、数据限制和科学证据，不能用工程通过替代任务收益。

- **Research Question / Hypothesis**：[HYPOTHESIS] 原生Reasoning私有输入、解析和首答案目标能否在真实UTF-8消息边界下保持，且拒发/丢失时不经全局知识板泄漏？本轮不检验通信收益。
- **已核验前人工作**：[CODE] MASBench固定`c0301a650db95958924bb080192c09fef39389a5`的Reasoning源码/README与MIT许可原件已按Git blob核验；沿用先前[PAPER]静态审查，本轮不新增论文效果主张。[官方版本](https://github.com/BUPT-GAMMA/MASBench/tree/c0301a650db95958924bb080192c09fef39389a5/Reasoning)。
- **实际阅读源码**：[CODE] 原`agents.py`活动OpenAIAgent、`conversation.py`双会话与parser、`data_loader_v4_mas.py`context/support、`metrics.py`、`prompts.py`、`run_asymmetric_agents.py`构建/通信/汇总；GOSC `channel.py`、`config.py`及BF接口边界。
- **本轮新增或修改**：独立`extensions/masbench_reasoning/{application,wire,evaluation}.py`；`tests_ext/test_masbench_reasoning_adapter.py`；三个HPC审计/合同入口；[实施合同](../benchmarks/masbench_reasoning_adapter_contract_v1.md)；本轮日志/原生参考源码/数据证据。原GOSC和历史扩展不改，旧报告/失败记录保留。
- **实际运行**：[RUN] 下表登记run，全部HPC `.venv/bin/python`，UID8301880、HEAD014b85d、2CPU/24GiB；无任务seed或模型。Windows只编辑、读取源码、Git/文件哈希、公开文件暂存及同步，不执行项目测试/数据分析。
- **测试与结果**：[RUN] 首版61项、扩展67项合成合同通过；最终版本计数与receipt以本报告末尾完成记录及execution manifest为准。包括逐request/memory/transcript/stop/legacy等价、私有隔离、本地板、No-A2A答题、实际bytes/CRC/ACK/ARQ/截止/整数预算/部分未服务量和GOSC outage/FBL概率接口。不是LLM缓存或实际任务重跑；CI不适用于确定性工程合同/完整文件盘点。
- **失败/负面证据**：[RUN] SSH首次两次被关闭，恢复后继续；首轮HPC GitHub raw读取超时failed保留。数据出现重复题、证据重叠及2条support/context异常，保守划分严重失衡；没有删除/修复/替换不利记录。
- **与原 GOSC 的差异**：新增独立QA接口，绝不标成原GOSC科学结果；仅可选复用原success_prob公式。未迁移Search位置、Lc、奖励、ToM/G0/G1，也未改变旧FIFO/source filter/BF/无线默认配置。
- **公平性与泄露检查**：agent view只复制question/自己的context；不含gold/peer/raw/context_raw/level/score/thread_id；admission不读receiver memory。own生成和已交付peer才入本地板；全局transcript仅审计，不注入请求。源答案允许外部发布，No-A2A不人为禁答。原始reference、输出与gold都留离线信任域。进程级恶意代码安全沙箱未实现，不作该保证。
- **成本**：[RUN] 公开数据11,996,959bytes、源码与许可/README不足64KiB；不下载模型、不安装依赖、不使用付费API。模型调用0、真实任务episode0、训练0；无GPU任务。实际run秒数/产物与同步开销见下表及manifest；合成帧uses是合同fixture，不能冒称真实任务通信成本。CPU service系数为显式合成slot，实测Python process ns另列，部署CPU/模型时间Pending。
- **可否进入下一阶段**：无模型接口工程合同在已测支持域Go；路线仍Conditional Go；数据分组/异常处置、真实模型上下文/超时能力及完整运行预算Pending。当前真实任务运行不放行；G1/GP-ID科学No-Go保持，单整消息内容排序主张No-Go保持。
- **用户需要批准的下一步**：先审阅本报告的数据分组及异常处置，再形成唯一开发问题清单与最小Full/No-A2A能力诊断预算；本轮不选择“答得好”的问题、不调用模型或自动开展后续任务。不提交/推送Git，验收交付后停止。

## 1. 数据身份、实际分母与限制

[RUN] 正文完整大小11,996,959bytes，Git blob SHA-1 `9cfc774f5828bb7b811612a16d0f7d209db627d7`；SHA-256 `ce65640b566e70098c540b9c814768c9ff5d8544a4cb25162a3872ac9c3bb331`。原始bytes存HPC登记outputs，取回后仍为忽略产物，不入Git。HPC raw超时后Windows只下载/哈希，scp暂存同一公开文件，HPC重新核身份并解析。

| 核验项 | 实际结果 | 解释 |
|---|---|---|
| 记录/难度 | 300；easy200/hard100 | 此次由正文核实，先前仅README声明 |
| ID唯一性 | 300唯一、0重复ID | 不能因此认定独立问题N300 |
| 规范化问题 | 200唯一；100个重复组，每组2条 | 大小写/空白规范化；不是所有语义改写去重证明 |
| 重复组 | 100组答案完全相同、context均不相同 | 合法数据变体仍不可跨开发/校准/评估拆开；本轮无删除 |
| 同一记录双agent证据重叠 | 100条共享article title、94条共享完整sentence、0条共享完整support triple | 不意味着所有证据严格不相交；也不等于在线读取gold。support triple包括title/index/text，不能由0推断无语义重复 |
| schema/一致性 | 所有300条具有question/answer/context/支持字段；2条出现support索引/文本精确匹配异常 | audit的`schema_errors`将语义一致性也列入；不能称全部数据无异常 |
| 额外离线字段 | context_raw300；thread_id/retry_count各100；source_id/_id未见 | 这些不进入agent或估值器；未恢复完整HotpotQA原始来源身份链 |

异常记录：index244 `sample_178_e0e09ec3`、index245 `sample_78_e0e09ec3`。followup证明对应article存在，部分非空支持句在文中其他位置；还存在空支持句。没有自动改索引、删空句或换题。当前只实现context输入；support模式仍不支持，不将本次异常解释成全文任务一定不可解。

实际context UTF-8长度（不是模型tokens）：Alice最小4504、中位顺序统计量7759、最大16492bytes；Bob3714/8185/14292bytes，未含system/question/history/board。需要未来固定模型tokenizer/context配置检验，不能沿用历史1024上下文短JSON能力验收，也不能由bytes直接算tokens或无线成本。

## 2. 划分可行性与明确不放行项

[RUN] 用相同ID、规范化问题、共享article title或完全相同support text构成无向连通分量，得到38组，最大242条。按组ID列表SHA-256的公开20/30/50桶规则给出**提案**：development9、calibration17、held-out274；未冻结为可执行划分，未选择真实诊断问题。

[HYPOTHESIS] 该保守分组把共享distractor也连起来，可能比必要条件更严格；它展示的是分组约束，不是“该benchmark只有38个统计独立样本”的证明。不能因为比例不好看就事后拆开242组、忽略共享文章或直接按行随机分。若未来决定只按源问题/支持文章隔离，需要明确修订研究协议、说明distractor重叠暴露并获用户决策，不能隐式改变本轮规则。

所有300条本轮经过离线结构/重复审计；没有模型输出或任务效用曝光。公开题库预训练污染、语义改写重复、模型记忆、原始数据构建过程仍不能排除。数据README的CC BY-SA声明与代码MIT分别保留；本轮不发布派生数据，也不新增法律适用性保证。

## 3. 工程验收的支持域

[CODE/RUN] 最小应用固定Alice先/交替、原模板、self full、peer visible、本地R板、原首答案规则。可靠传输采用实际分片、ACK与有限非零服务，在12种响应fixture×2提示族逐项核对原源码；测试同时覆盖缺MESSAGE、重复R、多A、placeholder/空A、boxed、早答和未答。完整请求字符串相同，而不是只比最终分数。

有损合同为合成故障注入，保留UL/DL/ACK/CRC/重试费用及截止未接收量；没有运行任何真实题。无通信能用本地信息提交最终答案，不自动获得peer记忆。最后ACK丢失的接收状态不撤回；应用可见时间明确晚于重组/传输barrier和应用CPU服务。

可选GOSC概率接口对原outage/FBL与实际frame uses做合同检验。仍缺真实任务外生随机信道/跨策略CRN、共享UL/BF迁移、实测CPU到slot映射、LLM模型时间和独立Reasoning环境的概率桥依赖。**G07仅合成序列传输合同部分Go，完整部署/公平前沿Pending**；不应把它当正式无线实验就绪。

私有信息边界、分母和身份合同只在已测接口支持域成立；Python可信controller的代码审计不能代替操作系统权限隔离。所有测试无真实HTTP，原credential loader用拒绝构建/网络的stub替代。

## 4. 运行与证据入口

完整命令、Git dirty/source sync哈希、资源与产物索引见各run `manifest.json/status.json/artifacts.json`。唯一数据来源为固定公开MASBench版本；fixtures没有数据集题目。所有失败保留。

| run ID（research/sync/runs下） | 实际状态/耗时 | 作用 |
|---|---|---|
| hpc-masbench-data-audit-20261103 | failed/exit1，30.895749s | HPC raw请求超时，非数据空或schema失败 |
| hpc-masbench-data-audit-v2-20261103 | completed/exit0，0.395099s | staged bytes重新核验、完整结构/重叠/分组审计 |
| hpc-masbench-adapter-contract-20261103 | completed/exit0，1.101604s | 61合成合同通过，旧结果保留 |
| hpc-masbench-data-followup-20261103 | completed/exit0，0.143353s | 200问题/100变体组/异常进一步只读核查 |
| hpc-masbench-adapter-contract-v2-20261103 | completed/exit0，1.284288s | 67合成合同通过，加入时间/概率桥及legacy汇总 |
| hpc-masbench-adapter-contract-v3-20261103 | completed/exit0，0.683723s | 最终67项全部通过，显式核验部分服务未接收/不可用量；pytest0.27s |

原始证据：`hpc-masbench-data-audit-v2-20261103/outputs/{reasoning.json,data_audit.json}`；followup的`data_followup.json`；各合同的`contracts.xml/contract_acceptance.json/wire_trace.json`。本地回传完成状态与最终源码版本以追加完成记录和[experiment_manifest](../logs/masbench-adapter-contract-2026-11-03/experiment_manifest.json)核对，不能将run completed自动当作文件均已回传。

## 5. 科研判断

本轮识别了运行前必须处理的数据独立性与上下文规模问题，并完成有限接口的可审计实现。尚无任何证据证明Full下可解、消息有实际增量价值、调度改善任务质量或适合发表。当前不能从67合同“通过”推导G1复活或复杂估值训练值得进行。

下一决策应是数据异常/分组规则与开发注册表审阅，然后另批完整预算的最小模型能力及信息依赖诊断。未建立识别空间时维持停止规则，不增加模型复杂度挽救负结果。本轮交付完成后停止。


## 最终完成与回传核验

[RUN] 最终源码的67项合同通过，exit0；source sync `20261103T025247Z`，762文件、SHA mismatch0。最终receipt `20261103T025330Z-a32cbc.json`，新增回传43,888,410bytes（含前一合同run与runner源码快照，不是本轮新任务数据大小），`all_outputs_mirrored=true`，receipt写回HPC。原数据审计超时失败及全部早期通过记录保持原状态。

本地轻量 `verify_management.py`核对所有六个run的manifest/status/产物哈希、最终测试XML、原始数据文件SHA、最终源码与HPC执行snapshot一致、73份冻结源码及保护报告不变，输出`file_management_passed`；`git diff --check`通过（只有既有LF/CRLF提示）。未在Windows运行pytest或数据分析。

最终代码之外的报告、日志、入口和执行索引更新属于交付管理，源码同步状态见本轮task_log末尾；不回填改变既有run的源码身份。实际命令见[执行索引](../logs/masbench-adapter-contract-2026-11-03/experiment_manifest.json)，所有模型调用/真实任务/训练仍为0。最终判断：**工程支持域Go；数据分组/异常与真实能力诊断Pending；科学No-Go保留。**


最终文档同步限制：[上行状态记录](../logs/masbench-adapter-contract-2026-11-03/final_upload_status.json)。所有HPC验收产物已经完整回传；最后报告/状态/日志/许可副本上行两次在SSH初始连接超时，最新文档目前只在本地。已执行的Python代码与最终HPC snapshot一致，不影响已完成测试，不把该上行失败冒称实验失败或测试未回传。连接恢复后可补本次文档同步；本轮到此停止，不自动运行模型。
