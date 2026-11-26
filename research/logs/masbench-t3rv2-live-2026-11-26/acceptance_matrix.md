# D01–D12实际验收矩阵

2026-11-26。最终新合同32项通过；首轮29过/1失败、第二轮31过、AS继承修订后第三轮32过分别保留。真实支持域为两次人工t0请求，不是六slot真实任务。

| ID | 最终通过case数 | 实际测试函数 |
|---|---:|---|
|D01|7|test_D01_new_approval_rejects_old_and_drift[change0]；test_D01_new_approval_rejects_old_and_drift[change1]；test_D01_new_approval_rejects_old_and_drift[change2]；test_D01_new_approval_rejects_old_and_drift[change3]；test_D01_new_approval_rejects_old_and_drift[change4]；test_D01_new_approval_rejects_old_and_drift[change5]；test_D01_baseline_PID_drift_before_service_change|
|D02|1|test_D02_parent_journal_reopen_no_refund|
|D03|6|test_D03_HTTP_whitelist[get-/api/chat-None]；test_D03_HTTP_whitelist[render-/api/chat-body1]；test_D03_HTTP_whitelist[unload-/api/chat-body2]；test_D03_HTTP_whitelist[generation-/v1/chat/completions-body3]；test_D03_HTTP_whitelist[lifecycle_get-https://elsewhere-None]；test_D03_failed_attempt_is_not_refunded|
|D04|4|test_D04_complete_counter_proof[render]；test_D04_complete_counter_proof[ids]；test_D04_complete_counter_proof[overflow]；test_D04_complete_counter_proof[tensor]|
|D05|2|test_D05_literal_assets_equal_actual_Agent_requests[0]；test_D05_literal_assets_equal_actual_Agent_requests[1]|
|D06|2|test_D06_independent_six_slots_match_frozen_entry[Full]；test_D06_independent_six_slots_match_frozen_entry[No-A2A]|
|D07|1|test_D07_unknown_usage_fences_and_retains_budget|
|D08|1|test_D08_packet_excess_and_unfrozen_request|
|D09|2|test_D09_single_cleanup_runner_exit；test_D09_foreign_runner_never_unloaded|
|D10|2|test_D10_tail_reserve_and_attempt_caps；test_D10_service_limits_do_not_inherit_narrowed_driver|
|D11|3|test_D11_resource_observation_and_sampling_fail_closed[RSS]；test_D11_resource_observation_and_sampling_fail_closed[gap]；test_D11_resource_observation_and_sampling_fail_closed[gpu]|
|D12|1|test_D12_complete_transfer_includes_failures|

来源：`hpc-t3rv2i-live-contract-v3-20261126/outputs/contract.json`及JUnit；[小型逐字节副本](../../artifacts/masbench-t3rv2-live-20261126/contract.json)。

真实执行独立审计：1151事件、43份HDD文件、两个token/usage/render绑定、两个退出barrier、1024回滚及当前GPU0均通过。长输入格式失败和2000秒完整交付超期仍不通过，不能用矩阵绿色覆盖。

D12完整实际回传另有双端receipt `20261126-t3rv2-live-d81f79a776.json`：458文件/7763327B，包括全部失败常规文件；pytest便利symlink不镜像。
