# T3-R-v2-I C01–C32 实际验收矩阵

2026-11-25，Asia/Shanghai。**全部未运行/Blocked，不存在新版通过记录。** HPC HEAD与索引阻断尚待处理方案确认。下表函数是已新增的验收设计，不是执行证据。

| ID | 已新增测试定位（1基行号） | 实际结果 | HPC run / 证据 |
|---|---|---|---|
| C01 | `tests_ext/test_masbench_fair_final_v2.py:68` / `test_C01_six_opportunities` | 未运行，Blocked | 无run；未做本地回退 |
| C02 | `tests_ext/test_masbench_fair_final_v2.py:85` / `test_C02_clock_and_prompt_bytes` | 未运行，Blocked | 无run；未做本地回退 |
| C03 | `tests_ext/test_masbench_fair_final_v2.py:97` / `test_C03_no_a2a_final_not_waiting` | 未运行，Blocked | 无run；未做本地回退 |
| C04 | `tests_ext/test_masbench_fair_final_v2.py:105` / `test_C04_early_answer_not_terminal` | 未运行，Blocked | 无run；未做本地回退 |
| C05 | `tests_ext/test_masbench_fair_final_v2.py:115` / `test_C05_full_string_no_fallback` | 未运行，Blocked | 无run；未做本地回退 |
| C06 | `tests_ext/test_masbench_fair_final_v2.py:127` / `test_C06_empty_and_invalid` | 未运行，Blocked | 无run；未做本地回退 |
| C07 | `tests_ext/test_masbench_fair_final_v2.py:137` / `test_C07_repeat_and_wrong_facts_not_fixed` | 未运行，Blocked | 无run；未做本地回退 |
| C08 | `tests_ext/test_masbench_fair_final_v2.py:149` / `test_C08_admission_and_condition_pin` | 未运行，Blocked | 无run；未做本地回退 |
| C09 | `tests_ext/test_masbench_fair_final_v2.py:160` / `test_C09_last_exchange_delivery_and_source` | 未运行，Blocked | 无run；未做本地回退 |
| C10 | `tests_ext/test_masbench_fair_final_v2.py:173` / `test_C10_final_isolation` | 未运行，Blocked | 无run；未做本地回退 |
| C11 | `tests_ext/test_masbench_fair_final_v2.py:183` / `test_C11_private_and_gold_boundary` | 未运行，Blocked | 无run；未做本地回退 |
| C12 | `tests_ext/test_masbench_fair_final_v2.py:193` / `test_C12_no_controller_injection` | 未运行，Blocked | 无run；未做本地回退 |
| C13 | `tests_ext/test_masbench_fair_final_v2.py:215` / `test_C13_final_syntax` | 未运行，Blocked | 无run；未做本地回退 |
| C14 | `tests_ext/test_masbench_fair_final_v2.py:234` / `test_C14_fixed_scoring_vectors` | 未运行，Blocked | 无run；未做本地回退 |
| C15 | `tests_ext/test_masbench_fair_final_v2.py:256` / `test_C15_no_real_data_or_scoring_import` | 未运行，Blocked | 无run；未做本地回退 |
| C16 | `tests_ext/test_masbench_fair_final_v2.py:265` / `test_C16_disagreement_and_rates` | 未运行，Blocked | 无run；未做本地回退 |
| C17 | `tests_ext/test_masbench_fair_final_v2.py:273` / `test_C17_started_and_not_started_denominators` | 未运行，Blocked | 无run；未做本地回退 |
| C18 | `tests_ext/test_masbench_fair_final_v2.py:283` / `test_C18_full_input_boundaries` | 未运行，Blocked | 无run；未做本地回退 |
| C19 | `tests_ext/test_masbench_fair_final_v2.py:292` / `test_C19_identity_and_counter_drift` | 未运行，Blocked | 无run；未做本地回退 |
| C20 | `tests_ext/test_masbench_fair_final_v2.py:304` / `test_C20_failure_no_replay` | 未运行，Blocked | 无run；未做本地回退 |
| C21 | `tests_ext/test_masbench_fair_final_v2.py:315` / `test_C21_all_http_caps_and_partition` | 未运行，Blocked | 无run；未做本地回退 |
| C22 | `tests_ext/test_masbench_fair_final_v2.py:351` / `test_C22_epoch_get_and_readiness` | 未运行，Blocked | 无run；未做本地回退 |
| C23 | `tests_ext/test_masbench_fair_final_v2.py:362` / `test_C23_seven_get_one_unload` | 未运行，Blocked | 无run；未做本地回退 |
| C24 | `tests_ext/test_masbench_fair_final_v2.py:373` / `test_C24_unbound_foreign_and_drift` | 未运行，Blocked | 无run；未做本地回退 |
| C25 | `tests_ext/test_masbench_fair_final_v2.py:388` / `test_C25_real_owned_worker_exit_and_crash_fence` | 未运行，Blocked | 无run；未做本地回退 |
| C26 | `tests_ext/test_masbench_fair_final_v2.py:428` / `test_C26_stage_and_tail_reserve` | 未运行，Blocked | 无run；未做本地回退 |
| C27 | `tests_ext/test_masbench_fair_final_v2.py:440` / `test_C27_resources_are_observations` | 未运行，Blocked | 无run；未做本地回退 |
| C28 | `tests_ext/test_masbench_fair_final_v2.py:448` / `test_C28_size_and_storage_no_truncate` | 未运行，Blocked | 无run；未做本地回退 |
| C29 | `tests_ext/test_masbench_fair_final_v2.py:476` / `test_C29_wire_loss_crc_and_ttl` | 未运行，Blocked | 无run；未做本地回退 |
| C30 | `tests_ext/test_masbench_fair_final_v2.py:489` / `test_C30_registry_pin_no_body_loader` | 未运行，Blocked | 无run；未做本地回退 |
| C31 | `tests_ext/test_masbench_fair_final_v2.py:496` / `test_C31_synthetic_failure_consumes_no_task` | 未运行，Blocked | 无run；未做本地回退 |
| C32 | `tests_ext/test_masbench_fair_final_v2.py:508` / `test_C32_receipt_failures_separate_execution` | 未运行，Blocked | 无run；未做本地回退 |

原验收依据：[冻结C01–C32](../../protocols/masbench_t3r_v2_contract_matrix_v1.md)。所有合成输入、早答/终答隔离、来源/重复事实、失败分母、超窗/usage/崩溃、计数/资源/回传反例均只写入专用测试，没有改旧测试、删失败seed或放宽科学门。

代码已提供新HPC入口、JUnit/逐合同报告及stdlib独立审计器；在实际run结束、审计和完整回传前不能把任何Pending改为Go。
