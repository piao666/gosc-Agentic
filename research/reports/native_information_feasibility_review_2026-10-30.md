# Native-Information Task Value：研究可行性与审稿审查

日期：2026-10-30（Asia/Shanghai）。审查基线：`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`。本文与[技术规格v1](../protocols/native_information_value_spec_v1.md)组成交付。角色是按拟投稿研究的证据标准进行自我审查；作者身份、署名与投稿决策由真实研究人员/导师决定。

## 1. 审稿结论

**静态设计交付：Go。未来有界shadow的技术可行性：Conditional Go；本轮不执行。将G1作为已验证学术贡献、启动效果campaign/扩N/训练：No-Go。**

[CODE/推导] 在真实admission入口，现有发送者局部信息足以定义不额外同步的G0/G1；源码没有迫使我们读取receiver私有状态。新规格解决了上轮候选定义中未展开的Lc/队列记账、权重/回退/归一化、接口范围和机制诊断问题。

[HYPOTHESIS] 然而，G1只是“已知意图/位置附近的belief变化”代理。它既未识别真实接收端边际收益，也没有任务收益、成本节省或新颖性证据。对期刊审稿人，**目前不足以支撑正向方法论文**。只有同状态诊断证实它超出G0/统一尺度/已声明动态price的作用，且实际成本可接受，才值得另审更下一步。若没有实质区别，应停止本估值路线，不增加模型复杂度。

## 2. 本轮完整阅读范围与版本事实

[RUN，本地管理] HEAD与用户指定SHA一致。完整分段阅读根AGENTS、总说明书、10/29决策报告、GP-ID校准报告、BF工程验收报告、`voi.py`、`schemes.py`、`belief.py`、`agent.py`、`simulator.py`和相关native wire/适配/局部知识/GP-ID/BF/causal service/Periodic/配对噪声源码。`realistic.py`核查平行候选/传输相关段，未宣称v1支持该路径。阅读身份与定位见[证据索引](../logs/native-information-review-2026-10-30/evidence_index.md)和本轮reading_manifest.json。

初始dirty仅为上一轮`research/README.md`、10/29决策报告与日志；本轮保留，不改写。所有新内容另建文件，既有raw outputs、失败run、冻结协议、GP-ID No-Go及BF支持域结论均保持。没有SSH、同步、项目测试、数值诊断、统计、仿真、训练或Git提交/push。

## 3. 上一阶段证据如何约束本设计

| 已有事实 | 对本轮的约束 |
|---|---|
| [RUN] GP-ID 13×12=156任务，5主要比较0组达到联合门槛；paid-pose对periodic平均慢33.83slots、通信比2.142032、逻辑CPU比3.664153 | 不能以付费位置已有正效应为前提，也不能把免费字段存在当成新方法必然有净收益 |
| [RUN] 共同native-age下位置增量gain0；共同paid-age下gain1、95%探索性CI[0,2.67] | 没有支持增加位置估值复杂度的收益依据；不证明任何状态普遍无价值 |
| [RUN] native-age/public通信比0.543817，但任务gain−3.42、CI跨0，CPU比1.063354 | 必须同时比较门槛/显式价格与内容价值，不能只报告少发消息 |
| [RUN] bits/AoI 7选包违规，原审计blocked；BF485旧测试/7修复/192兼容及短合同通过，效果N0 | 新比较共同使用合法BF后端；旧违规效果不能直接拿作通过合同的基线，BF工程Go不替代科学证据 |

来源：[GP-ID校准报告](information_calibration_results_2026-10-27.md)、[BF报告](budget_selector_acceptance_2026-10-27.md)。上述均为既有HPC事实，N为12个独立world而非156，不是本轮新算的CI/测试。

## 4. Major concern 1：Lc是否已经含候选EVID

### 4.1 源码判定

[CODE] `gosc/simulator.py:214–258`将自己感知写入`pending_llr`；`schemes.py:341–361`将通过source filter的记录写入FIFO/queued_llr。`native_paid_adapter.py:34–44`另建local视图，`:65–84`只在本地收到task时写`local[i].Lc`。因此不能把`local_llr=Lc+pending_llr`或`Lc+queued_llr`拿作新评分基准再加候选D。

重要反例是“自己task先收到、ACK丢失”：Lc中已含该记录，FIFO仍可能保留。但`:96–109`的outstanding守卫不允许这时估值；ACK在`:120–132`移除记录/queued_llr后才开放后续入口，收到task列表在`:133–135`处理。重复task由`:66–69`按(receiver,source,id)幂等。反过来，ACK先收到不代表本地Lc已经含该记录，pending_llr仍可能保留它。

**审稿判定**：[CODE/推导] 正常原生流程的**真实估值前状态**支持候选与本地已融合自身Obs不相交；任意中途快照不支持。记录身份不能由两个LLR数组相等/不相等来判定，相同cell上的不同Agent观测仍是不同证据，不能为了“去重”删掉。

### 4.2 必须补的合同

[HYPOTHESIS] 未来应从本发送者已解码自有payload建立本地Obs身份账本，在真实入口验证不相交。任何重合、同(agent,t)不同内容、缺本地历史、手工注入重复等都阻断该诊断，不通过减Lc/删FIFO补救。codec不保证一Agent每slot唯一Obs，旧手工fixture不能自动视为支持域证据。

**状态：静态条件解释通过；实测不重复计账合同未运行。** 不能把静态推导写成全轨迹已验证。

## 5. Major concern 2：目标函数仍是importance代理

[HYPOTHESIS/定义] G0=`Σ_live |sigmoid(L_i+D_prefix)−sigmoid(L_i)|`；G1是同一d的空间加权和。v1权重固定β1/2，peer当前局部INTENT优先、缺失回退最后收到位置、都缺失回退均匀核；对传感足迹距离取正核，在live区域均值归一化。权重有界，全部缺失/均匀时G1退化G0；精确定义见规格§4。

三个潜在拒稿理由都成立，不能靠术语规避：

- 大belief变化可能是噪声或无关新区域，不意味着更准确；G0没有正向reward语义。
- 更接近公开意图也可能只是重复大家已经知道的区域，或追随过时计划；G1没有peer私有belief、更新后的真实target和可靠送达状态。
- 原ToM已有行动分布/距离/避让，比单一空间核更直接；G1是否更好只能用低成本/鲁棒性或实际任务数据支撑，不能靠“加入任务权重”宣称升级。

规格将G1命名为**本地任务区域加权belief变化代理**。它不宣称接收端真实收益预测，不使用JTCM/BANDMAS等外部方法的新事实作优越性依据；本轮未做新文献检索/优先权核验。G0已有先例；G1的论文新颖性尚未建立。

## 6. Major concern 3：固定候选可能让G1退化为门槛

[CODE] `WireGOSC.build_groups`每rate只给最长可装FIFO前缀，全部EVID共一个Group，不存在任意挑观测的接口。若所有rate对应同一个prefix u，且G0>0，则`G1(u)=a_t G0(u)`使同次各EVID Option共同缩放。即使空间w很不均匀，也没有区分不同内容；若多个prefix的d是同一空间向量的比例，同样退化。

[推导] 这一缩放只作用EVID，仍可能改变它与CONF/INTENT的竞争或码率净值；不能直接断言它等价于改变**全局**price。只有全部组共同正比例缩放才具有理想全局price/f等价。规格因此同时设置：G0固定尺度、同次EVID尺度shadow、原Native-Age/显式全局价格与仅EVID-age参照。

不要求所有有效设计都翻转**原始值**顺序：即使prefix价值都随长度增大，内容分布改变价值/成本取舍，也可能在`V−pC`层改变不同prefix的选择。因此诊断同时比较原始/期望/净值三层排序，并要求排除同次统一EVID尺度，不能只数浮点变化或只数发/不发。

**判定：高风险但尚未证实退化。** 如果未来没有超过尺度/声明价格对照的内容级选择变化，当前内容排序主张No-Go；不通过加prefix/改FIFO/更多模型救此版本。

## 7. Major concern 4：控制变量与强Periodic不能写成虚假一致

[CODE/设计] 主轴G0/G1/Public-ToM只经EVID钩子替换原始值，CONF/INTENT value_hex、catalog结构、source filter、wire/信道/率/UL/DL/CPU合同与BF保持。单纯把WireGOSC的mode改成bits/tv会影响CONF/INTENT或触发mode拒绝，不能这样实现。可在独立扩展保持tom构造、仅重写evidence_voi，明确方法ID。

原Native-Age全组缩放，显式动态price改变所有类型的净值；它们是**有意超出纯EVID轴的强门槛参照**。强`WirePeriodic`更是独立剩余预算admit，候选生成/selector不是GOSC/BF。为保留它又保证归因，规格区分严格EVID周期门控-BF与原生强Periodic系统参照，后者共同验硬预算/wire，不伪称同BF。同filter比较为主，旧k8/eps0只作为另列历史锚点。

**判定：控制轴已写清；任何“所有基线同候选/同BF”的笼统表述应删除。** 此分层不减弱强Periodic参照，也不允许在主G0/G1中隐式改变候选或状态同步。

## 8. Major concern 5：量纲与选参可能掩盖弱方法

[HYPOTHESIS/设计] 本地L1变化、ToM效用、Age的单位不同。规格规定按world隔离C_norm/C_select/评估，先固定单位换算，再对所有family开放共同有限EVID尺度与price预算，使用相同任务/通信/CPU约束与tie规则，保留全部失败/无资源支持点；ToM也可校准EVID尺度，不能只给G1自由度。G1的核/β不额外扫。

平均权重归一化并不令不同prefix的G1/G0相同，也不能令CONF/INTENT相对EVID尺度天然公平。归一化无正值必须保留并阻断，不能删除world或加epsilon制造可调信号。相同校准无线均值也不保证封存评估成本匹配。

**判定：规则可审阅，N/world/资源界/执行身份未冻结，不是可运行校准协议。** 不使用旧GP-ID N12挑新方法后再当独立验证；不以未显著优越事后改作非劣效。

## 9. Major concern 6：低成本尚未成立

[CODE/推导] G1新增评分可按O(BA+u_max F+PA)计算，G0少核权重项；不需要LLM或新增同步。但保留INTENT估值仍须原TeamModel构造，不能声称完全去掉ToM；原wire对每个前缀重新编码的工作量不因改值消失。

[CODE] .001s的valuation_seconds是现有逻辑CPU假设，不是G1/ToM全路径实测。对同一快照shadow共享D会更快，但部署G1没有G0替它预处理，不能把共享加速算成部署省CPU。日志/拷贝/CRC/实际UL/DL/重试与接收处理仍收费。若未来绑定实测费用到slot时钟，需共同审阅，不在本轮偷偷改服务。

**状态：实际成本全部未测。** 规格要求独立冷/热路径、分段process/wall、内存和宿主观察中性；固定CPU预留与实测成本单列。计算量公式不能替代净收益数据。

## 10. 最小诊断与停止决策

[HYPOTHESIS/未来提案] 规格§8提供有界shadow设计：仅两已曝光成本world、24slot、每sender前8个真实有EVID入口，最多96快照；不选reward或有利事件。新增N=0，缺字段需经合同的被动导出，不能回填旧历史。单worker、120s/32MiB仅为待审预算提案，未运行/未批准。

| 未来诊断结果 | 审稿判断与行动 |
|---|---|
| 任一越权/重复未验证/目录改变/观察改宿主/预算失败 | Hard No-Go，先定位合同；不进入收益试验 |
| 无多prefix机会或有效本地输入覆盖不足 | Pending coverage，效果推进No-Go；不自动扩样本寻找有利场景 |
| G1=同次a_t G0、或三层均无实质不同prefix排序变化 | 内容价值No-Go；不加复杂模型 |
| 只改变EVID开关/类型竞争，声明尺度/价格对照可以解释 | 仅门槛作用，当前内容排序主张No-Go |
| 分数/排序改变但固定菜单下BF选包始终相同 | 当前只改估值的闭环路线No-Go，不改FIFO掩盖 |
| 两world都有实质内容级排序/最终prefix切换，超出统一EVID尺度且合同通过 | 仅机制Conditional Go；还需审查任务相关性/成本，不算方法成功 |
| 实际估值更贵且没有任务收益依据，或无法可靠测成本 | 分别No-Go/Pending，不通过更多重复/模型直到结果好看 |

即使shadow通过，仍不能声称“选对消息”：没有真实任务标签，只证明“选了不同消息”。后续若确需同前状态离线deliver/drop，必须事前固定干预/外生流/后续策略与指标，并将未来reward严格限制在离线评估；不在本轮执行或生成标签。

## 11. 潜在期刊审稿意见及可接受答复

| 审稿问题 | 当前可接受答复 | 尚缺证据 |
|---|---|---|
| 这不就是TV加一个空间核吗？ | 是一个简单候选；G0为已有思想，不能靠组合主张创新 | 与强简单基线成本匹配的任务证据、新颖性核验 |
| 你预测的是receiver价值吗？ | 尚不是；只计算发送者本地代理，接收者私有状态不可见 | 可检验的条件价值/实际任务关联 |
| Lc已经有待发证据，你算了两次吧？ | 任意时刻可能重合，真实admission守卫与ACK清除提供条件保证 | 原生时序+本地身份账本的运行合同 |
| 统一调价能实现同样结果吗？ | 有显式全局price和EVID尺度对照；不先声称不可替代 | 有限声明工作点的shadow差别，及独立闭环对照 |
| 你偷偷增加候选/调整过滤器了吗？ | v1禁止；比对同状态结构与非EVID value_hex | 实现后catalog/wire合同 |
| 为何比原ToM更好？ | 目前无法回答“更好”，只提出不同代理/成本假设 | 全路径计时、任务—资源前沿与区间 |
| 选择变化就是任务收益吗？ | 不是；shadow不含下游任务检验 | 冻结的独立效果设计或合法反事实 |
| 原来付费pose失败后是不是换名字继续试？ | 新设计明确无新增同步，并预先给出退化/停止条件，原负结果不撤销 | 不按诊断结果继续加模块/扩样本的执行纪律 |
| 能代表LLM Agent/真实无线系统吗？ | 当前仅Planner search与模拟服务，不能这样外推 | 本版本不存在的独立外部效度证据 |

## Research Task Report

- **Research Question / Hypothesis**：合法native信息下的区域加权EVID代理是否有超出G0/门槛的机制；本轮只做静态设计。
- **已核验前人工作**：[PAPER，沿用既有映射] GOSC Eq.(4)/p5、Appendix p12及Eq.(5)/p5对应原ToM/调度；本轮未新增论文/出版状态核验，不宣称首次。
- **实际阅读源码**：[CODE] 014b85d指定源码与相关原生局部接收/记账/估值/selector全链；完整/部分阅读标注及行号见本轮证据索引。
- **本轮新增或修改**：新增native_information_value_spec_v1.md、本审查报告及本轮日志/阅读身份/静态manifest/管理校验；旧报告和research/README.md不再修改。
- **实际运行**：[RUN] 本地git status/rev-parse/remote/diff、rg/Get-Content与轻量文件/SHA/文档校验。无HPC计算；真实读取与核验记录见task_log_20261030.md。
- **测试与结果**：本轮项目测试、shadow、任务实验、统计与训练均未运行；旧485测试/156任务不计成本轮新结果。
- **失败/负面证据**：原GP-ID科学No-Go/工程blocked和全部失败原件保持；本轮指出G1非VoI、单prefix退化、成本/数据缺口。读取中输出截断的必读正文已分段补读，推测不存在的测试文件名已按真实文件定位，不作已运行断言。
- **与原 GOSC 的差异**：仅定义未来独立EVID估值扩展，不修改核心/默认/历史结果；G0并非新方法贡献。
- **公平性与泄露检查**：仅本地Lc/收到意图与位置、真实入口、身份不相交；冻结候选/filter/服务/BF主轴；强Periodic与全局价格参照有意差异单列。
- **成本**：仅文档/文件管理，新任务N0、0新收费API/训练/模型调用；助手token与管理耗时未测。G0/G1实际计算费用未测，不虚报0。
- **可否进入下一阶段**：静态交付Go；未来有界shadow技术Conditional Go但执行未授权；学术正向贡献、效果campaign/正式test/扩N/训练No-Go。
- **用户需要批准的下一步**：本轮要求为交付后停止，现已按此完成；不自动启动实现、诊断、Git提交/推送或新研究阶段。
