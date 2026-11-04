# Research Task Brief — MASBench Reasoning静态适配

- 目标：核实Alice/Bob私有证据、消息与上下文边界、free/protocol、评价分母/异常/成本及数据许可划分；定义只拦截真实A2A消息的最小无线接口，提出强基线与未来能力诊断关卡。
- 范围：仅MASBench Reasoning；GOSC HEAD014b85dfc472c45d8ea5f15e83e0c1ed8e938daf+冻结扩展。现有dirty研究文件属于已记录前轮成果，按用户指定作为基础保留，不reset/覆盖。保留G1/GP-ID全部科学No-Go和失败记录。
- 方法：官方论文/README/可访问源码只读，争取固定第三方commit；当前HPC身份/配额/Python包元数据/Ollama inventory只读，不生成LLM请求，不启动服务或加载模型。若远端不可达，只记录历史证据/阻断，不本地替代测试。
- 交付：research/benchmarks/masbench_reasoning_adapter_spec_v1.md、masbench_reasoning_feasibility_review.md、masbench_reasoning_gate_matrix.md；日志/证据索引/文件身份及管理核验。
- 假设：[HYPOTHESIS] 私有互补证据可提供内容消息识别空间，但原始评价/共享transcript/终止行为可能与无线损伤冲突；接口必须保持私有任务信息、显式可见时刻与评价分母。静态审查不证明模型能力、净收益、新颖性或可发表性。
- 修改边界：只新增静态文档/管理证据和研究入口；不集成benchmark、不改GOSC/冻结算法/候选/数据/划分，不运行测试/任务/统计/训练、不扩N、不下载模型/数据集或安装依赖、不调用LLM/收费API、不提交Git。
- 成本：轻量Git/哈希/文档读写、公开文件只读、一次有时限只读SSH环境/服务元数据检查；无HPC科研计算。未来运行/存储只给公式/声明参数的预算情景，不编造吞吐或能力。
- 验收：代码事实具体路径/行号/版本，设计另标HYPOTHESIS；列zero-impairment身份对照、原生/修订评价并列、终止/超时/丢包/UL/DL/CPU规则、强简单对照、泄漏与反证条件；明确Go/Conditional Go/No-Go和未放行事项，交付后停止。
