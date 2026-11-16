# Research Task Brief — MASBench Reasoning B1-pre

日期：2026-11-10（Asia/Shanghai）。用户附件已完整阅读，范围为A tokenizer/context只读核验、B既有离线数据隔离描述性核查、C最小独立执行保护及无网络合同，完成四份指定文档后停止。

- 当前归档4754bede84bb6e6defd8e646a63e81ccd6a20b4b；历史科研014b85d+冻结扩展；MASBench c0301a6；固定模型qwen2.5:7b与原manifest。各身份不互换。
- 问题：能否可信执行exact_prompt_tokens+output<=effective_num_ctx；D1/D2下可保留多少任务家族/文章分量；执行driver能否共享不可重置预算且对失败/中断保持分母？
- 读取：用户列明的环境/预算/客户端规格、原prepare验收/数据决策、client/application/registry/wire、HPC注册/同步/Ollama脚本、已有registry/300行审计。
- 修改：仅新增B1-pre只读核验/描述性核查脚本、execution_safety独立保护模块及新无网络测试、四份交付/日志/状态导航；不改原策略、旧数据/registry/gold/评分/历史产物。
- 运行：所有新分析/测试在HPC经hpc_runs登记；A/B单进程120s/16MiB（已有模型文件头只读、不载入推理）；C目标≤120s/16MiB。无模型、网络生成、训练、安装、下载、服务重启/改配置、Git commit/push。源同步/哈希为管理操作。
- 反例：架构context不是生效num_ctx；有vocab/merges不等于计数器已验证；52行不等于52独立问题；客户端进程被杀不等于外部Ollama取消；journal通过不保证任意写盘进程受目录总quota约束。
- 验收：逐字段证据/缺口；残余52的家族/分量准确汇总及D1/D2比较；预算/硬watchdog/失败/恢复纯fixture合同；Go/Conditional Go/Blocked明确。不伪造ContextBinding，不用本轮测试冒充147+5重跑。
- 停止：真实任务、正式测试/训练维持禁止，G1/GP-ID No-Go保留。未核关卡输出具体权限/依赖/成本方案，所有失败保留。
