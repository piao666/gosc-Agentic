# Selector预算可行性修订审阅候选

后续审阅已完成：[审阅报告](../reports/selector_budget_revision_review_2026-10-27.md)与[细化规格v1](selector_budget_feasibility_spec_v1_2026-10-27.md)。方向有条件通过，明确有限失败、组唯一性、旧可行调用兼容和版本化重放；实现/合同仍Pending。下文为原候选，不构成运行许可。

状态：review_candidate，尚无修订算法实现、校准重跑或新实验授权。原GP-ID-CAL-v1、上游selector、冻结产物和全部负结果保持。

[RUN] [校准审计](../reports/information_calibration_results_2026-10-27.md)发现bits6/AoI1次选中152/228/304symbols>100。`hpc-information-calibration-bracket-diagnosis-20261027`在同7个原始日志目录独立转录旧二分过程：7次初始上端点均不可行，40步后仍不可行且精确重现观察选择。不是事后挑有利任务，也未产生新mission。账本物理服务容量通过不能补救选包合同失败。

[CODE] `gosc/schemes.py::lagrangian_select`使用`hi=max(value/symbols)`及40次二分，未先检查`pick(price+hi)`可行性。原文件不改。数值上端点不可行已经由日志重放核验；其普遍出现率/其他任务影响未核验。

[HYPOTHESIS] 最小修订方向：独立extension/新标识实现显式可行上端点与最终硬预算合同；保留原可行调用的选择、顺序和原基线。失败必须有界且可解释，不能仅删日志、提高100上限、丢弃辅助对照，或在比较后静默裁包。采用上端点扩张/严格更大界等具体实现前，比较舍入、溢出、零/负值、同组唯一性、贪心填充与确定性边界。

建议验收顺序（非本轮执行许可）：

1. 在HPC登记只读7目录回归及合成对抗合同；验证预算/成员资格/组唯一性、原可行选择不变和确定性，不用reward调修复。
2. 把共同selector修订应用到所有适用估值对照，periodic独立路径也核查；新旧版本分名，保持原GP-ID结果。严格默认审计必须拒绝所有真实违规。
3. 先审阅是否仍有付费信息研究必要性。现paid-pose部署比较无净支持，修复辅助bits/AoI不能自行翻转主方法No-Go。
4. 若确有新科学假设，再冻结共同对照、全新world、N、完整端到端/产物预算与停止规则。不得在本轮原12world上反复选参后称新独立验证，不自动扩N/price/正式test/训练。

当下写作可基于真实负结果与审计失效边界继续；任何主张收缩不等于宣布信息无价值或已解决普遍识别问题。
