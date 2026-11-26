# T3-R-v2 部署准入补齐合同 v1

2026-11-26 Asia/Shanghai。**Blocked；不是运行授权。** 本轮用户授权开展部署准入补齐，不自动批准尚无具体资源及入口合同的真实生成。v2-I已经通过的人工合同不重标为真实部署通过。

## 1. 当前现场与不可越过的前提

[RUN/管理] 本轮[原始只读快照](../logs/masbench-t3rv2-deployment-2026-11-26/hpc_readonly_inventory.json)：HEAD458a96f；UID8301880/n1；2CPU、24GiB容器硬内存、cpuset0–1。SSD个人hard limit100GiB，余6594560B；HDD余517812883456B。共享df不是个人可写空间。注册测试需要的16MiB新增上限尚无写前预留，因此未同步/登记/执行测试。

服务PID42172/start stamp4966705858仅为本次观测身份，后续不能永久照抄。binary SHA e014750cd656db3a77f3bf6b45903f646c76075e58b835cc9787fb5fc8a8a600，0.11.11、qwen2.5:7b manifest845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e及helper/template/system小文件SHA匹配既有pin；权重仅stat4683073952B，没有全文件重扫。三次GET成功，ps为空、无连接、recovery marker0B、GPU读数34304/0MiB；context仍1024且无persistent override。这不是16384有效窗口验收。

当前用户对所查CPU/memory/devices控制文件均无写权；24GiB是容器合计，不等于driver2GiB/service16GiB分别硬隔离。设备访问列表不提供16GiB显存分区证据。未找到可由当前用户直接执行的子树硬资源配置，不据此断言管理员无法提供。

## 2. 独立真实执行入口的改动合同

[CODE] v2-I `fair_final_v2.py:173–185`故意只接受精确FixtureDriver；`fair_final_v2_guard.py:86–125,188–216`明确model-free身份与fake_operation。旧 `live_driver.py:75–128,377–410,457–505,539–597`只认可T1/T2/T3旧授权，并非可换文件名复用的v2通道。

不能删类型检查、把fixture标为live、猴子补丁旧授权检查或把fake_operation改为false后开跑。拟新增独立`fair_final_v2_live.py`与专用guardian/launcher，保留原入口字节和旧默认。复用合法PrivateView、Agent/parse_output/Prompt资产、ControlledClient、wire以及经审阅的底层工具；新循环必须与现有六slot逐请求比较，不能只验证最终分数相等。

新入口最少需要以下合同；**目前未实现/未验收**，不宣称已有完整live入口：

1. 新approval schema绑定唯一登记run、parent budget、源码LF SHA、Prompt/registry/helper/model/template/service SHA、plan和新合同receipt。`approved:false`或缺失时，metadata/render/counter/generation/lifecycle全部拒绝；绝不调用旧require_authorization。
2. parent预算journal在两个真实阶段共享、fsync先于操作；全局单调deadline、生成/HTTP/计数/存储均不可重置。阶段二只能消费余量，未知usage不退款，不支持恢复后再生成。
3. 一个schema严格的应用worker仅持有己方PrivateView、原历史和真实收信。新guardian不把gold、另方私有字段、final/耗时/错误信息传入peer；t4不影响t5请求。冻结原system SHA，不新增提示内容或免费累计板。
4. 一份请求的全量messages→JSON SHA→同源精确render/token ids→native debug rendered相等→服务ps/context16384/manifest与唯一runner PID+stamp→ControlledClient身份→持久预留→一次POST→完整usage/原响应的链全部可追。helper最多20s、硬AS2GiB，计入driver树预算。不能套1GiB失败合同或默认bytes/4。
5. `stream=false, temperature=0,max_tokens=512,retries=0`；无隐藏采样参数/cache/tools/fallback；准备150s含helper20/render120及metadata，生成180s，清理40s。旧60s已被T2实测反证，不能沿旧RPC常量。
6. 64KiB单packet/512KiB累计/8MiB结果和原始响应/4096B规范文本两层上限；拒绝时保留原始前缀，不能截断或加请求。已观测72929B反例保持，不提高上限掩盖。
7. HTTP操作路径、完整body及分类在调用前扣账；失败连接也扣。原`hpc_ollama.start`内部readiness必须由新持久计数入口包围，不能漏掉其首次GET和循环。无后台自动重启。
8. 故障停止整轮；仅自有且身份未漂移epoch尝试一次清理，最多1前置ps+6poll，1unload。worker已停止、原runner退出、无陌生runner、驻留/GPU读数空、lease/receipt一致才结束。未知/漂移不卸载别人模型，不强清锁。
9. 外层watchdog含parent-death信号与PID+stamp；停止派发deadline早于清理/回滚/审计/回传deadline。异常清理不增加epoch/生成额度。服务1024→16384→1024可回滚，仅操作核验的自有空闲实例。
10. 每次写入前预算和实际个人quota检查；HDD独立新路径，control/应急失败记录预分配；source上行不得覆盖HPC运行数据。完整原件双端SHA回传，receipt不完整则整体不通过。

## 3. 新无模型部署合同及冻结测试预算

原v2-I的C01–C32支持域保持；新增部署合同需要另跑，不能借54/67结果冒充。本轮冻结最大3登记（readonly60s、contracts120s、audit60s），累计command240s、单worker、2CPU以内、普通进程AS256MiB、输出4MiB、新SSD16MiB/HDD0、回传16MiB。当前配额门失败，实际新增登记0。

新增合同D01–D12：新授权缺失/篡改/旧授权拒绝；共享父账本跨run不重置；全路径HTTP及失败扣账；完整request/render/token/usage绑定；六slot请求与旧v2-I合成路径逐项一致；final隔离；未知usage永久预留；IPC越界留前缀；服务/runner漂移与单次cleanup；完整deadline及tail reserve；进程树资源越界与不能证明硬隔离时拒绝；回传失败阻断。全部只用人造信息和假后端。

HPC SSD可用至少32MiB才启动这一16MiB上限阶段，另16MiB作故障空间；不得为让测试启动而把预算改成6MiB或转成本地跑。后续真实阶段另需至少64MiB（32MiB阶段cap+32MiB保护空间），HDD至少256MiB（128MiB阶段cap+128MiB保护空间）。容量是准入阈值，不自动授权删除/迁移任何现有文件。

## 4. 资源准入的两条可审阅路径

**当前默认严格路径**：由管理员/资源平台提供可核查的driver/service独立内存树约束、可分配GPU约束及独占身份；新入口先验证后派发。CPU现有2核总硬上界已核，但不能借宿主64核增加worker。SSD/HDD仍须写前预留、计量与故障空间。

**未批准替代候选**：研究者显式接受GPU与service RSS为监测停止阈值而非硬隔离（16GiB），采样<=0.5s；driver/helper分别RLIMIT_AS2GiB且仍监测树总量。不能保证采样之间无过冲；24GiB容器总硬限仍不等于16GiB服务保证。资源越界/采样失败即停派发、保留未知usage和前缀，仅自有安全清理。此为风险/合同变更，需用户明确批准，不能由“补齐”默认为已接受。

无需下载/升级模型、依赖或驱动。若严格路径不可提供且替代候选未批准，真实部署继续Blocked，不能通过扩大内存/显存指标或换模型解决。

## 5. 下一真实阶段的具体申请（未批准，非能力诊断）

完成配额恢复、独立live入口及D01–D12后，才具备申请一次纯合成部署验收的前提。详细预算与字面输入资产见[部署预检计划](masbench_t3rv2_deployment_probe_candidate_2026-11-26.json)。本轮不运行。

最多2个合成请求、2epoch、输出各512、输入各<=15872；完整新版System和PUBLIC_CLOCK，短/重复合成长输入各1，长输入精确计数必须>1024，失败不改文本重跑。没有真实题文/gold/评价；成功条件只看身份/render/context/usage/保护/退出/回滚/回传，不以回复是否像正确答案来评价科研能力。

必须独立授权一次16384临时切换及1024回滚；空闲PID+stamp在执行前重新绑定。生成前全量GGUF SHA核验<=120s，未完成则停止，不把文件名当权重SHA。若服务发生身份漂移则不启动/切换，保护锁和证据留待审阅。

## 6. 有界T3能力诊断申请的释放条件

只有D01–D12、纯合成真实部署、1024回滚及完整回传均通过，才生成**可签发**的原四家族8episode/48任务生成申请。本轮不选题、不读registry正文/题文/gold；不创建`approved:true`文件。未来两阶段合成2+任务48的生成总量仍50，但不能为分阶段而隐瞒管理成本增加。

若分两个独立服务切换阶段，各阶段readiness/rollback各自计价，lifecycle GET上限由128变256；全流程HTTP由468变**596**，start/stop各最多4次，需新预算审批，不冒充原468已覆盖。合成部署2000s+任务阶段18360s=**20360s**候选，比原19100s多1260s；这不是本轮授权。父账本/累计时限从首次真实阶段开始，第二阶段不能重新领50生成额度。

研究门保持完整4对、Full至少2家族双方EM1、平均配对F1差>=0.10、至少2正差且该家族双条件双方有效、真实L1及可追溯L2；主要分母不筛掉格式/未答失败。已曝光开发N4不作显著性测试，不证明独立因果或无线净收益。通过也不自动放行T4、训练、校准或封存评价。
