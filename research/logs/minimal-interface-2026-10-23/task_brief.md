# Research Task Brief — R2/R3交付、最小位置估值接口与HPC合同验收

- 用户授权：2026-10-23“按顺序推进执行”，对应R2/R3可提交成果包→已送达位置的最小估值接口→HPC有界合同验证；效果实验需先验收与冻结，复杂训练仍No-Go。授权未要求Git提交/推送，本轮先形成可提交结果。
- [CODE] 起点4ff4147654c07781d77a42acee3f31c0b8792f38，分支research/progress-audit-2026-10-19。已有未提交状态导航/协议文档由本会话上一步生成，保持原样延续，不reset/checkout/clean。
- 科学问题：[HYPOTHESIS] 能否只在估值器读取已真实送达、TTL内且比本地EVID位置更鲜的pose，同时不改Planner、原候选/速率/调度规则？RTT等待/旧ACK/过期/计费是否有可核验合同？本轮不检验任务增益。
- 前人成果：[PAPER] 沿用D01 p5 Eq4、D08 p6/p16既有阅读记录；[RUN] 既有免费特权0/6、96固定轨迹回放不支持部署净收益。位置刷新是既有机制对照，不宣称新颖性。
- 修改范围：新增research/artifacts下白名单交付副本与哈希索引；extensions独立pose cache/ledger/ToM接口与RTT状态机；tests_ext有界合同测试；新增运行协议/报告/证据。原gosc/experiments/tests/results/LICENSE不改，旧冻结协议/run不覆盖。
- 双路径：先映射schemes.GOSC.build_groups与realistic.RealisticGOSC.build_groups的TeamModel构造及EVID估值调用，使用估值专用接口，不改全局公共位置或Planner。共享UL不纳入首验收主张。
- 设计：先只复制已登记R2/R3公共生成物并比对原SHA，不重绘；实现权限/时序/原生EVID本地时间ledger/无cache回退/两条build_groups；独立RTT attempt与latest pending、ACK/TTL/预算合同。仅HPC运行测试，拟单进程、数值线程1、硬上限300s，无任务效果campaign。
- 预算：R2/R3轻量文件复制/哈希；HPC合同测试至多300s，<=2CPU/实际配额内，0GPU/0LLM/0训练/0下载。若需非合同仿真/新样本/更大预算另行冻结，不自动扩大。
- 反例与停止：时间ledger读到未收到的edge状态、旧摘要覆盖新EVID、projection修改Planner/候选、开启oracle、旧ACK删新代、重传超预算或HPC不可达均停止依赖步骤；保留失败，不回退本地计算。
- 验收：交付包所有副本SHA与登记产物一致；两路径合同与RTT/CRC/TTL/预算测试在HPC有独立run/日志；报告明确接口不是闭环收益、未执行效果实验，保留P1材料缺口。
