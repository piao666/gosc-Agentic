# Research Task Brief — approved fixed-checkpoint R32 precision experiment

- 授权：用户2026-10-18“批准执行”前一报告固定14snapshot、R4→32方案。起点9196a61effa745d97d0091585b7b5cd8cf11b4a8，启动clean；现有原始数据和报告保留。
- RQ：[HYPOTHESIS] 固定同一message/state/world，增加stream-coupled Monte Carlo repetitions能否降低标签噪声、稳定局部符号与排序？不增加独立mission N，不开发估值器，不将精度提高称新算法收益。
- 已有证据：[RUN] R4共8worlds/14点/112branches，meanDeltaT+1.09375、探索CI[-2.5,5.265625]；12/13非零点MCSE≥|均值|。strictR4 failed和R4-S1 inconclusive保留。[PAPER/CODE] 原GOSC和BANDMAS已有反事实/估值先例。
- 修改：新增precision runner/analyzer/loader契约与新research目录；复用且不改extensions.counterfactual及v1 branch。原gosc/results/cache/测试/旧报告/Obsidian不写。
- 设计：核验旧raw index、16checkpoint中14选定点、packet/tape/state/config/源码/lock/实际依赖；可信自产pickle先验hash再反序列化。只跑replicate4–31，每点56branches，共784；保留0–3及2个空时隙，不补点/新world。预先固定R4/8/16/32全层级，报告mean/MCSE/正零负分布、真实目标变化和mission-cluster统计。
- 成本：2workers，各1数值线程；新增实验wall900s硬上限，估计495s（由旧成本外推，非实测）。测试/归档另计，无GPU/API/Ollama/下载/安装；助手tokens未计量。
- 反例/停止：增加R仍可能改变符号、显示有害或不提高排序保真；全部保留，不能按好结果提前停止/扩R。源码/数据/环境不匹配先定位且不运行；错误/超时保留partial，不自动重跑。
- 验收：完整配对/唯一ID、旧112原hash保持、加载/干预/特征边界测试实际通过、不可变manifest/逐branch raw/来源hash、R4旧值精确重建、R4/8/16/32收敛表图和Research Task Report。实验结束报告并停止；新方法/额外world/重复扩张另审。
