# 官方材料与新颖性核查 — 2026-10-22

[PAPER/CODE] 本轮只读打开论文原文/存档和作者GitHub，不下载、安装或执行第三方代码，不联系作者。私人PDF及完整提取文本仅本地使用。以下为已观察的材料状态，未找到链接不等于不存在，README宣称官方不等于实现可执行。

| 工作 | 原始来源 | 本轮发现与限制 |
|---|---|---|
| D06 PragComm | [论文](https://arxiv.org/abs/2401.12694)、[作者repo](https://github.com/PhyllisH/PragComm) | 论文给出该repo；根目录当前仅见README和1commit。未验收可运行源码。 |
| D08 ToM2C | [作者repo](https://github.com/UnrealTracking/ToM2C) | 可见model、训练、环境、通信削减与依赖入口，README给出MSMTC/CN命令；未下载、锁commit或运行。 |
| B05 SIAC | [作者repo](https://github.com/SSG2019/SIAC) | README自述部分代码；可见功率分配/重要性耗时等.m和压缩包，未完整复现。 |
| B06 ULSC | [作者repo](https://github.com/SSG2019/ULSC) | README对应题名；可见AMC/LLM、BERT、图文转换等压缩/分卷包，未解包核验。 |
| B08 LLM-SC | [作者repo](https://github.com/gujianhunwang/LLM_com) | 可见model_utils .py、test.ipynb与Apache2；README给Applied Sciences 2025,15(13):7227。DOI本轮429失败，出版社未独立核验成功。 |
| A10 FOL/LogiCity | [论文](https://arxiv.org/abs/2604.19614)、[所引环境](https://github.com/ahmetfsaz/LogiCity) | 环境repo含SPF/配置/仿真入口；不等于该论文语义选择算法与全部实验可执行实现。 |
| A02 BANDMAS | [v1正文](https://arxiv.org/html/2608.00458v1) | 核验题名/作者和准入框架；正文及题名+github检索未确认官方算法repo。arXiv的Report GitHub Issue不是论文代码。 |
| B10 iCoTASC | [v1正文](https://arxiv.org/html/2606.29052v1) | attribution/offline utility table/online refinement可核验；未确认可执行官方repo。 |
| D13 Proxifield | [v1正文](https://arxiv.org/html/2609.20889v1) | 四路由信号与附录prompts可核验；未确认官方可运行repo；提示词不等于完整环境。 |
| B11 GVQ | [v2](https://arxiv.org/abs/2602.02035v2) | 版本说明将摘要41.4%更正为71.4%，800/2800表值未变。accepted ICRA2026是作者存档声明，未另验出版页；未确认官方repo。 |
| A08 belief sync | [v1](https://arxiv.org/abs/2608.13394) | latent translation/MEC/adapter机制与本地一致；未确认官方实现。 |
| A04 token/KV | [存档](https://arxiv.org/abs/2605.25422) | 核验三作者和JMSRA；已有receiver history/compute影响通信媒体选择；未确认官方实现。 |
| A11 AgentComm-Bench | [存档](https://arxiv.org/abs/2603.20285) | 六扰动、grid-world和冗余/陈旧融合；未确认官方repo，未在本项目运行。 |
| A01 JTCM | [存档](https://arxiv.org/abs/2608.00368) | 任务条件token编解码/调制和两阶段训练；未确认本轮可运行官方实现。 |

[INFERENCE] 已有工作覆盖receiver需求/知识/ToM、删消息代理、离线轻量估值、变化触发belief同步、无训练语义路由、receiver历史/算力影响媒体选择。因此不能声称首次receiver-aware、首次反事实通信价值、首次offline-online或首次语义路由。潜在贡献只能收缩到：在明确可观测且付费的receiver状态下，固定其他GOSC模块后，是否超出强简单baseline的净闭环任务收益；本轮pilot尚未建立。

[RUN] 代表性查询为PragComm/Proxifield/BANDMAS/ToM2C/iCoTASC/JTCM/AgentComm-Bench/Token-KV/FOL精确题名+github，以及A08/B11精确题名；随后打开作者repo及arXiv abs/v1/v2 HTML。技术结论仅据原文/作者材料。其余正式出版、完整官方代码与全球新颖性仍未穷尽，不编造commit、下载或运行成功。
