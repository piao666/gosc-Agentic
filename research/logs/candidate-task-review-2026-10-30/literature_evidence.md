# 公开研究先例与benchmark核验记录

访问日期：2026-10-30。仅原始论文/官方项目资料；不使用搜索摘要的性能数字作结论，不下载或执行第三方代码/数据。本轮为指定问题的局部阅读，不称系统综述。仓库README读取的是当日main，**没有锁定第三方commit或验证可运行性**。

## L1 GOSC

[PAPER] Farhad Rezazadeh, Hatim Chergui, Lingjia Liu, Merouane Debbah. *Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams*. arXiv:2609.39477v1，2026-09-30。本轮核验HTML§IV-C（Eq5/最长前缀）、§V-D/G/H；原本地PDF页码映射见`research/logs/GOSC_paper_code_map.md`。不据预印本声称正式期刊录用。[原文](https://arxiv.org/html/2609.39477)

五句卡：研究任务与无线资源协同。已有what/when/reliability和ToM，不是我们的新贡献。候选由每rate最长前缀形成。复杂ToM与受限LLM的外推须遵守原文边界。它要求我们区分表达限制、代理差异和真实任务效果。

## L2 ToM2C

[PAPER] Yuanfei Wang, Fangwei Zhong, Jing Xu, Yizhou Wang. *ToM2C: Target-oriented Multi-agent Communication and Cooperation with Theory of Mind*. arXiv:2111.09189v2（2022版本）；本轮读§3.3及相关§3.4–3.5。[原文](https://arxiv.org/html/2111.09189)、[作者官方代码/ICLR2022说明](https://github.com/UnrealTracking/ToM2C)。OpenReview PDF访问返回验证页；不因此声称其出版信息不存在。

五句卡：研究目标导向合作。目标推断参与通信筛选。通信删减用消息前后策略差异辅助学习。它不是本项目Planner/native wire的直接数值基线。它否定“目标感知过滤/ToM通信本身首次”的主张。

## L3 BANDMAS

[PAPER] Jiangwen Dong, Wanyu Lin. *BANDMAS: Causality-Inspired Semantic Packet Scheduling for Bandwidth-Efficient Multi-Agent Collaboration*. arXiv:2608.00458v1，2026-08-01；读§IV-A–D、V-G、VI。正式录用未核验；论文链接匿名代码不等于本项目已复现。[原文](https://arxiv.org/html/2608.00458)

五句卡：研究LLM生成消息中的片段准入。区分packetization与replay价值。线上特征隔离最终答案。作者将效果限于冻结traffic/受控lossless评估。新路线必须超出“typed片段+预测值+调度”的已有组合，不能只加无线包装。

## L4 Collab-Overcooked

[PAPER] Haochen Sun, Shuwen Zhang, Lujie Niu, Lei Ren, Hao Xu, Hao Fu, Fangkun Zhao, Caixia Yuan, Xiaojie Wang. *Collab-Overcooked: Benchmarking and Evaluating Large Language Models as Collaborative Agents*. EMNLP2025，pp4922–4951，DOI10.18653/v1/2025.emnlp-main.249。核验正式元数据与PDF§4.1、Table2、Limitations（PDF pp4–6/9，印刷pp4925–4927/4930）；不是将早期arXiv少作者版本混为最终元数据。[出版页](https://aclanthology.org/2025.emnlp-main.249/)、[PDF](https://aclanthology.org/2025.emnlp-main.249.pdf)、[官方README](https://github.com/YusaeMeow/Collab-Overcooked/blob/main/README.md)

五句卡：两agent完成有前后依赖的协作任务。资源与任务知识不对称。环境状态仍公开广播。小模型能力及过程评价开销限制迁移。它更适合长依赖候选，但需先查旁路信息和完整通信能力，不能先大规模实施。

## L5 MASBench

[PAPER] Qizhi Chu, Zekai Yu, Sijie Wen, Yang Liu, Chen Qian, Cheng Yang, Chuan Shi, Zhiyuan Liu. *MASBench: Benchmarking LLM-based Multi-Agent Collaboration under Partial Observability*. arXiv:2610.04672v1，2026-10-03。读§4、附录C.3–4/D/E相关信息边界与评价；未核验正式录用。[论文](https://arxiv.org/html/2610.04672)

[CODE] 当日官方README的Overview、Metric conventions and reproducibility notes、Data Sources and Licensing：Reasoning legacy分母与words计数需特别审查；Reasoning的HotpotQA派生数据不应因仓库代码MIT而误当同许可。[官方README](https://github.com/BUPT-GAMMA/MASBench/blob/main/README.md)

五句卡：研究部分可观测协作。任务覆盖证据问答、私有日历和资源游戏。协议/记忆/路由已有公开参照。确定性评价函数不等于模型输出确定，README的部分legacy口径也不能直接用于丢包研究。优先做Reasoning静态边界核查，尚未批准运行或保证本地模型可用。

## L6 CoLLAB

[CODE/官方介绍] Saaduddin Mahmud, Eugene Bagdasarian, Shlomo Zilberstein. *CoLLAB: A Framework for Designing Scalable Benchmarks for Agentic LLMs*。[官方项目页](https://agents-collab.github.io/)、[README](https://github.com/Saad-Mahmud/CoLLAB_SEA/blob/main/README.md)。读取问题/通信/agent分层与symbolic参照说明。OpenReview forum、pdf及attachment端点本轮均返回浏览器验证页；搜索可见workshop抬头仅作元数据线索，不作为正文核验或NeurIPS主会录用证明。

五句卡：用DCOP骨架研究LLM协调。公开分层便于隔离通信接口。数值utility可对照symbolic规则。私有字段是否泄露到prompt未做源码核验。当前作为备选，不凭README即宣布满足receiver-information研究要求。

## 交叉比较与未核验项

- GOSC/ToM2C：已有目标/意图驱动通信；前者无线/typed网格，后者学习目标合作，不能直接搬分数横比。
- BANDMAS/GOSC：两者都有价值与资源控制，任务/消息边界与传输模型不同；“引用相关”不等于同成本外部基线已跑。
- MASBench/Collab-Overcooked/CoLLAB：分别优先检查私有证据与评价分母、显式长依赖和全局状态旁路、结构化效用与private prompt边界。没有任何一个仅靠“公开”二字就通过本项目可复现验收。
- 没有系统核完所有新近工作/所有benchmark，没有第三方固定commit、安装验证、模型能力或功耗/费用测量；任何“最先进/首次/可以发表”的推断均无依据。
