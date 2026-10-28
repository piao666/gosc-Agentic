# 结果后审计故障登记 — 2026-10-27

[RUN] `hpc-information-calibration-audit-20261027` 在严格 `Selected budget` 条件失败，退出1。`hpc-information-calibration-budget-diagnosis-20261027` 对原156任务、70,302条decision只读扫描：bits六次、AoI一次选包超过100-symbol上限，选中总量152/228/304，最大超额204；不是浮点求和容差问题。原始results SHA `8df6df09036ad3ff528fe346409bb71ed6c35c48f5a751d0a307698ebd46c77b`。

[CODE] 不修改 `gosc/schemes.py::lagrangian_select`、在线GP-ID策略或服务、已冻结协议、旧run及原始结果。结果后仅增补审计诊断模式：默认仍严格拒绝；显式收集越界项时继续其他逐决策/目录/账本/统计检查，任何已记录越界使状态为`blocked_selection_budget`，不能改成passed。新审计源码SHA单列于新run及输出，不冒称与事前frozen相同。预登记分析保持原稿，统计No-Go与工程阻断分开。

[RUN] 新诊断合同先红（未实现接口，退出2）。全391项回归390通过、1失败：新增合成catalog漏`value_hex`，定位于测试fixture；仅补其`value`/`value_hex`，旧390项不受改动。修复后的3项针对合同另run验证，原失败保留；不得将该全套run写成391/391通过。

[RUN] Windows端同时回传同一文件曾触发WinError5，影响两个launch的本地收尾；HPC分析completed、严格审计failed分别按远端status认定。后续完整receipt `20261027T082418Z-dd3177`已覆盖校准/分析/严格审计/首次诊断，其他回传改为串行；不删除残留partial或失败日志，不把本地管理异常写成仿真失败。

[HYPOTHESIS] 旧selector二分法初始上端点的数值可行性是待核验解释；必须由原日志目录的独立重放支持，不能仅靠源码推断宣布根因。任何修订scheduler并重新实验都需要独立版本/完整对照和预算；本轮不执行。

[RUN，后续核验] `hpc-information-calibration-bracket-diagnosis-20261027` 在11.633064s完成。同7原目录独立重建初始上端点/40步二分：7次初始上端点不可行，最终选择均与观察到的超预算选择相同。故上述待核验解释在这7目录获得支持，不外推其他任务/所有selector调用。诊断审计run30.501279s完成全156记录/账本/统计复算一致，仍blocked_selection_budget；receipt `20261027T083457Z-d8e935` all_outputs_mirrored=true。
