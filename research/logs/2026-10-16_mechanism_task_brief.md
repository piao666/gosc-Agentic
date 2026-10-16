# Research Task Brief — receiver mechanism and counterfactual protocol review

- **授权/起点**：用户“进行此阶段”，批准上一报告建议的机制审查与同状态离线反事实/成本协议制定。base d1eddaebc63313f222da7b5bb759a3e86a4da4d3，启动工作区clean。当前阶段不是新方法开发或新多seed实验授权。
- **科学问题**：[HYPOTHESIS] GOSC代理效用与实际Planner决策/消息生效时序之间，哪些差异可以通过同状态反事实独立识别？现有作者诊断是否已经覆盖，哪些设计会产生混杂？
- **前人成果**：[RUN] Receiver-D1主要六项区间均跨零，未确证稳定≥5%收益，也未排除；strictR4 failed与R4-S1 inconclusive保留。[CODE] 原TeamModel为softmax代理、位置同时影响policy和utility。
- **拟改文件**：新增机制映射/证据卡/实验与成本协议，必要时新增只用于验证复制与时序契约的小型tests_ext；不改gosc、原实验/结果/缓存、旧分析/协议或Obsidian。
- **验证设计**：全文审查相关源文件；只读核对本地D01及直接相关先例PDF。构造有限的状态/行为契约检查，验证复制隔离、随机流、接收融合时序、hysteresis等，不采集性能数据，不以构造反例估计缺陷频率。新snapshot/rollout批次只形成协议，不执行。
- **成本**：本地阅读/静态分析及短契约检查，CPU预计数分钟内；无依赖安装、模型/数据下载、付费API、Ollama或GPU。PDF仅本机解析，不上传到文档解析服务。
- **可能反例/停止**：代理与实际动作差异可能与真实任务收益无关；不可将单一构造反例写为稳定损失。若作者已有同机制诊断，明确借用和边界；需改变任务/划分/新多seed运行则停在具体协议等待后续确认。
- **验收**：逐机制源码行/论文页锚点；清楚区分直接receiver消息与原edge融合语义；配对随机流、干预边界、主要终点/统计单位/成本/否证条件可执行；测试仅报告实跑；完整Research Task Report、manifest、证据索引和可审阅下一阶段计划。
