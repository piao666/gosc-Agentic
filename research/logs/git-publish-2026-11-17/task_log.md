# Git归档管理记录

2026-11-17 Asia/Shanghai。用户授权一次详细报告+本地整合+正常GitHub提交。分支research/progress-audit-2026-10-19，base与提交前远端均916289ba20fd9808a3673af0aebf175bfc830ccc。

本次只做Git、文件/JSON/哈希/Markdown/敏感路径/大文件与stage字节核验；没有新的HPC测试、模型推理、实验或服务操作。此前15个run（4 completed/11 failed）和上次提交前的67、147+5、17、最终24合同等分别归档，旧计数不累加。固定五部分详细说明为 `commit/2026-11-17-01-context-tokenizer-and-real-deployment.md`。

20份小型原始JSON逐份匹配原artifacts，80,630bytes；16份完整receipt原件19,943,370bytes保留本地/HPC，Git仅存SHA/大小及本轮run条目索引。15run元数据、失败/unknown状态、先前running副本和归档侧车保留；所有原始patch/tar/gzip与outputs继续忽略。源码参考保持原字节，未上传模型、环境、私人PDF或凭据。

初始文件审查和实际stage审查：blockers0、73冻结源不变、20小型输出与16原receipt指纹一致、受保护GOSC/结果/客户端无修改。实际stage新证据blob与本地raw bytes一致。检查自身JSON不自哈希，最终路径数以Git树/审查记录为准。

首次默认沙箱git add失败（.git/index.lock Permission denied），没有暂存成功；按已给Git授权提升权限后暂存成功。不是自动审批拒绝，也未请求用户重复授权。

默认全量空白检查把-text保留的CRLF原件报作行尾空白；不修改证据。明确 `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check` 后exit0，无真正例外；结果见whitespace_check.json。不存在为变绿删改失败日志。

审查完成后一次普通commit（带Commit-Note）及正常push当前授权分支，不force。实际归档身份由Git历史/远端引用核实，不在本记录回填自身哈希，不追加第二次说明提交。随后科研工作须核HPC Git/source身份，本次不会自行更新HPC引用或回填历史run。
