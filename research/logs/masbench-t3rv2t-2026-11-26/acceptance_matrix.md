# T3-R-v2-T 新增任务路径无模型合同矩阵

2026-11-26 Asia/Shanghai。只执行本轮 `tests_ext/test_masbench_t3rv2t_task.py`；不重跑旧C/D合同、不将旧T1/T2/T3当成本轮结果。人造4家族用于工程覆盖，独立科研N=0。

[RUN] 最终hpc-t3rv2i-task-contract-r3-20261126：25/25通过，T01–T16全覆盖；r2为24/24，首轮23/24。独立hpc-t3rv2i-task-audit-20261126通过，四run/1683常规文件/11818187B完整回传。新增的第25项是源码与实测回执一致性合同；不把重复run相加为73项。所有失败run保留。

| 合同 | 实际断言/支持域 | 测试入口（同名函数及参数分支） |
|---|---|---|
| T01 | 8×6完整计划；新Agent/transport/IPC累计状态；48/24/6永久分账；Full收4条且来源可追，No-A2A仍双final且无peer；双方终答不互见；fixture标签不可充真实 | full_plan_reset_isolation_and_fixture_label |
| T02 | null、空串、早期A、混合MESSAGE+A不终止；不修复，仍六机会 | early_empty_illegal_exchange_never_shortens，4分支 |
| T03 | 无效E归零、合法U弃答、占位A无效；失败保留双本地分母 | final_source_abstain_no_repair，3分支 |
| T04 | strict四视图bundle拒绝gold/records/缺家族/私有信息变化；历史pairSHA约束 | strict_bundle_rejects_gold_and_unbound_views |
| T05 | probe/未批准/新增合成/重开旧deadline拒绝；CLI未批准在数据/服务前退出；源码同时绑定审批与实测回执 | probe_and_unapproved_task_authority_rejected；approved_source_must_match_contract_receipt |
| T06 | 未知usage/超时保留预留、当前已启动episode分母2、后续未启动NA；重开账本不退款/不重新放行 | partial_failure_denominator_no_retry_persistent，2分支 |
| T07 | 8个完整初始输入人造计数；SHA错或15873+512超窗拒绝；不伪称真实qwen计数 | initial_full_input_count_and_window |
| T08 | slot计数超窗在生成前停；单包、累计、终端上限；driver/service/GPU观察超界拒绝 | limits_and_no_generated_calls_on_overwindow |
| T09 | 退出失败fence；回传/存储失败后不进入下一episode | exit_barrier_and_return_failure_stop_plan |
| T10 | 小存储额度拒绝、8预计数/48即时计数上界、fixture与real账本身份不可互换 | storage_reservation_and_operation_caps |
| T11 | 真实TaskDriver接口通过FakeRPC跑完整8×6；GET152、render48、generate48、cleanup/unload8；8个runner epoch不复用；slot身份损坏拒绝；缺独立基础设施证据的科研门拒绝 | task_real_adapter_all_48_are_only_simulated |
| T12 | TaskDriver未知usage/完整计数SHA错误/runner中途改变停止；无补请求 | task_adapter_unknown_usage_count_identity，3分支 |
| T13 | 部分失败也可算配对分，独立工程与基础设施门仍不通过 | scoring_does_not_substitute_engineering |
| T14 | 重复episode/乱序启动拒绝 | plan_order_and_alias_refuse |
| T15 | 字面PromptSHA冻结；旧probe生成cap2和独立scope/path保持，新HTTP总440 | literal_prompt_frozen_and_probe_caps_intact |
| T16 | 在线campaign不导入评分/参考答案；无cache模块接入 | no_cache_or_scoring_in_task_orchestrator |

## 支持边界

[CODE] 测试T11用`fixture=False`账本专门检查真实适配器的接口分支，RPC完全由固定人工响应替换。`task_real`是接口计量标签，不是本轮发生过真实HTTP/模型的证据；wrapper、manifest、独立审计都明确模型/HTTP/helper/服务切换=0。本轮T01原件用`task_fixture`，禁止把其人工计数单位混入未来真实token统计。

T08的资源超界是人造观测值，T06超时为受控假后端，T09退出是人造runner。它们不证明现场故障硬隔离；TaskSpawner/Deployment的新真实路径尚未启动。不复测旧合同以增加数字，T15只读冻结SHA。

独立stdlib审计不导入生产TaskDriver/Parser/Scorer，分别重建T01的48请求账本和T11真实适配器模拟账本，核hash链、6slot/角色、终答隔离、合法来源、HTTP分类与清理，并比较旧冻结源码与c062。完整回传需要独立双端receipt，不以pytest退出0代替。

## 原失败

[RUN] 首轮 `hpc-t3rv2i-task-contract-20261126`：23通过、1失败；7.276632秒登记墙钟，pytest5.64秒。TaskLedger未解释复用LiveDriver的`cleanup`事件，T11首episode清理后中止。原ledger因`_append`写盘后解释异常，留下重复seq99/前链分叉；这份失败journal**不能**宣称通过链审计。修复仅在新TaskLedger解释原有cleanup事件，保留首轮全部412文件/3002294B及receipt `20261126-t3rv2t-fca11334f6.json`，不改旧基础Ledger和probe。
