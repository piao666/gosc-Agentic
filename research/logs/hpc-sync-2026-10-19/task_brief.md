# Research Task Brief - HPC execution and synchronization

- 用户授权：更新 AGENTS，后续项目 CPU/GPU/RAM 测试和训练全部在 HPC 执行；将 E:\gosc 同步到 JupyterLab 的 Paper 内。
- RQ / Hypothesis：[HYPOTHESIS] 能否保留上游基线、当前未提交研究文档和原始结果，同时建立可验证的 HPC 工作副本？
- 前人成果：[CODE] main@876fc52、原作者基线 387b493；已有 Windows 验证是历史证据。
- 已核验路径：[RUN] Paper=/home/u202520081000097/jupyterlab/Paper，为空；目标 Paper/gosc。
- 已有修改：本会话已授权的进度审计文件，全部保留并纳入同步；禁止 reset/clean。
- 变更范围：AGENTS、README 工作区说明、workspace_paths、HPC 操作说明与单向同步 helper、本轮日志。
- 验证：HPC 上解析同步脚本；Git bundle 恢复历史；全部同步文件 SHA-256；保护原始结果/缓存；不运行项目 pytest、仿真或训练。
- 成本：轻量文件打包/哈希与 SSH/SCP 网络传输；无依赖安装、模型下载或模型推理。远端验证遵守 2 CPU / 24 GiB 配额。
- 反例/停止：目标目录与截图不符、远端原始结果有差异、Git HEAD 不一致、同步哈希失败。
- 验收：AGENTS 两端一致；指定连接及执行规则持久化；Git 历史和当前文件在 Paper/gosc 可核验；输出同步 receipt。
