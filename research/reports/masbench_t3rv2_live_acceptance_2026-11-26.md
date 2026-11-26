# Research Task Report — 公平终答独立入口真实合成验收

2026-11-26 Asia/Shanghai。**两次合成真实执行、退出/回滚及事后独立证据审计通过；原连续2000秒完整交付要求未通过。** 验收支持域为固定服务与两个人工输入，不是六阶段真实任务能力、消息内容价值或无线净收益。长输入有一次真实格式失败，原样保留。

## 问题、改动与保护

- **Research Question / Hypothesis**：[HYPOTHESIS] 独立真实适配器能否实现固定身份、16384配置/完整计数与usage绑定、有界请求、可核退出及1024回滚？不评价MASBench推理成绩。
- **已核验前人工作**：AGENTS、总说明书、四份v2审查、v2-I及HDD恢复记录、T1/T2/T3相关源码。未新增[PAPER]或出版状态断言。旧54/67结果仅作既有支持域，不冒充本轮新合同。
- **实际阅读源码**：[CODE] base458a96f及新未提交文件，函数行范围见下表。旧T3身份仍b05ea73+20261125T034132Z，不改历史run。
- **本轮新增或修改**：独立live授权/账本/RPC/计数及模型适配器、独立六slot入口、可回滚服务launcher与service spawner、新D合同/独立审计、预算/单次授权/续办登记、完整回传工具及附件。原base/protocol/v2-I默认和旧评分不改；81份前序交付原字节SHA及19项本轮执行源LF SHA一致。
- **实际运行**：[RUN] HPC n1，UID8301880，项目.venv Python3.11.15，2CPU/24GiB容器；5个登记：1失败、4完成。全部命令、Git/sync与来源SHA见[run索引](../logs/masbench-t3rv2-live-2026-11-26/run_index.json)。本地仅编辑、SHA/Git/同步/回传管理。
- **测试与结果**：新合同先29过/1失败，纠正非确定CPU计时相等断言后31过；启动前补出服务AS继承风险，增加纯Python进程继承合同后最终32过，D01–D12均覆盖。真实模型恰2请求，独立审计重建1151 journal事件及43份HDD文件。
- **失败/负面证据**：长输入响应缺少规定换行，invalid_exchange；没有修复/重跑。原2000秒连续交付因自动审批服务用量错误阻断而超期，不能从墙钟扣除等待；本次用户续办只做事后审计/回传。首合同与管理失败均保留。
- **与原GOSC差异**：无调度/估值/信道/缓存/训练变化，只有独立MASBench应用及部署保护。
- **公平性与泄露**：仅冻结人工blue-parcel输入；不读原四题、剩余52条、registry正文/gold，不选择新家族。System字面SHA不变。六slot请求/历史/终答隔离有无模型比较，**两次真实预检均为Alice t0，不声称已经实测完整六slot/双方final**。
- **成本**：真实run108.091165s；helper2、生成2、render2、卸载2、start/stop各2。输入实际及永久预留9345 tokens，输出实际28、永久预留1024，不退款。账本HTTP预留28、实际发送标记26（readiness未有listener时仍预留）；低于156。三轮工程累计6.196603s，事后审计登记0.500649s。runner CPU/RSS含Git/服务子进程，不是模型独占性能。
- **可否进入下一阶段**：受测合成服务执行与证据闭环Go；原按时全流程验收不合规，整体仅限定支持域Conditional Go。真实任务profile/授权、能力筛查、内容因果及无线净收益未建立；T3/G1/GP-ID科学No-Go与T4停止保持。
- **用户需要批准的下一步**：可审阅[有界T3条件申请](../protocols/masbench_t3rv2_bounded_diagnosis_request_2026-11-26.md)，尚不可直接开跑。无Git提交推送，完成交付后停止。

## 原始身份与实际结果

[RUN] `hpc-t3rv2i-live-probe-20261126`使用Git458a96f59b620a02e6872d038b87912eb39e92e4、Source Snapshot `20261126T032819Z`，manifest源清单SHA834ffb36b048d1b5c46dd36db108c2833d2c66fa5b0aedc48a71017b5924e4cf。执行授权为HPC规范化LF SHA **8ee5cdd329bf8a73ffe7b9dd9bdb713e7e236e01d1849c240b9083e4a7a36fcd**；Windows原字节SHA不同，不拿本地归档身份替代实际执行身份。

模型qwen2.5:7b/Ollama0.11.11，manifest845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e。权重全文件SHA核验、helper/template/system SHA及逐请求原生render、ps有效16384、runner PID+stamp、完整usage均有原件。没有cache/云fallback/重试。

| 人工请求 | 精确输入=usage | 实际输出 | 全串格式 |
|---|---:|---:|---|
| deploy-short | 625 | 14 | 合法MESSAGE |
| deploy-long | 8720 | 14 | invalid_exchange，header后缺少换行 |

8720+512=9232≤16384，长输入显著超过1024；配置/同源render/usage绑定有受测证据，不是16384任意合法历史或最坏序列化证明。格式有效率1/2只是两个人工服务输入的观察，不能外推任务能力或按正确题数统计。

## 源码及新合同

| 文件/行范围 | 实现与实际支持域 |
|---|---|
| fair_final_v2_live.py:59–95 | 新单次授权、19材料LF SHA及实际D回执绑定，拒绝旧授权 |
| 同上96–179 | 不可重置账本、生成前永久预留、HTTP分类与生命周期计价 |
| 同上180–304 | 完整计数/token ids/render SHA、全量回传判定、owned RPC超时/退出 |
| 同上305起 | 两个冻结输入的真实count/native render/usage及单次cleanup；不是任意任务loader |
| fair_final_v2_runtime.py:11起 | 新六slot入口，无模型逐请求/历史/无线账目与冻结入口比较；当前probe授权明确拒绝真实六slot任务 |
| masbench_t3rv2_live_probe.py:43–193 | 资源观察、PID绑定、空闲切换/退出/1024回滚 |
| 同上194–264 | 在driver硬AS前创建固定命令服务spawner，服务树独立计量，保持服务AS继承语义 |
| 同上265起 | 唯一注册run、HDD原件、全权重SHA、1460s执行alarm及安全尾部 |
| masbench_t3rv2_live_audit.py:28起 | stdlib独立账本/来源/token/usage/退出/当前基线审计，不导入生产parser/scorer；事后模式显式标超期 |

源代码行号是当前交付，历史run以其source snapshot/源码归档为准。[D矩阵](../logs/masbench-t3rv2-live-2026-11-26/acceptance_matrix.md)逐项关联最终32项及原失败。

## 资源、退出与限制

962次资源采样；driver树峰106934272B，service树峰5251112960B，GPU峰6767509504B。活跃阶段最大采样起点间隔0.237718061s。用户已明确接受监测停止语义，**不是硬RSS/GPU隔离，也不保证采样间无过冲**。driver/RPC/计数helper硬AS2GiB；服务spawner及模型属于独立监测的service树，保留原AS继承。原60s超时配置没有复用。

两次清理均有原runner退出、无陌生runner、驻留空和GPU归零证据；服务最终1024、marker为空、当前GPU0，由事后审计再次核验。此次不是“只发成功请求便称部署通过”。没有新故障注入真实模型请求，真实超时/崩溃新版本分支仍依赖本轮无模型合同及既有明确区分的T1/T2证据，不声称所有现场故障都新测过。

原连续2000s交付要求不满足：原审计命令未被执行（自动审批用量故障），用户续办核查时距原启动约11905.54s；事后审计记录约12180.72s。原截止未重置，旧源码/授权未回填。执行108.09s通过与按时审计回传未达成是不同事实。

## 回传与研究决定

[RUN/管理] 五个run、458个文件、7763327B已完整定向回传并逐件SHA；含首轮失败、HDD人工请求/响应/计数/账本/服务日志和合成fixture常规文件。仅pytest临时便利symlink明确排除，不漏原始常规文件。双端receipt为`20261126-t3rv2-live-d81f79a776.json`，HPC原件仍在HDD。源码与小型汇总可审阅，原始镜像不自动公开Git。

**实现/无模型合同通过 ≠ 两个合成真实请求工程通过 ≠ 六阶段真实任务能力成立 ≠ 消息内容价值成立 ≠ 无线资源净收益成立。** 本次已完成获授权的真实调用与事后证据交付；保留格式负例和超期偏差，停止等待审阅，不进入T4。
