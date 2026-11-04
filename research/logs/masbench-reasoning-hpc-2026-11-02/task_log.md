# HPC恢复连接后的只读核查结果

日期：2026-11-02 13:46（Asia/Shanghai），远端查询时间05:46:17–18Z。

- **Research Question / Hypothesis**：只核查静态适配的环境进入条件，不检验模型能力或任务效用。
- **已核验前人工作**：沿用已完成MASBench Reasoning固定版本审查，本次没有新增文献结论。
- **实际阅读源码**：已审阅的两个只读盘点payload；未修改GOSC/MASBench算法。
- **本轮新增或修改**：本目录只读脚本、原始stdout/stderr、inventory及核验记录；三份交付和research入口增加最新环境状态。原10月30日及11月2日失败证据不覆盖。
- **实际运行**：[RUN] `python research/logs/masbench-reasoning-hpc-2026-11-02/refresh_readonly.py`；内部两次`ssh -o BatchMode=yes -o ConnectTimeout=12 hpc /home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -`均exit0，payload来源及SHA在[inventory.json](inventory.json)。本地GET仅查询同端口version/tags。另运行本目录`verify_management.py`及Git轻量检查。
- **测试与结果**：项目测试、任务、模型调用、训练均未运行。元数据核查成功不等于Reasoning工程或能力验收。
- **失败/负面证据**：当前Ollama模型清单为空、旧三个标准manifest未见、项目依赖缺失。Windows同端口仍URLError。之前SSH超时记录保留，不回写为成功。
- **与原 GOSC 的差异**：仅更新静态环境状态；73个冻结源码与原报告保护项由管理核验确认。
- **公平性与泄露检查**：未读取.env、凭据、权重、私有证据或任务gold；未请求chat/generate，未加载/注册模型，未同步源码。
- **成本**：仅两次有界只读元数据SSH和GET；没有任务channel uses或模型tokens，未测吞吐。
- **可否进入下一阶段**：连接关卡Go；环境运行仍Blocked/No-Go；路线Conditional Go。G1与GP-ID科学No-Go保持。
- **用户需要批准的下一步**：若继续，另行决策现有模型定位/恢复、独立依赖环境和无模型工程合同的范围；本次不自动执行。

## 当前已核实事实

[RUN] 主机n1、UID8301880、项目路径及origin正确，HEAD为014b85dfc472c45d8ea5f15e83e0c1ed8e938daf；Python3.11.15。quota200000/100000、cpuset0–1、RAM25769803776bytes；NVIDIA L40、驱动545.29.06、34304MiB，当时used5940MiB。不能将used显存归因给本项目或宣称独占算力。文件系统free38605744787456bytes，不等于账户配额。

[RUN] Ollama0.11.11的GET version/tags/ps/v1/models均可达，分别为版本响应、models=[]、models=[]及data=null。原models/ollama-gosc根存在，但qwen2.5:3b、llama3.2:3b、qwen2.5:7b已知标准manifest均不存在；未扫描其他服务/位置，不能推断权重已删除。

[RUN] 包元数据numpy2.4.6、pytest9.1.1；openai/httpx/requests/python-dotenv/pandas/tiktoken均未找到。实际权重身份、许可、上下文、端点参数兼容、任务能力及数据完整性仍Pending。

原始证据：[environment_stdout.json](environment_stdout.json)、[environment_stderr.txt](environment_stderr.txt)、[model_storage_stdout.json](model_storage_stdout.json)、[model_storage_stderr.txt](model_storage_stderr.txt)。管理核验见[verification.json](verification.json)，不作为项目测试通过。
