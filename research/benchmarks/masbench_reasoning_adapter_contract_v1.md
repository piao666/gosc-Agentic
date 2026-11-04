# MASBench Reasoning 最小无模型适配实施合同 v1

日期：2026-11-03。用户授权范围为数据核验、无模型适配实施及HPC合同验收；不是任务能力或无线科学实验的运行授权。原静态规格保留，本文件说明已实现的有限接口及未实现边界。G1/GP-ID科学No-Go不变。

## 1. 实现与权限

[CODE] 独立包 `extensions/masbench_reasoning/`，不修改GOSC核心、旧扩展或第三方原始活动代码。只提供 `run_fixed` 合成固定字符串入口；没有真实模型连接器、数据集任务循环、训练器或线上估值器。

| 原生接口 | 本地接口 | 支持域与信息边界 |
|---|---|---|
| loader context构建、runner初始化 | `application.private_view/PrivateView` | 从离线记录复制question及本方context；不保留raw/gold/level/context_raw/score/thread_id/peer回指；仅context模式 |
| system模板、`_build_messages` | `LocalAgent.__post_init__/request` | 原模板注入，保留空context回退；自身前缀assistant、其余user，顺序不变 |
| 原生成后处理 | `generate_fixed` | 注入固定响应，原strip/姓名前缀/self full memory；没有模型调用 |
| MESSAGE与answer parser | `peer_payload/parse_answer` | 匹配原活动regex/大小写/fallback/空答案行为，不擅自加强schema |
| 原shared_blackboard | `add_facts/receive` | 每agent仅自生visible与实际收齐peer bytes建本地R列表；strip、精确去重和顺序与原生一致 |
| 传输barrier | `ContractTransport.transfer` | 单条在途消息；两跳串行逐片，有限ARQ；没有后台未登记drain |
| 首答案停止 | `run_fixed` | 在共同barrier及应用处理后解析source本次visible；No-A2A仍可提交本地答案，截止后不计timely answer |
| 原通信/F1/汇总 | `evaluation.legacy_* / f1` | 旧words/F1非None分母/效率独立保留，不当作真实无线bits |
| 新评价 | `evaluation.summarize` | planned/start/completed/error/unanswered/not-started；全启动分母，失败0，未启动显式列出；error与unanswered可重叠 |

[CODE] 这是可信程序之间的白名单数据接口，不是对恶意Python插件/同进程代码的安全沙箱。离线controller可持有全数据用于评测和记录，但不将其传给agent或admission callback。callback只获sender编号、该sender payload bytes和turn；没有receiver memory、gold或未来信道输入。

## 2. 帧、计价和时间

[CODE] `wire.Frame`网络字节序24byte header+4byte CRC32；magic/version/kind/episode/message/src/dst/created/fragment index/count/payload length均实际编码。四种DATA/ACK拓扑字段验证，CRC覆盖header与payload。payload每片最多16bytes，空body仍有一片；分片可以切开UTF-8字符，只有完整重组并strict UTF-8通过后才能进应用。消息ID按episode作用域防重复；运行命名空间episode唯一性仍由未来driver保证。

本次**合成合同配置**，不作为未来能力诊断/部署的参数冻结：rate4bit/use、预算100uses/slot、TTL与任务deadline各100000slot、每片每hop最多3尝试、RTO6slot、每服务CPU阶段1合成slot、body cap65536bytes、单消息在途/无并发。所有原生rate集合值均可表达；低rate帧不可装显式unserved，不删除这些rate来伪造可行性。ACK同控制rate4，非免费。

[CODE] 每个实际帧尝试 `ceil(8*len(encoded_frame)/rate)`，失败/CRC错误/ACK/重复同样收费。source DATA与receiver DL_ACK计UL，edge DATA与edge UL_ACK计DL。串行服务确保单方向slot预算，**不声称验证了共享上行、多消息BF调度或并发资源分配**。不进行任意半帧服务；截止留下的整帧/原消息未接收量与已有消耗保留，不把部分UTF-8交给模型。

UL已解码但ACK耗尽时edge仍可转发；末片DL_ACK耗尽不能撤销已收到的body。重复片只计重传/ACK，不重复进memory。重试不重新生成消息。最终barrier解决后没有后台队列；未接收片以显式丢弃/未完成状态结束，未来若增加drain必须另行计价。

[CODE] 分开记录payload创建/offered/enqueue、编码与解码CPU服务、frame start/end、CRC接收/重组完成`receiver_receive`、barrier_end、应用CPU处理后的`visible`、下一次request的monotonic时间。`delivered`仅指传输重组，`visible`还需应用处理未过deadline。最后ACK等待可能使body已经收到而应用未及时可见；这是本最小顺序barrier合同的明确限制，不称并发端到端协议的最小时延。

实际Python `process_time_ns`按request构建/固定响应处理/payload、编解码CRC、重组、板和parser等阶段记录；不是LLM推理时延/CPU能耗。合成1slot系数只验证队列因果性与截止规则，**没有实测部署CPU映射或GPU推理成本**。模型usage为未请求/不可适用，不用words估成tokens。审计日志/pytest开销由run总耗时另列。

## 3. GOSC信道复用的有限范围

[CODE] 可选 `GOSCProbabilityContract`只读取现有 `Channel.success_prob`，统计CSI、公开UL/DL SNR及实际帧uses传入outage/FBL公式。成功抽样值必须由合成fixture逐key显式提供，缺值即失败，不偷偷新建未来事件或用QA答案决定信道。key为episode/message/kind/fragment/attempt。

当前仍未实现/验收：真实campaign的外生随机场与跨策略CRN、QA几何/公开SNR实验点、共享上行/BF-selector迁移、模型时间到无线slot映射、独立Reasoning venv内的NumPy桥接环境。桥接合同在已有GOSC venv运行，未安装新依赖。**接口公式合同通过不等于真实随机无线实验已经可执行。**

## 4. 原生等价与反证边界

[RUN/验收入口] `scripts/masbench_reasoning_contract.py`通过HPC登记，仅合成字符串；参考文件逐Git blob核验到MASBench `c0301a6`。第三方原件位于本轮日志reference目录，保留MIT版权/许可；生产包不会导入原api_key_loader。测试以拒绝网络的stub替换其导入，原OpenAIAgent仅以固定响应client替身运行；没有凭据读取或HTTP。

逐turn比较原活动源码与适配器：role/content/order requests、双方memory、transcript、首停止位置/答案、旧comm words、F1及汇总字段；覆盖base/protocol、fallback、重复R、多A、placeholder/空A/boxed、早答和未答。非零有限airtime仍等价，说明接口不依赖瞬时交付stub；仅对这些固定响应及配置成立，不是任意LLM/有损条件的普遍等价证明。

负向合同检验无通信仍可答、丢失R不能从另一方全局板恢复、幂等、错误CRC/UTF-8/路由、各hop丢失与ACK失败、低rate不可行、部分服务/截止及分母。账本用独立struct/CRC/整数公式复算，不仅调用被测类自证。

任一隐藏状态注入、无损输入差异、漏算ACK/DL、失败样本排除都应阻断后续能力诊断。通过这些工程合同不撤销G1/GP-ID科学No-Go，也不使单整消息接口具备多个内容候选的排序自由度。

## 5. 当前研究关卡

数据实际审计与最终合同证据见[验收报告](../reports/masbench_reasoning_adapter_acceptance_2026-11-03.md)。数据异常、重复题与保守证据分组须先审阅，不按行随机切分。之后才可另行冻结唯一开发问题、模型digest/context/输出上限、显式超时/重试、完整Full/No-A2A预算；本轮不开始该诊断。
