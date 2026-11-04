# Native-Information Task Value：静态技术规格 v1

日期：2026-10-30，Asia/Shanghai。源码基线：`014b85dfc472c45d8ea5f15e83e0c1ed8e938daf`。状态：**静态规格已定义，未实现、未运行、非可执行预登记**。本规格中的常数是候选v1设计选择，不是实验发现；未来执行仍须独立冻结源码、采样清单、资源预算和授权。

## 1. 论文问题与三类量的区分

[HYPOTHESIS] 在非oracle、正交上行、lossless typed wire、Planner search的既有服务中，不新增接收端状态同步，只替换EVID价值，检验本地收到的任务区域信息是否能带来区别于普通belief变化与统一门槛调整的选择，并最终改善实际任务—通信—计算前沿。当前没有此收益证据，不外推LLM/Rescue/共享上行。

| 层次 | 定义 | 本规格能否直接得到 |
|---|---|---|
| 本地belief变化 | 对发送者已收到的belief加入候选证据，得到概率场变化`d` | G0/G1直接计算；不是正确率、奖励或接收者真实belief |
| 接收端预测收益 | 在接收者近似策略/知识模型下的预期行动效用变化，如原TeamModel | Public-ToM提供代理；G1没有接收者策略模型，不冒称接收端收益预测器 |
| 真实任务收益 | 相同决策前状态下实际投递/不投递导致的下游完成时间/成功率变化 | 本轮与shadow均得不到；需要另立离线反事实或闭环评估，未来reward不得在线使用 |

[CODE] G0与`gosc/schemes.py::GOSC.evidence_voi`的TV分支同类；G1是空间加权扩展的候选，不是已证实新VoI。原ToM已具有任务、距离和意图机制。候选论文贡献须来自严格比较后的成本/任务证据或可信边界，不能来自命名。对应说明书§6.1–6.7；[审稿结论](../reports/native_information_feasibility_review_2026-10-30.md)。

## 2. 支持域与不变项

[CODE/规格] 未来只考虑显式独立扩展入口，不改`gosc/`或既有GP-ID/BF默认。主比较G0、G1、Public-ToM及EVID专用消融须满足：

原生支持条件继续保留：grid在1–32、max_steps不超过512、task=search、tom_oracle=false、shared_budget=0、无LLM Agent、value_mode=exact、overhead_bits=0；原Config的dl_delay/dl_loss为0，由既有service/callback另计实际DL时延/丢失。不得把Config这两个0解释成实际下行免费无损。

- 同一配置、同决策前状态、同source filter（主比较`filter_eps=.02`）、同感知/Planner/stop-and-wait/ACK状态。
- CONF、INTENT组的生成条件、原始/期望价值、排序和所有Option保持；EVID同一FIFO序列、每rate最长可装前缀、一个EVID Group，不能重排/删观测/新增前缀/拆包或增加报文数量。
- 保持codec、envelope/CRC、bits、`symbols=ceil(bits/rate)`、率集合、合法CSI与成功率函数；EVID的原始代理只乘一次既有成功概率。
- 同一UL/DL容量、CPU预留/队列/可见时钟、因果重试下界、有界catchup、丢失与事件索引随机过程；所有native方法不调用`submit_pose`，不读取paid cache。
- 同一`BF-selector-v1::select_feasible`，整数预算/组/成员/有限算术合同、原tie顺序均不变。BF是可行性后端，不保证组合全局最优。

“候选方式/消息数量不变”指同状态下产生相同候选组与Option身份字段；改变价值后，实际选中消息数/频率可以不同，这是结果，不能反过来固定成相同策略。闭环历史会分叉，同候选的严格相等仅在同前状态可比较。

## 3. 必须先满足的信息与不重复记账合同

### 3.1 四个不同的belief/队列量

[CODE] `Simulation.phase_decide`先将每个新`Obs`写入本Agent的`pending_llr`，随后`GOSC.on_step`只把通过过滤的记录写入`pending_records`和`queued_llr`。`NativePaidSimulation.view(i)`返回`local[i]`；其`Lc`在`_local_packet`处理已经本地收到并解码的task后更新，与edge的`self.Lc`不同。

| 量 | 所含信息/更新点 | 用途/限制 |
|---|---|---|
| `local[i].Lc = L_i` | 初始公开prior + 本地收到task中证据的累计融合 | G0/G1唯一基准；包含其他Agent重叠区域证据是合法条件化，不代表同一Obs重复 |
| `agent.pending_llr` | 自己感知后尚未被自己收到广播抵消的证据；包含被source filter拒绝的观测，也可能包含已ACK但尚未自收到的记录 | 既有Planner/TeamModel使用；**不能先加入G0/G1基准再加候选** |
| `agent.queued_llr` | source filter保留且尚未ACK移除的待发记录增量 | 仅过滤/账本；不加入G0/G1基准 |
| `agent.pending_records` | 已保留的FIFO记录；自发task ACK后移除 | 候选内容。非估值时刻可与已收到自己证据重合，不能仅凭变量名假定完全未融合 |

### 3.2 逐事件追踪与条件结论

[CODE] 一次真实估值前入口为`NativePaidSimulation.phase_communicate`的`if not any(k==i for k,_ in _outstanding)`分支，且发生在本slot的`service.tick`之前：

1. 本slot感知进入`pending_llr`，过滤后可能进入FIFO；未因此写入`local[i].Lc`。
2. 选中的EVID进入`_tx[(i,id)]`及`_outstanding`，待发记录仍保留，禁止该sender再选新批次。
3. edge接受只更新edge状态；task ACK和task广播独立送达/收费/丢失，ACK并不证明所有peer已收到。
4. 若自己先收到task而ACK丢失，`_local_packet(i,i,id)`会把记录写入本地Lc并抵消pending_llr，**FIFO可暂时仍含它们**；但outstanding阻止估值。
5. ACK处理移除该task记录并扣queued_llr，清outstanding。适配器在同slot先处理task_acks列表，再处理task_received列表；下一slot估值前这两步均已完成。
6. 若ACK先到而自己task尚未收到，记录已移出FIFO，pending_llr仍可能含旧记录；这也不能用来给G0/G1基准整体加pending_llr。
7. task重播按`(receiver,source,id)`幂等；正常一Agent每slot一Obs，FIFO原对象只提交一次EVID批次，不因重试生成新Obs。

**条件结论**：[CODE/推导] 在正常启动、单一EVID组、未注入/改写记录、真实outstanding为空的入口上，当前候选Obs与已由自己收到task写入Lc的自身Obs应不相交。因此可用`L_i+D_m`表达当前候选的本地条件更新。此结论不能推广到任意中途快照、手工fixture或只含数字数组的离线日志；`queued_llr == pending_llr`也不是所需不变量。

未来诊断必须验证该不相交合同：用本发送者已解码自有payload的**本地历史**建立`(agent,t)`到完整`(pos,det)`指纹的账本，与候选记录核对；同键不同内容、重复候选键、键来源不明或overlap任一出现则标`blocked_evidence_identity`，停止依赖结论，保留失败。一个Obs/Agent/slot是支持域前提，codec本身不保证它（旧手工fixture可能不满足）。不能通过从Lc减去记录、跳过重合观测或改FIFO来“修复”快照。缺本地历史则`unverifiable`，不得当作无重合；不从edge/peer私有日志替代在线输入。

### 3.3 逐字段来源与访问权限

| 字段 | 来源/最早可用时刻 | 用于 | 禁止替代/约束 |
|---|---|---|---|
| sender、t、公开配置 | 本地当前决策入口 | 索引/形状/合法时刻 | 无run seed/世界真值/随机流句柄 |
| L_i、local_declared | `local[i]`，既有`_local_packet`处理完成后，下次入口 | G0/G1的基准和live mask | 禁edge Lc/declared、`local[j]`和事后快照 |
| FIFO `Obs(t,agent,pos,det)` | 自己过去和本slot感知，通过原on_step后 | 前缀D | `t_rec<=t`、sender匹配、网格合法、同键内容唯一；不读未入FIFO的未来/peer感知 |
| peer intent | 当前`local[i].team_intent[j]` | 区域锚点首选 | 是最后本地应用的INTENT，非peer真实target；当前map无创建/接收时间，不新增TTL/排序规则 |
| peer pose | 当前`local[i].team_pos[j]` | intent缺失时回退 | 启动位置是公开先验；EVID后为最后收到位置，可能陈旧/回退；禁`agents[j].pos`/paid cache |
| native_created | `knowledge.native[i][j]`的已有本地EVID时间戳，初始-1 | Native-Age参照 | 不用于G1虚构intent age；与view位置不匹配时诊断失败 |
| 自己target/shared/acked状态 | 自己Agent与已收到ACK | 原CONF/INTENT候选、合法入口审计 | G1权重不额外用自己target；ACK不提供peer送达位图 |
| known、P_s、rate、bits、symbols | 原调度传入合法CSI和公开Channel模型/实际wire | Option层 | 不接入实际未来解码结果；P_s不是完整peer投递概率 |
| 本地自有payload处理历史 | 本发送者自己的接收路径；仅诊断验证/哈希 | 防重复/trace | 缺失不补造；新增只读记录计内存成本，不做价值特征 |

只给估值器不可变的局部`NativeValueContext`，不得传整个Simulation/服务/world对象。Context含Lc/declared副本、peer maps、公开传感参数、sender/t；records/prefix lengths单独传入。候选/账本检查可在可信调度包装层执行，不向G1开放全局审计对象。

## 4. G0与G1的精确定义

以下为[HYPOTHESIS/规格定义]，并非实测结论。网格`C={0,...,n−1}²`，`M_i={c: local_declared_i(c)=false}`，`K=|M_i|`。只使用本地declared，不额外用自己confirmed_pending改变mask。公开sigmoid使用既有`S(x)=0.5(1+tanh(x/2))`。

### 4.1 前缀增量与输出

FIFO为`r_1,...,r_Q`。原wire builder给出每率可装的最长长度`n_r`；仅评价`U=sorted(unique(n_r))`，`P=|U|<=R`。对`u in U`：

\[
D_u=\sum_{k=1}^{u}\Delta(r_k),\qquad
d_u(c)=|S(L_i(c)+D_u(c))-S(L_i(c))|.
\]

`Δ(r)`必须逐条使用同一`SensorModel.apply(zeros,r)`语义：窗口内加llr_neg，正检测cell再加llr_pos−llr_neg。禁止把每条记录的绝对变化相加；同cell的正负证据可抵消，`d_u`以及价值对u不必单调。禁止从整个pending_llr/queued_llr取近似D，或拿ToM已裁剪/已乘成功率值当D。

输出为按原prefix长度键的`{u: G_h(u)}`，有限float64、非负原始值；不返回未来奖励、概率正确率、packet列表或新的候选。若Q=0或U为空返回空map；若K=0则所有现有prefix返回0，不改候选或终止规则。

### 4.2 G0：普通本地belief变化

\[
G_0(u)=\sum_{c\in M_i}d_u(c).
\]

这是网格上Bernoulli occupancy概率变化的L1和，不是网格归一化分布间的KL，也不是LLM不确定性。单位为“cell概率变化之和”；不除以前缀记录数、bits、symbols或K，不奖励新包数量。它对应同mask/同输入的原TV思想；原`WireGOSC`不接受tv模式，未来必须新建扩展，不能把未运行的同wire G0称已验收。

### 4.3 G1的区域锚点、回退与权重

peer集合固定为公开注册的`j!=i`，数量J；不因有利位置挑peer，不读取peer私有状态。对每个peer：

1. 当前局部map存在合法INTENT cell时，锚点`a_j=divmod(intent,n)`，来源标为`native_intent`。
2. INTENT缺失/None时，若局部map有合法位置则`a_j=team_pos[j]`，来源标为`native_pose`；初始公开launch点也属此类。
3. 两者都缺失则用均匀区域核`k_j(c)=1`，来源`uniform_missing`。缺失是没有字段，不等于字段非法。
4. 已存在的非整数（含bool）/越界INTENT、非整数网格坐标、未来记录或ledger矛盾属于输入错误，失败并保留；不得静默fallback掩盖。v1不人为添加intent时间戳、过期阈值、运动预测或新TTL。最后收到的意图可能陈旧，即使比位置更旧也不擅自改变原更新语义。

对有锚点者，公开传感半径为r，`ell=max(1,r)`，采用到其传感正方形足迹的L1距离：

\[
\delta_j(c)=\max(|c_x-a_{jx}|-r,0)+\max(|c_y-a_{jy}|-r,0),\quad
k_j(c)={1\over 1+\delta_j(c)/\ell}.
\]

该核是“上次公开意图/位置附近可能相关”的启发式，不是真实行动概率。空间尾部严格正，避免直接删除无人关注的新区域。r、ell不调参；不以peer ID优先级/真实路径扩权，不额外模仿ToM避让。

\[
q_i(c)=\begin{cases}J^{-1}\sum_{j\ne i} k_j(c),&J>0\\1,&J=0\end{cases},\quad
u_i(c)=(1-\beta)+\beta q_i(c),\quad \beta=\tfrac12,
\]

\[
\bar u_i=K^{-1}\sum_{c\in M_i}u_i(c),\qquad
w_i(c)=u_i(c)/\bar u_i\ (c\in M_i),\qquad
G_1(u)=\sum_{c\in M_i}w_i(c)d_u(c).
\]

K=0按§4.1返回；非live处权重仅存0用于mask。权重对**同一次调用所有前缀/速率相同**，不能按某候选效果重建。live上均值1；由于`1/2<=u_i<=1`，`1/2<=w_i<=2`、`G0/2<=G1<=2G0`。若所有peer缺失、J=0或权重恰常数，则G1退化为G0；这是合法退化标签而非新增收益。β/核固定为v1，不在失败后扫形状/加模型。

平均归一化只消除全场共同因子，不保证每个候选`G1/G0`相同，也不消除CONF/INTENT与EVID之间的尺度效应。新增区域权重不是新信息；若只改变EVID类型优先级，必须按此较弱机制解释。

### 4.4 接入成功概率、尺度与price

对原Option `(rate,bits,symbols,u)`，仅EVID替换为

\[
V_h(o)=\alpha_h s_h G_h(u)\,P_s(rate,known,n=symbols),\quad h\in\{0,1\}.
\]

CONF/INTENT的value逐位沿用Public-ToM同状态结果。`s_h`是离线校准的固定单位换算，`alpha_h`是共同规则的EVID类型尺度；二者不从评估world即时拟合。BF仍优化原`sum(value)−p*sum(symbols)`近似目标。不再除symbols，不二次乘P_s、不乘未建模的peer收包概率。均为本地代理×UL成功模型，不叫全链路预期真实任务收益。

### 4.5 数值与失败约定

- 输入Lc/增量/输出均float64，形状固定n×n；配置和所有中间值必须有限；不允许NaN/Inf作为0或极大价值通过。
- 使用原tanh sigmoid，不更改上游SensorModel。有限L_i+D溢出即显式失败，不能靠截断LLR伪造平稳。浮点饱和得到d=0可以保留，记录`saturated_cells`，不加epsilon制造信息价值。
- 权重分母至少1/2，不做候选依赖的min-max/softmax归一化；越界非负性/界限异常应停止，不自动裁剪为通过。
- 增量按FIFO顺序积累，reduce按固定行优先顺序；每个唯一前缀评分一次，不使用随机tie-break，BF继续原tie顺序。
- 仅诊断比较容差`tau(a,b)=1e-12+1e-9*max(|a|,|b|)`；不修改selector内部严格比较。归一化/缩放乘法也需有限；均零不是“错误数据”可丢弃的理由。

## 5. 源码—接口映射与实现约束（未来，未修改）

| 入口/对象 | 014b85d位置 | 未来仅允许的接入 |
|---|---|---|
| 本地状态与估值时刻 | `native_paid_adapter.py:34–44,65–84,96–140` | 构造只读Context，入口守卫/本地身份观察，不改接收/ACK顺序 |
| 过滤与FIFO维护 | `schemes.py:341–361` | 原样；G1不接入on_step |
| prefix长度与Option/wire | `native_task_wire.py:77–106` | 原build_groups逻辑；仅通过evidence_voi钩子获得G0/G1原始map |
| EVID估值钩子 | `schemes.py:363–384`，由WireGOSC调用 | 新扩展子类重写同签名`evidence_voi(sim,records,prefixes,team=None)`，内部只读Context。WireGOSC仍以tom构造，单独method ID区分，不扩大上游mode列表 |
| CONF/INTENT | `native_task_wire.py:89–96`、`voi.py:122–134` | 同状态值保持；TeamModel构造仍保留，不宣称全部ToM CPU消失 |
| BF入口/版本重放 | `budget_feasible_information.py:67–105`、`budget_feasible_selector.py:99–152` | 独立新入口绑定新scheme，selector函数/参数语义/trace不改；新估值版本写入日志 |
| 服务与随机过程 | `causal_paid_service.py`、`paid_receiver_service.py`、`paired_paid_simulation.py` | 原样，无新增summary/ACK/CPU逻辑放行；只读shadow不能调用valuation_work/submit_task |
| realistic平行路径 | `realistic.py:84–151,403–481` | 已识别存在独立构造/共享路径；v1不接入、不声称覆盖 |

不能先运行完整ToM EVID再覆盖数值却声称省掉那部分CPU。可用原钩子避免无用EVID估值，但CONF/INTENT和TeamModel仍需计算。同状态验收必须核对结构清单`(group_index,kind,cell,option_index,rate,bits,symbols,n_records,payload)`一致；CONF/INTENT的`value_hex`一致，仅EVID value允许变化。成员对象身份在每个独立catalog内满足BF合同，不要求不同策略catalog共享Python对象。

## 6. 复杂度、缓存与实际成本

[CODE/推导] 设网格A=n²、Agent数B、FIFO长度Q、唯一可行前缀数P<=rate数R、`u_max=max U`、每Obs触及cell数至多F（含正检测更新）。只积累到u_max：

- 构造G1核/权重：时间O(BA)，空间O(A)；可逐peer累加，不保存B张网格。
- 前缀D累计：O(u_max F)；每唯一prefix比较sigmoid与点积O(A)，合计O(u_max F+PA)，空间O(A+P)。G0同阶少O(BA)，G0/G1同时shadow时可共享d但计时须另有独立部署路径。
- 不能把prefix价值做简单前缀标量和；belief非线性与证据抵消要求保持D，不能用`sum |Δp_record|`换快。
- 不动原wire size生成：它为每个长度重新编码，现有代码工作量可达对FIFO长度的二次增长；不能把整个build_groups称为O(Q)。本规格只给新增估值的界，不掩盖候选生成/TeamModel/BF/codec成本。
- Context/FIFO深拷贝与全FIFO身份检查另需至少O(A+Q)时间/存储（若含完整检测列表，按实际元素数计）；本地历史账本按已收到自有记录数增长。上述评分核复杂度不包含这些包装成本，计时不得省略它们。
- 跨调用缓存v1禁用；Lc/declared/intent/pose/FIFO每次都可能变，缓存失效容易泄露/错算。调用内只复用p0、weights和唯一prefix值；没有EVID时不运行G0/G1网格循环。

[HYPOTHESIS/计量设计] 未来按`context_copy/validation`、`TeamModel+fixed CONF/INTENT`、`wire/candidate_build`、`G0或G1`、`success_prob`、`BF`、`logging`拆分process_time/perf_counter_ns与峰值内存。测冷调用及独立重复热调用，所有方案相同重复数；序列化/哈希/shadow共享加速不得计作部署估值更快。按world和真实admission机会汇总p50/p95/max与总时间，空/被stop-and-wait阻塞比例分开，不能只报每次均值。

**当前实际耗时、CPU节省、内存峰值均未测。** GP-ID固定`valuation_seconds=.001`是模型预留，不是上述全路径硬件计时；不允许因G1名称简单就给0费用，或把shadow多策略时间加到原宿主CPU队列改变轨迹。若未来要把实测费用绑定任务时钟，需另行共同审阅CPU合同；本规格不修改队列/预留，不能凭shadow声称实测部署净收益。

## 7. 强基线与共同校准规则

### 7.1 两类比较，不混淆控制变量

| 方案 | BF/原候选 | 修改内容 | 识别作用 |
|---|---|---|---|
| Public-ToM | 同BF、同wire/candidates/filter | EVID仍原ToM | 已有强任务代理，不买summary |
| G0、G1 | 同BF、同wire/candidates/filter | 仅EVID代理与共同校准尺度 | 唯一主机制轴 |
| G0统一EVID尺度 | 同上 | 各EVID前缀统一乘固定alpha；其他类型不变 | 排除类型优先级/整体尺度解释 |
| Native-EVID-Age（机制参照） | 同上 | 只对原ToM EVID乘native f | 比较EVID门槛作用；不等价全局动态price |
| 原Native-Age/显式Native-Price | 同BF/结构/filter/服务 | 前者同次所有组乘f；后者全部原值保持、price改p/f | 强门槛参照；这两者**有意超出只改EVID轴**，不能声称CONF/INTENT值也完全相同 |
| 内容权重打乱G1 | 同主轴 | 按§7.3重排空间权重，不动records | 检验区域与内容对应关系 |
| EVID周期门控-BF | 同BF/全部候选/filter | 非周期slot仅将EVID value置0，CONF/INTENT不变 | 严格EVID接口内的简单时间规则；不冒称原WirePeriodic |
| 强WirePeriodic | 原独立admit，不走BF；同wire/服务/信道 | 原CONF优先、周期INTENT/EVID、剩余预算下的prefix/率选择 | 独立系统部署参照；结构/后端与主轴不同，不能用于纯EVID归因 |

[CODE] 现有`WirePeriodic.select`按剩余预算生成选择，不能一边保留该强算法、一边写“所有基线完全同BF/同候选”。v1明确将其放在独立参照层；执行共同硬预算/成员/wire审计，不伪称其内部改用了BF。若研究要求每一项比较严格同BF，则使用EVID周期门控-BF，仍须另报强WirePeriodic以防弱化简单基线。旧k8/eps0保留为历史部署锚点；严格机制层固定eps.02，不能把跨filter差异全部算给价值。

原Native-Age使用本地native时间戳：`mean_age=mean_{j!=i}(max(0,t-created_j))`、初始created=-1，J=0时f=1；`f=1/(1+mean_age)`。同catalog全值缩放的理想目标等价price/f，但BF有限浮点结果须分别核验。仅EVID缩放在存在CONF/INTENT时不等价改全局price；不得用错误代数掩盖这一点。

### 7.2 不同量纲与冻结选参

[HYPOTHESIS/未来规则] 不执行校准，本节规定未来必须采用的共同流程，具体world/N/资源尚未冻结：

1. 划分开发、`C_norm`单位归一化、`C_select`参数选择、封存评估world；按world而非事件拆分，全部查重，旧28000000–11只能作已曝光开发，不能新验证。不能从同mission抽片段跨集合。
2. 在C_norm的共同Public-ToM宿主前状态上，对每个world取得正的原始ToM EVID值中位数及正G_h值中位数，再分别取world中位数，固定`s_h=median_world(ToM)/median_world(G_h)`，ToM自身s=1。只用于量纲锚定，不使用未来奖励。任一world没有正值/非有限则登记归一化不可用，不丢world或补epsilon放大，回到规格审阅；不启动效果比较。缺正值的事实本身是退化证据，不等于运行失败可替换seed。
3. 每个估值family都允许同一EVID尺度集合`alpha in {1/2,1,2}`（ToM亦允许，包含原alpha1）和共同原生单位price集合`{0,p_ref/4,p_ref/2,p_ref,2p_ref,4p_ref}`，最多18候选；p_ref取未来协议声明的正参考值，不混用Config默认1e-5与GP-ID诊断1e-4。G1的β/核不再调。Native-Age与显式价格固定age形式，不能额外多扫参数。
4. 在C_select、同预设无线/CPU支持界下，先排除失败/任务质量约束不满足点，再用**相同**规则选择：达到共同资源上限的点按平均受限完成时间、通信、逻辑CPU、固定ID字典序取最优；若无支持，标无可比工作点，不放宽预算。保留全部点及校准前沿。规则/资源上限/false declaration要求必须结果前冻结，不用隐藏评估seed选点。
5. Periodic同filter参照拟用k集合`{1,2,4,8,16,32}`，同C_select目标/约束与tie规则，不扫描filter来取得主轴优势；另列k8/eps0历史点。不得用它与G1价格相同当成本匹配。不同参数族不机械追求相同price或相同18次无意义重复；G1不能获得额外自适应试验次数。
6. 在封存world上报告预先选点的任务/UL+DL/字节/CPU/实际时间及配对区间/比较族校正，仍需核查实际资源支持；校准等成本不保证评估等成本。优越性与非劣效目标必须事前选定，不事后互换。

归一化与alpha固定在训练/校准侧；线上不按每次候选最大值归一化。EVID缩放为共同校准自由度，CONF/INTENT锚值不随family改；因此不能把s_h当成全目标可抵消的price变换。

### 7.3 精确消融与结构退化

- **空间打乱**：按live cell的行优先列表对weights循环移位`floor(K/2)`位（K<=1则恒等），保持weight直方图/均值与d不变。固定无RNG、不动真实动作；是内容对齐破坏参照，不是一次随机置换就证明无关。移位后相同须记degenerate，不能私下寻找最不利移位。
- **同状态EVID统一缩放shadow**：取最短、G0>0的原可行prefix u_ref，令`a_t=G1(u_ref)/G0(u_ref)`，对全部EVID替换为`a_t G0(u)`；若全G0=0则两者按界也全0。这是使用合法同状态分数的诊断参照，不是已部署动态price，计算成本单列；若各prefix比例都相同，G1在该catalog没有新增内容排序自由度。
- **原菜单的单prefix限制shadow**：只保留原EVID中最短prefix对应的既有rate Options，其余EVID Options仅在此诊断副本屏蔽，CONF/INTENT不变。绝不扩大到任意记录/全部prefix，不写回online菜单。比较剩余差别是否全属类型门槛，不把受限诊断当新策略效果。
- **单prefix结构性退化**：[推导] 若所有rate都对应同一u，则G1/G0是同次EVID所有rate的共同因子；能改变EVID与CONF/INTENT竞争或选率的净值，但不能证明区分了不同EVID内容。若`d_u`对所有可行u仅为同一空间向量的比例，结论同样成立，即使权重场不均匀。
- **零/均匀退化**：无EVID、K=0、uniform权重、饱和零变化等全记录。不能只挑G1会改变选择的catalog做分母。

## 8. 未来最小同前状态shadow诊断

### 8.1 只检验机制可区分性，不检验任务收益

[HYPOTHESIS/未来提案] 使用已曝光成本world `27000000,27000001`，每world同一Public-ToM/GP-ID-BF宿主24slot，按原source/filter/service配置。每sender取前8个真实admission且有EVID的入口，按t/agent次序，最多96个快照（默认6agent）；同时记录所有入口、空EVID和stop-and-wait阻塞计数。无按reward/改变率挑选，无新独立效果N。既有日志缺Lc/declared/intent完整快照，未来需要经合同验证的被动导出或受控重放；不拿edge最终数组补齐。

这是候选的有限开发诊断，**尚未授权执行**。资源提案为单worker/数值线程1、120s总硬上限、32MiB新增产物上限，实际投影未测，运行前必须按hpc_runs预检/同步/身份及预算合同另行冻结；不足即停，不擅自延时/扩world/扩slot。与旧run比较如需确认复现，必须使用原run/source/config身份，不能倒填014b85d为旧运行commit。

### 8.2 快照与操作顺序

1. 在真实select入口、候选构建前，深拷贝只读Context、FIFO及自己的outstanding/已接收Obs身份验证摘要，保存原始值与SHA；不向评分器暴露全局状态/seed。原日志缺字段标缺失，不回填。
2. 原宿主构造一次catalog（Public-ToM），保存raw ToM EVID、成功率、稳定索引、实际payload哈希、非EVID value_hex；原宿主正常选择/执行。
3. 从完全同一快照构造独立catalog副本，仅替换EVID值为G0/G1/打乱/统一尺度等，使用同budget/对应声明price和原P_s。绝不调用各shadow的service.valuation_work/submit/tick/plan，绝不送出包或推进分支。所有source/group/options哈希与成员身份合同检查后保存各自BF trace。
4. 先在规范化单位/alpha1/p_ref下比较，再对§7.2已声明的有限price集合做敏感性检查；不是用此曝光数据挑选部署点。s_h若尚未由合法C_norm固定，仅允许原始G0/G1的同尺度内部比较，跨ToM的选包结果标未校准，不下公平性能结论。
5. 宿主观察开/关的原结果/随机流/服务账本必须相同；shadow所有操作只占实际记录时间，不改变宿主逻辑CPU。若数值函数有全局cache，则隔离其预热对实测计时的影响，不能共享cache冒称部署成本。
6. 独立部署计时路径对同快照使用固定顺序轮换，冷调用1次、热调用3次（每方法，不挑最快）；重复计时不生成任务样本。快照复制、body计算和观察器成本均分别保存。

### 8.3 必报指标和分母

| 指标 | 定义/分母 | 解释限制 |
|---|---|---|
| 合法性/重复证据 | 每入口可核验Obs集合；overlap/missing/malformed计数 | 任一硬违规即阻断，不跳过不利样本 |
| 候选覆盖 | 全入口数、有EVID数、唯一prefix>=2数、合法可行pair数，按world/agent列出 | 同一world事件相关，不作为独立N |
| 权重/分数非均匀性 | w范围、G1/G0逐prefix、对统一尺度a_t的最大容差残差 | w不均匀本身不等于评分/选择区别 |
| 相对排序 | 不同prefix原始G0/G1、乘同P_s后的Option值、`V−p*symbols`在声明price下的pair次序；另报V/symbols作为诊断，容差内tie另列 | 区分不同内容与同prefix不同rate，后一类不作内容排序证据；不把V/symbols再送回selector重复扣费 |
| 同symbols竞争 | 相同symbols、不同prefix的可行pair若存在，比较值次序 | 可能没有这种pair，记N/A，不能记零失败或强行造pair |
| 最终签名 | 各方法选择的组/Option稳定索引、kind/cell/prefix/rate/symbols/payload | value变化不是收益；同前状态选择差别不是闭环效果 |
| 频率/类型/内容分解 | EVID无→有/有→无；双方均选EVID时prefix切换；仅rate切换；CONF/INTENT竞争改变 | shadow只观察admission倾向，不能称真实长期发送频率已改变 |
| 超出统一缩放/price | 在规定price集合、a_t控制和单prefix副本上比较差别 | 不能证明所有可能动态价格函数均无法等效 |
| 计算与内存 | §6各段cold/hot时间/总量、context大小、日志大小 | 不把3次热调用合并为3个样本，不称任务CPU节省 |

### 8.4 明确停止规则

- **硬No-Go**：信息越权、未验证重复计入、改了任何结构字段/非EVID值、宿主观察改变结果/随机流/账本、预算/组/成员/wire违反或非有限算术；保留失败，不运行效果阶段。
- **内容机制No-Go**：合法快照内G1全部可由同次a_t G0解释；或在原始值、期望值及声明price下净值三层均没有超过容差的不同prefix相对排序变化；或最终差别完全由有/无EVID、统一尺度/声明动态price对照解释。可报告门槛机制，不得靠增加模型复杂度保住内容排序主张。只要求原始值次序翻转会误拒绝“原始值仍随prefix增大，但内容带来的增益/成本取舍改变”的合法机制，因此净值层也必须检验。
- **固定菜单下No-Go**：虽然分数/排序变了，但所有可比价位的实际BF选包不变；不能换FIFO或增加prefix来宣称当前只改估值的设计成功。候选改造若有必要必须另立研究修订，本轮不开展。
- **覆盖不足**：两world均需至少存在一个合法的多prefix入口；不足则记`Pending_coverage / No-Go_for_efficacy_progression`，不称普遍无效，也不自动扩world/时长寻找区别。
- **仅机制Conditional Go**：两world分别至少有一个超过容差的不同prefix排序变化（原始/期望/净值之一），且至少有一个双方均选EVID时的真实prefix切换不能被同次a_t控制解释；相关pair两侧排序差均须超过tau，不能只由rate/tie/开关造成。全部合同通过后，才可建议审阅下一诊断。不用“改变>某比例”代替任务价值证据。
- **成本No-Go/Pending**：独立全估值路径耗时若稳定超过共同Public-ToM且没有已识别任务收益依据，低成本路线No-Go；计时噪声/3次重复无法辨认时Pending，不自动重复到有利。即使更快也不证明任务改善，.001s预留是否覆盖实际费用仍须另审。

通过上述门槛只说明**机制存在可检验区别**；真实任务优越性、净收益和学术贡献仍No-Go/Pending。后续离线deliver/drop或封存world效果试验都不在本规格执行授权内。

## 9. 后续必须具备但本轮未运行的合同

[HYPOTHESIS] 精确G0对应原TV；β0/均匀场/G1退化G0；缺intent回退位置/均匀；异常字段显式拒绝；ACK先到/自己task先到/重复task/零DL/同slot观测隔离；前缀抵消和最大prefix一致；CONF/INTENT value_hex及完整catalog结构保持；只乘一次成功率；输入不变与禁止全局对象；BF版本/member/group/budget/wire；日志观察中性；空菜单与计时成本范围。以上都只是未来合同清单，**无新增测试通过记录**。

本轮仅静态规格交付Go。当前研究设计缺少内容排序与任务收益证据，**No-Go：效果campaign、正式test、扩N、训练及论文正向贡献主张**。是否实施有界诊断由后续明确任务决定；本文完成后停止。
