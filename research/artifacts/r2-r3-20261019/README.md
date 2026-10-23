# R2/R3 可提交交付副本

本包于2026-10-23整理，来源为HPC 2026-10-19登记产物，**不是新运行**。文件逐字节复制；[manifest.json](manifest.json)给出来源run、路径、字节与SHA256，均与原artifacts.json核对。47份数据产物合计1,330,880 bytes；本README和manifest另计。

- `r2/plots/`：作者保存数据重分析产生的17PDF、18TeX。图件为沿用上游GOSC制图，不是本课题原创方法图。原版权/MIT和引用见仓库根LICENSE/README。
- `r2/summaries/`：三个绘图summary；`r2/replot_summary.json`及commands/input_integrity保留当时结论。
- `r2/supplements/table_values.tex`：后续paper-audit的原生table-only补表。最初R2的同名表仍含5格n/e，原件保留；完整Table VI应看此补件，不能把原表覆盖后冒称首次重绘即完整。
- `r3/mission.json`：真实重新执行Planner/GOSC、seed3000的单mission，含配置与原始结果；该seed属于作者验证划分，不是新未见world。命令与输入完整性另列。

任务结论：R2属于作者数据重分析，R3为N=1重新执行；均不证明新估值器有效。后续live LLM表、视觉修复派生版和全campaign差异请看research/reports，勿混为此包的来源。

公开范围核查：只含公开模拟器生成图表/summary、Planner合成世界与管理证据；不含私人论文、LLM提示/响应、模型、凭据。原results/cache与run outputs不移动、不覆盖。`plots/`名称用于避开原生成目录`figures/`的忽略规则，不修改.gitignore或强制加入被忽略输出。

归档状态：本包随[2026-10-23 / 01本地提交](../../../commit/2026-10-23-01-paid-pose-calibration-and-cost-review.md)纳入Git；**尚未推送GitHub**。具体提交身份由Git历史关联说明。原始outputs仍按忽略规则保留两端；在线报告/manifest不等于在线已有全部数据。
