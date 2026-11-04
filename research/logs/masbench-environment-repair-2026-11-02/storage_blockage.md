# 账户配额阻断与剩余恢复方案

历史阻断快照；后续用户精确授权清理后已解除本次恢复阻断，三个模型/依赖/metadata验收完成。最新事实见[最终报告](report.md)和[完成记录](task_log.md)，下文失败与当时待决方案原样保留历史含义。

日期：2026-11-02。当前环境修复**部分完成，模型恢复未全部完成**；不以任务效果或模型能力为结论。

## 已完成及未完成

- 独立Reasoning环境安装/导入/uv pip check已通过，原GOSC包元数据不变；run `hpc-masbench-dependencies-20261102` exit0。
- qwen2.5:3b原生pull成功，Ollama校验并写manifest；digest与历史一致。
- llama3.2:3b下载到约98%，尚不能称注册/完整校验通过；qwen2.5:7b尚未恢复。全blob独立校验和最终三模型SDK验收未执行。
- 原始模型下载run受控中止，1912.014109s/exit-15；retry1第二次受控中止，904.705078s/exit-15，终态已写。两者不是成功恢复三模型的记录。
- retry2遇到`OSError: [Errno 122] Disk quota exceeded`，登记器写artifacts失败，status残留running，但只读确认PID8900已不存在。**残留running不代表任务仍执行；不能擅自写completed。** 空间恢复后须保存原状态并补失败reconciliation，结束时间/子进程退出码未持久化则保持未知。
- retry1的回传数据已在本地，但receipt写回HPC也被EDQUOT拒绝；两端完成状态不能称全部同步成功，需空间恢复后补核。

## 空间证据与可审阅处理选项

[RUN] 原模型目录内容缺失后，官方声明恢复三个模型需8,632,391,403bytes。可见共享文件系统约38TB free并不等于账户配额；本轮实际EDQUOT是硬证据。没有quota工具，不能编造账户总限额或余额。

[RUN] 只读目录盘点：项目`.local` allocated6,106,427,392bytes，其中`.local/ollama`5,508,472,832bytes；uv缓存`.cache/uv`6,603,972,608bytes。uv缓存57,229个普通文件中，单硬链接allocated约923,951,104bytes，其余5,648,748,544bytes有多个硬链接；**不能把6.6GB缓存总量冒称清理后可释放6.6GB配额**。共享extents/目录及配额计算可能另有差异。

[RUN] 已完成安装的Ollama tgz：`/home/u202520081000097/jupyterlab/Paper/gosc/.local/ollama/downloads/ollama-linux-amd64-0.11.11.tgz`，1,908,755,362bytes，allocated1,908,760,576bytes；旧失败partial安装包6,365,184bytes，保留失败原件。本轮未删除上述任何文件或缓存。

仅清理上述可重建缓存/完整安装包，保守可释放估算不足约2.84GB；剩余7b模型本身约4.68GB，另有llama尾段/元数据，因此这不足以支持全部恢复，不能让用户批准一个已知不足的清理方案后继续盲目写盘。

建议优先增加账户可用配额**至少6GiB**；或者由用户指定允许清理的其他目录，再只读核对实际可释放量/保护边界并形成精确清理清单。未获范围授权前不删除其他项目、环境、模型、原始结果/缓存或历史失败文件。

空间具备后仍须：修复失败运行的元数据与receipt；冻结剩余下载的新有界维护窗口（原模型恢复3600s截止不静默重置）；复用现有manifest/blob/partial，继续同两个历史digest；校验所有blob和SDK GET模型清单。不会运行Reasoning任务、generate/chat或训练。

需要用户决策的依据：[AGENTS.md](../../../AGENTS.md) J要求在“results、缓存或PDF会被覆盖/删除”等情形暂停请示；E/E1要求预算与资源授权。当前“修复模型并安装依赖”不被解释为任意删除其他项目或原始研究数据的许可。
