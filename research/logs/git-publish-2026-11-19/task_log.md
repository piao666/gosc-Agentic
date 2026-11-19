# T1 归档管理记录

2026-11-19，Asia/Shanghai。工作树基线 `d5f5522f99872d7453ef54cce06c9ae941846877`，GitHub 当前研究分支在归档前指向同一版本。执行为一次普通提交及推送，历史 HPC 运行身份以各自记录为准。

- `git status`、`git rev-parse HEAD`、`git branch -vv`、`git remote -v`、`git ls-remote --exit-code origin refs/heads/research/progress-audit-2026-10-19` 复核工作树和远端。
- 经 `scp` 读取 HPC 的 `STATUS.md`、`dashboard.json` 和两份 HDD 归档定位侧车。首个面板命令的花括号由 Windows SCP 当作字面路径，失败后改用精确路径，未改 HPC 文件。最新面板与本地 32 条 T1 登记的状态、退出码及耗时逐条一致；本地旧面板中的非 T1 登记在最新 HPC 面板中无差异。
- 本地运行 `python research/logs/git-publish-2026-11-19/prepare_archive.py`，逐一核实登记来源快照、30 份关键产物的大小和 SHA-256、10 份完整回执原件 SHA。32 条记录中 10 条失败，其中两条收尾缺失。三个中断写入的空临时文件、完整回执、原始 outputs 与源码压缩包在原数据通道保存。
- 6 个关键文件按同步时的 LF 规范化后，与最终现场及独立审计的原始源码快照逐份核对 SHA-256，均一致。
- 暂存前按路径检查发布范围、大小、凭据模式、GitHub 文档入口和关键证据；暂存后使用 `git diff --cached --check` 及 Git blob SHA-256 检查。历史只读记录与普通源代码分别审查。原始 GOSC、客户端、测试数据划分和结果目录均沿用基线。用户提供的审阅附件继续留在本地。
- 本轮只有 Git、传输和归档管理，没有运行新的 HPC 测试、模型推理或科研实验。
