# T3-R-v2-I C01–C32 实际验收矩阵

2026-11-26，Asia/Shanghai。新版54项pytest（含参数化）全部通过；独立审计通过。支持域为固定人造输入/假后端，C18/C19不等于真实服务窗口绑定，C23/C24不等于真实外部runner退出，C27不等于GPU/RSS硬隔离。

| ID | 测试函数 / 当前行号 | 实际参数化call数 | 结果与运行证据 |
|---|---|---:|---|
| C01 | `test_C01_six_opportunities` / `tests_ext/test_masbench_fair_final_v2.py:68` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C02 | `test_C02_clock_and_prompt_bytes` / `tests_ext/test_masbench_fair_final_v2.py:85` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C03 | `test_C03_no_a2a_final_not_waiting` / `tests_ext/test_masbench_fair_final_v2.py:97` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C04 | `test_C04_early_answer_not_terminal` / `tests_ext/test_masbench_fair_final_v2.py:105` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C05 | `test_C05_full_string_no_fallback` / `tests_ext/test_masbench_fair_final_v2.py:115` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C06 | `test_C06_empty_and_invalid` / `tests_ext/test_masbench_fair_final_v2.py:127` | 7 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C07 | `test_C07_repeat_and_wrong_facts_not_fixed` / `tests_ext/test_masbench_fair_final_v2.py:137` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C08 | `test_C08_admission_and_condition_pin` / `tests_ext/test_masbench_fair_final_v2.py:149` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C09 | `test_C09_last_exchange_delivery_and_source` / `tests_ext/test_masbench_fair_final_v2.py:164` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C10 | `test_C10_final_isolation` / `tests_ext/test_masbench_fair_final_v2.py:177` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C11 | `test_C11_private_and_gold_boundary` / `tests_ext/test_masbench_fair_final_v2.py:187` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C12 | `test_C12_no_controller_injection` / `tests_ext/test_masbench_fair_final_v2.py:197` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C13 | `test_C13_final_syntax` / `tests_ext/test_masbench_fair_final_v2.py:219` | 9 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C14 | `test_C14_fixed_scoring_vectors` / `tests_ext/test_masbench_fair_final_v2.py:238` | 5 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C15 | `test_C15_no_real_data_or_scoring_import` / `tests_ext/test_masbench_fair_final_v2.py:260` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C16 | `test_C16_disagreement_and_rates` / `tests_ext/test_masbench_fair_final_v2.py:269` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C17 | `test_C17_started_and_not_started_denominators` / `tests_ext/test_masbench_fair_final_v2.py:277` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C18 | `test_C18_full_input_boundaries` / `tests_ext/test_masbench_fair_final_v2.py:287` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C19 | `test_C19_identity_and_counter_drift` / `tests_ext/test_masbench_fair_final_v2.py:296` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C20 | `test_C20_failure_no_replay` / `tests_ext/test_masbench_fair_final_v2.py:308` | 4 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C21 | `test_C21_all_http_caps_and_partition` / `tests_ext/test_masbench_fair_final_v2.py:319` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C22 | `test_C22_epoch_get_and_readiness` / `tests_ext/test_masbench_fair_final_v2.py:355` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C23 | `test_C23_seven_get_one_unload` / `tests_ext/test_masbench_fair_final_v2.py:366` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C24 | `test_C24_unbound_foreign_and_drift` / `tests_ext/test_masbench_fair_final_v2.py:377` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C25 | `test_C25_real_owned_worker_exit_and_crash_fence` / `tests_ext/test_masbench_fair_final_v2.py:392` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C26 | `test_C26_stage_and_tail_reserve` / `tests_ext/test_masbench_fair_final_v2.py:432` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C27 | `test_C27_resources_are_observations` / `tests_ext/test_masbench_fair_final_v2.py:444` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C28 | `test_C28_size_and_storage_no_truncate` / `tests_ext/test_masbench_fair_final_v2.py:452` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C29 | `test_C29_wire_loss_crc_and_ttl` / `tests_ext/test_masbench_fair_final_v2.py:480` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C30 | `test_C30_registry_pin_no_body_loader` / `tests_ext/test_masbench_fair_final_v2.py:493` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C31 | `test_C31_synthetic_failure_consumes_no_task` / `tests_ext/test_masbench_fair_final_v2.py:500` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |
| C32 | `test_C32_receipt_failures_separate_execution` / `tests_ext/test_masbench_fair_final_v2.py:512` | 1 | Pass；hpc-t3rv2i-contract-v2-20261126 / contract_results + JUnit |

独立审计：hpc-t3rv2i-audit-20261126；逐字段重建、46份journal/CRC/uses/局部memory、5评分向量、39冻结SHA、35个精确计数绑定。真实服务与科研能力未验收。

首轮hpc-t3rv2i-contract-20261126为53通过/1失败：C08误把offered候选字节当作wire字节；纠正只断言wire/UL/DL为0并明确offered>0，C03同时加强为无frame。保留首轮原始日志/源码快照，不删测试/不改科学阈值。

11月25日未运行矩阵原样保留于[暂停矩阵](acceptance_matrix_2026-11-25_pending.md)。实际结果见[小型证据包](../../artifacts/masbench-t3rv2i-20261126/README.md)与完整定向回传。
