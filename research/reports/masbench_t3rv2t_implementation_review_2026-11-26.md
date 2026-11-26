# T3-R-v2-T 实现与冻结行为核查

2026-11-26 Asia/Shanghai，base c0621a1ab2cc249bbb6acb3b81cf1cec14591bcd。各run以其manifest/source snapshot为准；当前未提交源码不冒充历史执行身份。

## [CODE] 新增实现

| 源文件/函数与行范围 | 修改及边界 |
|---|---|
| `extensions/masbench_reasoning/fair_final_v2_task.py:29–127`，validate_plan/validate_task_approval/require_approval/load_private_bundle | 新task scope与8计划；approved:false先拒绝；新合同回执/源码SHA双重绑定；strict四私有视图schema和原pairSHA；不含原生300记录或gold loader |
| 同上TaskLedger/TaskFixtureDriver，128–188 | 复用FairLedger持久预留、锁、hash链、boot/墙钟、artifact；新任务/fixture身份、操作56、HTTP440、严格顺序及新epoch；识别复用cleanup事件，不改变历史账本 |
| 同上engineering_complete/scientific_gate，189–225 | 全8episode/48已知请求/6slot身份与cleanup；独立基础设施门要求runtime/resource/rollback/audit/回传/deadline，评分不能代替；L2需人工独立复核，不信E自报 |
| 同上RPC/worker及TaskDriver，230–425 | bounded RPC/worker由已验probe实现作授权专用复制，模块入口/审批改为task；复用原render/usage/退出逻辑。TaskDriver继承http/artifact/cleanup/end/abort，新增六slot、逐次计数、runner稳定及epoch隔离；没有另造Parser/client/wire |
| `fair_final_v2_task_campaign.py:11–40`，run_campaign | 不导入gold/评分，逐8执行，失败/写盘/回传失败立即终止下一episode；保留started状态及未完成分母 |
| 同上42–61，preflight_initial_inputs | 仅8个完整初始请求计数，单包先拒绝；以后每slot独立即时计数，无免费摘要/裁剪 |
| `experiments_ext/masbench_t3rv2t_task.py:14–54` | 独立任务spawner，复用原ServiceSpawner请求/退出协议与Monitor/Deployment，保留1024回滚和2GiB driver前启动服务broker |
| 同上55–126，main | 新task授权、HDD/view bundle/父journal绑定，资源/存储检查、17360执行alarm、六阶段及完整HDD索引；本轮未执行获批真实路径 |
| `tests_ext/test_masbench_t3rv2t_task.py:17起`、`masbench_t3rv2t_contract.py:9起` | 固定人工视图、原fake sandbox/FakeRPC；只新合同，登记AS256MiB/120秒/HDD64MiB |
| `experiments_ext/masbench_t3rv2t_audit.py:11起` | 独立stdlib原件、两种48请求链及旧SHA审计，无生产评分/协议依赖 |

行号按当前交付；审阅时结合函数名和run源码归档，后续文字行移不改历史源身份。

## 唯一共享源码修改

[CODE] `fair_final_v2_runtime.py:18–26,73–102`：只增加精确TaskDriver/TaskFixtureDriver类型准入、task专用异常/清理失败保留和会计标签。旧probe的scope拒绝门仍在；旧FixtureDriver保持旧标签，Timeout/OSError在旧driver仍抛出。未改`fair_final_v2.py`冻结入口，未改base/protocol默认分发、Prompt、Parser、旧评分或ControlledClient/transport核心。没有重跑旧suite，也不作所有输入行为等价的普遍证明。

## 旧源码/数据保护

[RUN/管理] 启动时local/GitHub c062，HPC旧458；备份HEAD/index/refs/status后仅fast-forward Git元数据，无checkout/reset/clean，1508个同步工作文件SHA不变，见git_alignment.json。首个bundle ref错误失败保留；改用bundle实际HEAD引用成功，未以新HEAD重写历史run。用户三项untracked未覆盖、删除或提交。

独立审计逐字节比较c062下application/evaluation/fair_final_v2/Prompt/scoring/guard/live/client/execution_safety/live_driver/wire、原probe launcher与原probe授权。源文件冻结通过不代表新真实任务已执行。registry/D1未修改、未读取或解封剩余52记录；本轮没有读取四题正文或gold，全部测试视图从人工字符串构造。

历史T3真实身份仍b05ea73+20261125T034132Z；真实probe仍458a96f+20261126T032819Z。旧No-Go、invalid_exchange及旧2000秒超期保持。
