# Research Task Brief — B1 无模型Driver整合与精确计数/context方案

日期2026-11-10 Asia/Shanghai。用户已批准上一轮建议的“精确计数/context方案及无模型Driver整合保护”。上一轮未提交工作保留，不重新请求相同范围授权。

- 问题：共享持久预算能否实际约束ControlledClient metadata/generation、run_controlled、wire/audit写盘与恢复；自有假worker/外层Driver挂起崩溃是否可阻断后续派发？如何精确重现固定Ollama模板/tokenizer而不把原料存在称作verified？
- 既有证据：B1-pre A/B只读完成、17独立安全合同通过；服务默认1024、模板身份不同，真实绑定及服务取消/完整硬边界Blocked；历史147+5不作本轮重跑事实。
- 范围：新增独立fixture-only Driver/集成合同/登记入口，必要的小范围保护修订须保留原17合同兼容及原run；新增计数/context实施方案及本轮验收报告、日志。原client/application/wire/registry/核心/冻结数据与旧四交付不改写。
- 运行：HPC经hpc_runs登记，单进程默认，外层120s、科学产物≤16MiB目标；假消息/假后端，不读真实题目或gold、不运行Reasoning效果任务。不安装/构建第三方依赖、下载模型、修改/重启服务、真实chat/generate、训练、提交/push。
- 预检：SSH UID/HEAD/origin/无running、实际CPU/RAM、现有运行库/构建工具与kernel只读；同步SHA核验。所有代码测试仅HPC。
- 反例：客户端关闭不等于Ollama取消；进程隔离不是可信用户的文件安全沙箱；跨进程预算若可重置则无效；整轮与请求截止包含清理的边界必须写清；fixture计数/绑定只能标fixture，不能升级为真实verified。
- 验收：实际经原ControlledClient+run_controlled的Full/No-A2A替身闭环，预留次数/96+2分区/usage/全写路径成本、失效/超时与分母、恢复/漂移/不利重跑拒绝；外层真实自有进程停止证据；计数/context具体可审阅方案及尚需额外授权事项。科学G1/GP-ID No-Go与真实B1 Blocked不自动撤销。完成后停止。
