# HPC Ollama 用户级部署

部署日期：2026-10-20。此文的命令是操作入口；成功状态以 research/sync/runs/hpc-ollama-*/status.json 与 outputs 为准。安装或 smoke 不等于完整 LLM 复验完成。

## 路径和版本

- HPC：ssh hpc，u202520081000097@172.18.101.241:22610（需学校 VPN）。
- 项目：/home/u202520081000097/jupyterlab/Paper/gosc。
- 固定 Ollama0.11.11：项目 .local/ollama/runtime/0.11.11；命令包装器 ~/.local/bin/ollama。
- 模型：/home/u202520081000097/jupyterlab/models/ollama-gosc，可从 JupyterLab 的 models 下查看。模型权重不进入 Git 或本地源码同步。
- 服务：http://127.0.0.1:11434，仅 HPC 回环接口；本地 Windows 的127.0.0.1不是此服务。
- 状态与日志：项目 .local/ollama/service.json、service.log；服务使用用户权限，退出 SSH 后保留，容器重启后需重新启动。
- 真实复验服务配置：项目 .local/reproduction-services.json；仅全部模型验收通过后写入 ready。

## HPC 操作

```bash
cd /home/u202520081000097/jupyterlab/Paper/gosc
.venv/bin/python scripts/hpc_ollama.py start
~/.local/bin/ollama list
~/.local/bin/ollama ps
curl -fsS http://127.0.0.1:11434/api/tags
```

从本地可执行 `ssh hpc '~/.local/bin/ollama list'`。不要在本地另起推理实例；所有测试/训练/仿真/统计和模型调用继续由 HPC 登记执行。

## 复现约束

论文原代码模型名 qwen2.5:3b、llama3.2:3b、qwen2.5:7b；保存实际模型 digest/quantization。今日标签不保证等于作者历史权重快照，不宣称模型版本完全等价。验收用 num_ctx1024、num_predict12、temperature0、seed0 和 JSON choice schema，外加线程限制2；原 LLMClient 再以空的新缓存实际 HTTP 调用，必须 calls1、hits0、choice有效。api/ps 的 size_vram>0且 ollama ps 为100%GPU，才能确认 GPU 推理；不能只凭服务能响应判断。

缓存回放与真实 LLM 复验分开。不得修改已发表缓存，不得服务故障后用 planner 冒充模型结果。部署不启动新方法训练。具体任务设计、网络失败、校验和见 research/logs/ollama-2026-10-20/ 和 research/protocols/ollama_hpc_v1.json。

## 官方依据

- [Ollama0.11.11 GPU 支持](https://github.com/ollama/ollama/blob/v0.11.11/docs/gpu.md)：driver531+，含L40；当前驱动545.29.06。最新文档的550+要求与此固定版本有区别。
- [固定版本官方下载与 SHA256](https://github.com/ollama/ollama/releases/expanded_assets/v0.11.11)。
- [Linux 手工安装](https://docs.ollama.com/linux)、[FAQ 配置与 GPU 验证](https://docs.ollama.com/faq)。本项目改为用户目录，不运行 root 安装器或修改集群驱动。


## 已完成验收（2026-10-20）

[RUN] hpc-ollama-deploy-retry1-20261020 completed，exit0，516.104521s。三个模型均完整GPU加载，原LLMClient各真实HTTP调用1次、缓存命中0、choice=A；另各有一次JSON API smoke。均Q4_K_M。实际digest和响应/时延见该run的outputs/readiness.json、各模型smoke/integration JSON。此处不代表完整LLM mission复验已完成。

用户授权后删除旧Github--llm、HM，预删除allocated占用共26058240000bytes（约26.06GB/24.27GiB）；已有models与当前Paper/gosc保留。第一次解包EDQUOT以及慢速下载终止均保留失败记录。失败run因配额满未能写终态，后根据进程已退出和exit1日志恢复failed；准确结束时间未知，finished_at=null，reconciled_at单列。
