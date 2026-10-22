# 论文主张—复验结果—判定矩阵（2026-10-22）

[PAPER] D01本地精确v1，13页，SHA256 e99130b27965bc4b6c06ccca8fc2dd9a3fd8b2dd5f6880964b6e0a4003c01923。页码为物理页。既有逐式源码映射和本轮HPC验收分别引用，不将印刷舍入一致当作全部原始字段一致。

[RUN] 本次9张数值表IV–XII共405单元检查，5张全部匹配，4张有差异；575条为当前网格外原记录，非漏跑。精确机器结果见hpc-acceptance-scope-v2-20261022；首次入口失败run保留。

| 图表/理论 | PDF页 | 论文主张/对象 | 当前判定与边界 | 证据 |
|---|---|---|---|---|
| Fig1 | 2 | Q1/Q2/Q3和公共知识闭环 | 结构映射通过；非性能结论 | gosc/{simulator,schemes,voi}.py |
| Fig2 | 7 | 救援任务资源—效果前沿 | 定性可比较；历史逐点不完全一致；原图第三面板刻度重叠；仅改刻度标签的展示派生版已目视通过，曲线XY哈希一致 | resume-revision-rest-20261020/outputs/legacy_results/rev_rescue.json |
| Fig3 | 9 | 粗略估值误差下的资源效率 | TableVII印刷49单元匹配；575网格外记录不改变选点/两位相关性 | hpc-acceptance-scope-v2-20261022/outputs/noise_extra_impact.json |
| Fig4 | 9 | SNR完成时间/资源双面板 | 4200条SNR保存指标匹配；不声称全部SNR都任务占优 | resume-main-sweeps-20261020/outputs/legacy_results/snr.json |
| Fig5 | 11 | 共享上行预算 | 18400条保存指标匹配，TableXI印刷值匹配；B150两者均未达目标 | resume-radio-shared-20261020/outputs/legacy_results/shared.jsonl |
| TableI | 4 | 相关工作定位 | GOSC机制列源码映射；近邻已增补D06/A08/D13等，不称穷尽新颖性验证 | research/literature/Research-Gap-Matrix.md |
| TableII | 4 | 消息比特长度 | 复用已核验相同源码：raw218/confirm18/intent18/semantic33+5P；NL1480是示例 | hpc-paper-audit-20261019/outputs/static_and_frozen_checks.json |
| TableIII | 7 | 默认配置 | 复用25字段核验；rescue60–180为实验显式覆盖，通用Config100–300 | hpc-paper-audit-20261019/outputs/static_and_frozen_checks.json |
| TableIV | 8 | 冻结点fresh任务/资源结果 | 54个印刷单元匹配；periodic两search条件略未达目标，保留而不改阈值 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableV | 8 | 表示方式对比 | 36个印刷单元匹配；default完整900记录中其他scheme仍83条历史差异 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableVI | 8 | 实际预算匹配的估值比较 | 40单元中11有差异，主要throughput；未确证复杂ToM普遍优于简单值；Bonferroni与未校正分别记录 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableVII | 9 | 估值精度鲁棒性 | 49个印刷单元匹配；未达目标标记和低相关反例均保留 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableVIII | 10 | 消融 | 30单元中11有差异；多数差值CI跨零，不把同价消融当等成本因果实验 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableIX | 10 | 计入头开销后的资源比 | 48单元中2个CI上端差0.01；保持原未达标/优势反转条件，不升级全部数值一致 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableX | 10 | UL和DL总成本 | 72个印刷单元匹配；控制/反馈/广播需纳入，不只看payload | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableXI | 12 | 共享预算fresh | 32个印刷单元匹配；完整精度summary另有差异，不声称全文字节一致 | hpc-acceptance-scope-v2-20261022/outputs/paper_tables_current.json |
| TableXII | 12 | 异构LLM概念验证 | 44单元中20有差异；Qwen3B任务收益未确证，Llama/7B分别披露，资源节省仍需成本边界 | hpc-live-llm-tables-20261022/outputs/llm_native_statistics.json |
| TableXIII | 12 | 冻结参数点 | 12个选点与原保存选择一致；search37/后续38敏感性分轨，校准生成过程仍缺失 | ordered-selection-20261019/outputs/selection_audit.json |
| Eq1–5/Algorithm1 | 4–6 | 任务、AoI/ToM估值和无线调度 | 源码映射保持；条件值估计非真实任务因果效用，平局严格>与论文最大maximizer边界保留 | research/logs/GOSC_paper_code_map.md |
| Prop1/Thm1–2/Prop2 | 4–6 | belief账本、阈值/保护、松弛精确/代理误差 | 既有测试与theory/scheduler数据支持其实现口径；未独立形式化重证、不宣称启发式任务全局最优 | resume-theory-20261020/outputs/original_comparison.json |

[RUN] 视觉检查：17张现有PDF已逐一通过5张contact sheet及单图查看；轴/图例/字形可读，fig_rescue刻度重叠已在独立展示派生版修复并目视通过，原native不覆盖。原论文p2/4/7/8/9/10/11/12完整页本轮已目视。TeX内容与原印刷表逐单元核对，不把未编译片段写成完整论文排版验收。原始图件和私人PDF未修改。

[RUN] 必要补验决策：原生234配置×100seed网格完整。323条为六headline场景eta3e-6（每组仅部分seed），252条是非headline search-W50；去除它们不改39个有效noise-arm选点及rho两位显示。因此不扩展原冻结协议去补跑575条，保留其原始记录与归属表。其他历史差异已有稳定重复/版本/局部ULP诊断，当前没有需要盲目重复全量仿真的新证据。需要的补项是图件版式派生与下一独立协议。

展示派生版与曲线XY一致证据：research/sync/runs/hpc-rescue-display-20261022/outputs/{fig_rescue_display.pdf,fig_rescue_display.png,layout_provenance.json}。未新增仿真。
