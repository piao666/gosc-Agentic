# MASBench Reasoning独立运行环境 v1

**最终状态：基础环境维护Go，模型加载/生成和Reasoning任务能力Pending。** 2026-11-02T07:29:11Z三个模型全部恢复且逐blob SHA-256通过；07:31:49Z独立SDK GET模型清单和三模型show metadata验收通过。没有运行题目、chat/generate或训练。配额失败、受控中止、用户精确授权的清理及新30分钟窗口见[最终维护报告](../logs/masbench-environment-repair-2026-11-02/report.md)。本项目历史digest相等不等于原论文作者历史模型版本已恢复。

日期：2026-11-02。范围为用户授权的模型恢复与依赖安装，**不是Benchmark集成或任务运行授权**。本次实际结果与失败见[环境修复记录](../logs/masbench-environment-repair-2026-11-02/task_log.md)，最终验收见同目录verification及HPC运行账本。

## Python依赖

[RUN] HPC Python3.11.15，独立环境：`/home/u202520081000097/jupyterlab/Paper/gosc/.local/envs/masbench-reasoning-v1`。Python入口为该路径下`bin/python`；它与原GOSC `.venv/bin/python`不同。

[CODE/RUN] 四个直接版本取自MASBench固定c0301a650db95958924bb080192c09fef39389a5的官方requirements：openai1.101.0、httpx0.28.1、requests2.32.5、python-dotenv1.1.1。选择范围见[requirements输入](masbench_reasoning_requirements_v1.in)；Reasoning原生入口主要依赖标准库和OpenAI客户端，未引入Scheduling/Game/MARBLE、可视化或训练依赖，也没有为“装齐清单”引入未使用的numpy/pandas/tiktoken。

[RUN] `hpc-masbench-dependencies-20261102`完成：uv0.11.19解析传递依赖与hash锁，按`require-hashes`及`only-binary`安装；`uv pip check`、四包导入和本地端点客户端构造/关闭通过。构造过程使用公开占位字符串、没有读.env或发模型请求。原GOSC环境包元数据前后相同。[Linux实际hash锁](masbench_reasoning_requirements_v1.linux.lock.txt)与该run原件逐字节相同；不得把Windows解析结果代替这份Linux实际锁。

后续HPC任务若获授权，必须显式选用独立环境Python，不能因原GOSC环境仍缺openai而继续在其内安装。未来登记入口的manifest会保留runner解释器；实际子命令的独立Python路径及其包快照需同时记录。

## 模型恢复边界

[RUN] 已核实服务PID8964使用正确模型目录，固定Ollama0.11.11；空清单来自已知存储内容缺失，未核实缺失原因。已批准恢复三个历史模型，事前官方registry返回的manifest SHA-256与旧记录一致：

| 模型 | manifest SHA-256 |
|---|---|
| qwen2.5:3b | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b |
| llama3.2:3b | a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 |
| qwen2.5:7b | 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e |

唯一blob合计8,632,391,403bytes。原10GiB/3600s窗口内的慢速/配额失败均保留，未静默重置；用户批准精确存储清理后，另有07:14:11–07:44:11Z的30分钟维护窗口。最终成功run为`hpc-masbench-model-restore-after-storage-retry1-20261102`，109.357746s、exit0；前序已完成下载/失败不计入这109s，不能声称全部权重109s从零下完。三个manifest与历史一致、每个blob真实SHA-256/大小正确、tags可见、ps无模型加载。许可原文随恢复产物保存，不能将模型许可等同项目MIT许可。Ollama/驱动/默认1024context均未改。

许可归档以`hpc-masbench-model-license-audit-20261102/outputs/license_layer_index.json`为准，4个层文件各有唯一digest文件名和已校验SHA。原恢复run对Llama多层许可曾使用同一文件名，原歧义产物保留，不从旧单文件路径推断完整许可；新索引补全实际层，具体适用性仍待后续审查。

## 使用与后续关卡

[CODE/设计边界] 本服务地址是HPC内的`http://127.0.0.1:11434`，OpenAI兼容地址为其`/v1`。Windows自己的loopback不是该服务。未来客户端应显式指定本地地址、无云端默认回退；此说明不是已经实现了Benchmark端点白名单。客户端key可用无敏感含义的本地占位符，不读取或配置收费API密钥。

[RUN/HYPOTHESIS] 本次不发generate/chat、不加载GPU模型、不改1024默认context、不运行题目。恢复相同模型文件与依赖仅解除对应环境阻断；OpenAI chat参数/usage/timeout兼容、实际加载与Reasoning能力仍Pending。数据正文/分组划分、无损等价、权限隔离、传输/CPU计价及完整诊断预算也尚未通过。G1/GP-ID科学No-Go保留；完成环境维护后停止，不自动开始能力诊断。
