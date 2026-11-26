# T3-R-v2-I 旧行为与冻结源码保护核查

2026-11-25，Asia/Shanghai；base458a96f59b620a02e6872d038b87912eb39e92e4。

[RUN/本地轻量管理] 启动及当前`git diff --name-only HEAD`均为空；本轮新增文件均为独立命名路径，没有编辑旧application/client/evaluation/wire/ledger/fixture/live driver、GOSC核心、既有tests或四份冻结v2静态文档。两份用户任务文档与.workbuddy保留，不暂存，不提交推送。

39项旧源码/测试/GOSC/管理器/registry与冻结规格的原始及LF SHA已记录于[frozen_baseline.json](../logs/masbench-t3rv2i-2026-11-25/frozen_baseline.json)。初始tracked干净，故这些实际工作字节对应已审base；registry只作SHA，没有解析记录或读取题目正文。LF哈希用于HPC标准同步规范化后的对账，不能与Windows原始字节SHA混称。

[CODE] 新协议使用`fair_final_v2*`命名，仅显式导入PrivateView、ControlledClient、ContractTransport、Ledger和fixture_rpc。没有修改旧base/protocol默认分发或parse_answer/legacy/summarize。新评分在独立离线模块，不反向导入在线应用，不将双final分数写回旧团队结果。

[HYPOTHESIS/待动态核验] 新测试含旧parser/自动角色前缀语义的回归；专用`--legacy`入口拟重新运行旧synthetic adapter回归，并单列结果，不冒充C01–C32。**这些回归尚未运行；字节未改不是运行时回归通过。** 独立审计拟再次核39项LF SHA并从新夹具journal/帧/输入恢复新版状态，尚无审计通过记录。

[RUN/管理阻断] HPC HEAD=b05ea73且索引有大量原有暂存删除；本轮未修复/重置/覆盖这些状态，亦未同步新增文件。未经处理方案确认，不将HPC称为458a96f运行环境，不绕过sync_hpc的HEAD/origin一致性检查。

历史T3运行身份仍b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0+20261125T034132Z，不被本轮base替代；684原件、旧结果与T3/G1/GP-ID科学No-Go保留。未启动新能力实验/新算法/T4/校准/封存test/训练。

结论：**本地旧文件字节保护可核验；动态旧行为回归和HPC源码对账Pending。** 不能据本文件声称新版工程验收或真实部署已通过。
