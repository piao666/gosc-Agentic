# Research Task Report

- **Research Question / Hypothesis**: 当前HPC的L40、驱动545.29.06、glibc2.27与2CPU/24GiB配额，能否运行原论文模型的真实GPU/JSON推理？[RUN] 已通过部署及接口验收；不表示完整LLM mission复验完成。
- **已核验前人工作**: [CODE] 原gosc/llm_agent.py的LLMClient使用Ollama generate、JSON schema、temperature0/seed0/num_predict12/num_ctx1024；[官方兼容文档](https://github.com/ollama/ollama/blob/v0.11.11/docs/gpu.md)给出531+驱动与L40支持，据此选择固定0.11.11，并以实际GPU运行验证。
- **实际阅读源码**: HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f；gosc/llm_agent.py、scripts/repro_extra.py、hpc_runs.py、sync_hpc.py、repro_legacy.py、repro_ordered.py、原experiments/run_belief_divergence.py。官方release SHA256来自expanded_assets/v0.11.11并与下载校验和交叉核对。
- **本轮新增或修改**: scripts/hpc_ollama.py（用户级部署/真实GPU与原客户端HTTP检查）；scripts/hpc_ollama_cleanup.py（用户明确授权的两目录清理）；research/protocols/ollama_hpc_v1.json与ollama_storage_cleanup_v1.json（冻结版本/预算/清理边界）；research/reproduction/ollama_hpc.md（操作指南）；本日志目录；AGENTS.md与research/sync状态/计划。repro_legacy.py修复原脚本无main入口兼容，tests_ext新增3项回归。
- **实际运行**: 全部计算HPC。hpc-ollama-adapter-tests-20261020通过10项(3.71s)；hpc-ollama-storage-cleanup-20261020完成37.682647s；hpc-ollama-deploy-retry1-20261020完成516.104521s；hpc-ollama-final-check-20261020完成0.111619s。命令与源快照以各manifest为准。清理运行命令为hpc_runs.py launch --kind infrastructure --config research/protocols/ollama_storage_cleanup_v1.json -- {python} scripts/hpc_ollama_cleanup.py；部署控制器由hpc_runs.py run登记、4h上限，顺序运行hpc_ollama.py install与prepare。最终核验运行本目录final_check.py。
- **测试与结果**: [RUN] 三模型qwen2.5:3b、llama3.2:3b、qwen2.5:7b均Q4_K_M，每个JSON API smoke及原LLMClient实际HTTP调用成功，原客户端各calls1/hits0/choice=A；api/ps有size_vram且ollama ps显示100%GPU。模型digest、请求、响应、tokens、耗时和GPU快照保存在部署run的outputs。最终审计确认服务API0.11.11存活、模型齐全、原gosc/experiments/tests/results/LICENSE的Git diff为空，当前项目和既有模型目录保留。只清理Github--llm18602799104bytes和HM7455440896bytes，合计26058240000bytes（约26.06GB/24.27GiB，预删除allocated占用而非精确账户余额）。
- **失败/负面证据**: 初次HPC官方资源下载约46KB/s，终止本轮专用下载(exit-15)，部分文件保留；本地临时中转TLS中断后续传成功，1908755362bytes的SHA256为1d2988c29346e6af0216c847db20f7df7794412ae56674eeec21e0917113843f，两端均匹配官方。第一次解包EDQUOT122，连runner终态写入亦失败；恢复failed时确认原进程不存在且日志exit1，精确结束时间未知，finished_at保持null/reconciled_at单列。用户授权清理旧项目后重试成功。当前驱动老旧的性能warning保留，未升级系统/驱动。旧复验队列c-belief适配器异常已修复，但未自动重启或重复已完成四阶段。
- **与原 GOSC 的差异**: 原算法、模拟器、测试、结果、缓存、LICENSE不变。用户级固定兼容运行库；今日模型digest已记录，不保证等于作者历史权重快照。安装检查prompt不属于论文科学任务。外层legacy CLI适配只执行原有CLI守卫体，保留Pool截获与原argparse行为。
- **公平性与泄露检查**: 原发表缓存未用于本次真实HTTP验收；每个原客户端使用新run的隔离缓存。没有用planner回退，没有新方法调参/训练，没有修改seed划分，没有上传私人PDF或SSH凭据。公开参数选择不是缺失的原1000–1079校准流程，缺口仍保留。
- **成本**: 模型标签大小约1.93GB/2.02GB/4.68GB，blob共享可能略省；安装包1.908755362GB。每个模型API smoke限制12输出tokens/1024上下文/2线程，原客户端再真实调用一次；实际tokens在各smoke.json，不把HTTP客户端计数冒充推理token总量。数值线程/CPU配额最多2，service并发1、加载最多1模型；GPU峰值未独立采样，不将单点显存或runner子进程RSS写成峰值模型成本。清理释放量以目录分配统计为准。
- **可否进入下一阶段**: Go：真实LLM服务已就绪，HPC .local/reproduction-services.json已写入。Pending：原顺序队列仍需明确resume清单/新runID和输入核验，从c-belief继续，已完成四阶段保留；完整P1、完整live任务、原校准与新方法训练未完成。
- **用户需要批准的下一步**: 本轮安装与指定旧项目清理已按用户授权完成；已授权的剩余复验可继续推进，不需重复审批同一范围。此授权不扩展为自动清理其他新目录、升级驱动或启动新方法训练。

完整运行证据：research/sync/runs/hpc-ollama-*/。执行状态与本地回传完成状态分别看status.json和receipts；最终同步回执见evidence_index.json。
