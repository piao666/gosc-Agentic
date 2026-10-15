# Research Task Brief — approved statistical reproduction

- **问题**：[HYPOTHESIS] 在固定 Windows 环境中，原始 GOSC 各方法的任务/通信均值能否在预定实际等价界限内重现作者保存面板？继而才判断是否可做 receiver 假设诊断。
- **授权**：用户针对“获取 provenance、审定新的 R4 统计复现协议并保留原严格失败”批准。原 5200-run 与条件性 1200-run receiver 规划继续有效。本轮不联系外人、不发布、不下载模型/更换依赖。
- **前人成果**：[CODE] 原版387b493，当前工作8e97bc6；[RUN] R2/R3及93tests已有证据，严格R4失败及14次数值敏感性探针全部保留。历史83-slot来源未核验。
- **暴露声明**：已见1399条旧R4记录和seed0探针，不能称盲法预注册。新协议在本轮新数据之前固定；不使用已见差异优化方法、参数或选seed。
- **文件**：只新增独立runner/统计模块、必要统计测试、协议与报告；原gosc/实验/测试/结果/缓存不改。
- **实验**：原W100 frontier34点×100；原private6点×100；冻结headline12点×100独立seeds3000–3099，共5200全新执行。若统计门槛全部通过，再按既定独立4000–4099的2×2 receiver协议执行1200次。严格验收失败不改写。
- **验收**：52组×任务/UL symbols共104项，配对bootstrap最大标准化偏差同时区间，family95%，20000resamples、固定统计seed20261015；search均值±5%保存均值，rescue saved_fraction±0.02，symbols±5%。全部区间包含于界限内才标记 scoped statistical agreement；跨界为不确定，整段在界外为不一致。非显著不等于等价。
- **反证/限制**：均值一致不保证尾部/失败率/全部论文结论一致；全部分位数、完成/失败和逐seed差异另报。固定价格oracle非等成本；对历史保存面板的比较不证明作者生成环境。
- **成本与停止**：主环境CPython3.12.10/NumPy2.5.3，≤4 workers，每worker1数值线程；预计15–40分钟，R4硬上限45分钟，新增统计开销预计数分钟，原始输出约数百MB。测试先行；异常/保护哈希变化/缺seed立即失败，数值不一致仅留证不提前选停。无GPU/API/模型下载。
- **交付**：独立 `.local/reproduction/2026-10-15-statistical-v1/`，不可变plan/config/raw/统计；紧凑报告、命令及证据索引；最终Go/No-Go且暂停。
