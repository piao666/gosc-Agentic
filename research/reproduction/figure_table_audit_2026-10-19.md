# GOSC 原论文图表核对与差异报告

日期：2026-10-19。精确PDF为本地D01 arXiv:2609.39477v1，13页，SHA256 e99130b27965bc4b6c06ccca8fc2dd9a3fd8b2dd5f6880964b6e0a4003c01923。完整逐项索引见 research/logs/GOSC_paper_code_map.md。

## 已完成的核对

[RUN] 本地只读提取和渲染原PDF全部13页，重点逐页查看含编号图表的p2/4/7/8/9/10/11/12。将已回传17张图的PDF渲染为PNG浏览，并将Fig2/3/4/5分别定位至fig_rescue/fig_noise/fig_snr_pair/fig_shared_col。渲染仅用于阅读，未改写原PDF；私有原文/全文/截图不随项目上传。渲染中间件保存在本机任务可视化目录 gosc-paper-review/。

[RUN] HPC `hpc-paper-audit-20261019` 用手工独立抄录的印刷参考值核对9张数值表（IV–XII），共405个数据单元，包含均值/CI端点和†/‡标记。参考值不是从生成summary复制，来源页码/表号记录在 paper_table_references.json。已印刷小数按数值token检查，1e-8仅为浮点解析容差；不同于上轮三summary的1e-10相对/绝对比较。

- 原R2：IV、V、VII、VIII、IX、X、XI、XII共8表全部一致；VI存在5个n/e，不能按“脚本退出0”视为完整。
- 隔离补表：执行原`experiments.run_belief_divergence --table`，不重仿真，补全VI全部10行40单元。补全表的全部数据与印刷值一致；旧表和原始结果保留。
- II：218-bit raw、18-bit confirm/intent、semantic 33+5P、单记录无检测evidence34-bit得到核验；有一个检测时39-bit，NL长度随正文变化，约1480不是常数。
- III：25项Config字段匹配；救援的[60,180]是实验显式覆盖，通用Config为[100,300]；slot1s是模型单位。
- XIII：6组冻结scheme/eta/k/theta与保存数据一致。
- I：完成GOSC机制列的源码映射与原表阅读；其他文献的跨论文定位尚未独立全文复核，不能计为完成全部related work。

详细机器证据：research/sync/runs/hpc-paper-audit-20261019/outputs/{audit_summary,original_table_comparison,completed_table_vi_comparison,static_and_frozen_checks,input_integrity}.json；补表为该outputs/supplements/table_values.tex。

## 明确差异与处理

| 编号 | 发现 | 处理与影响 |
|---|---|---|
| D1 | 上游README三条plot命令缺少TableVI补表步骤，K10三行/clustered两行仍为n/e | 已执行仓库已有table-only helper，单独保存完整表；未修改原算法/脚本或覆盖原R2证据 |
| D2 | 重绘Fig2第三子图次刻度标签在log轴重叠；论文中的图更紧凑但未出现同样密集的标签 | 已记录为显示差异，不解释为数值变化；原重绘PDF不改。后续制作展示版可仅隐藏minor标签，须另存并标明版式派生 |
| D3 | 论文称38种periodic配置；主结果保存搜索候选实际37，救援38；当前rate_aware搜索生成器只有k=1,2,4,8 | HPC元数据预检确认，各候选100个独立eval seed（0..99）；R4严格复现保留37口径，新增k16另设38候选敏感性轨道，不静默补数据 |
| D4 | Genie在研究说明书曾写“只作上界”，论文p7明确不是performance bound | 已更正说明书为理想通信参考；同一启发式planner可能因额外信息改变决策而变差 |
| D5 | 共用统计说明写4000 bootstrap，matched-budget代码实际10000，部分效率诊断2000 | 协议分别固定主结果4000、TableVI10000，记录实际resample数；不声称所有原表都用同一个次数 |
| D6 | analyze_theory docstring写Proposition3；当前PDF为Proposition2；共享price实现有过载指数clip，理论maximizer平局顺序有实现细节 | 以PDF编号和真实源码分别标注，未改原源码，未将此映射升级为独立定理证明或新的失败结论 |

## 必须保留的负面/条件结论

[PAPER/RUN] TableVI简单throughput/AoI比较15项，仅1项在未校正95%CI中显著，未通过Bonferroni；不支持把更复杂ToM普遍优于简单值写成结论。TableIX默认search在H16时UL ratio=0.84，反向；H32时GOSC标†。TableVII部分配置未达目标，ratio大也不能不附条件宣称优势。TableXI B150未达到目标，B300 search ratio CI跨1。TableXII Qwen7B的任务时间差CI跨0，LLM成本收益结论不能推广到开放式Agent。

[R2] 数值一致意味着重建作者保存结果一致，不代表这些400/10000次bootstrap是我们独立的新mission；R4新仿真与R5真实LLM仍未执行。

## 验收结论

- 论文5图/13表/5式/Algorithm1已完成定位与源码映射。
- 可计算的印刷数值表已在已说明的补表步骤后匹配；消息/参数/冻结点亦有证据。
- 图1为静态结构，表I为文献定位，不能按数值实验计完成。
- 版式D2和实现/候选口径D3/D5/D6已显式登记。当前可进入有边界的R4预登记与pilot准备，不能称原P1全部验收或新方法已成立。
