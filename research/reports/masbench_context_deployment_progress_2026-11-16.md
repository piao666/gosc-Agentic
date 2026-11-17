# 数据隔离、精确计数与真实部署三项推进报告

2026-11-16 Asia/Shanghai。**D1方向已决定；Go与固定模块校验完成；helper未构建成功，真实部署仍Blocked。** 本轮没有真实Reasoning任务、模型加载/生成、GPU推理或Ollama服务变更，没有正式评价/训练或Git提交/push。

## 1. 三项工作的实际状态

| 用户要求 | 本轮实际推进 | 当前判定 |
|---|---|---|
| 评价主张与数据隔离 | 用户明确选择保留D1，形成[决策记录](../benchmarks/masbench_d1_evaluation_decision_2026-11-16.md)，原registry/四题/异常不改，D2只保留备选 | **D1方向完成**；正式校准/封存划分与功效仍Pending |
| 精确计数准备/隔离构建 | 固定官方Go1.26.11 archive/SHA，获批后在HPC执行登记；模块签名验证与7参考文件SHA匹配；Go helper和独立渲染/边界合同代码已写 | **部分完成，编译Blocked**：现有C++标准库与完整vendor源码不足；没有可用helper或合同通过证据 |
| 真实部署验收 | 当前身份/资源/配置重新核验；梳理实际debug渲染、裁剪、取消和卸载链，交付[具体合成验收方案](../benchmarks/masbench_real_deployment_acceptance_plan_2026-11-16.md) | **方案完成，实际验收未运行**；有效32768、无截断、计数一致、服务取消均未verified |

本报告的Go/No-Go是工程准入判断，不是任务收益或论文创新结论。旧G1/GP-ID科学No-Go保持。不能把“推进三项”写成三项全部验收通过。

## 2. D1：已经明确的研究边界

[RUN/用户决策] 保留按文章关联组隔离，优先保证文章隔离。后续主要主张限定在本项目开发中未复用文章关联组的任务上；不宣称排除模型预训练污染或证明所有分量统计独立。

原开发预留248行、余52行/36家族/34文章关联分量保持，2条原异常仍在原分母/标记中。正式calibration/evaluation尚未切分，不为了增加N拆大分量或把开发文章重新称未见。新真实题目模型曝光0。

## 3. HPC身份、版本与资源核对

[RUN，本轮管理读取] n1/UID8301880、项目Python3.11.15，实际CPU quota200000/100000、cpuset0-1、RAM25769803776bytes（24GiB）。当前Ollama0.11.11 PID8964，单并发/单模型，默认context1024；`/api/ps`返回models空列表。可见L40总34304MiB，查询时使用0MiB，不代表已验证模型峰值。

启动远端HEAD4754bed，晚于此前归档但落后本地916289b。先核901文件SHA与已知sync20261116T024042Z全部一致、origin相同且无running记录，再使用增量bundle、ancestor和原子update-ref将归档引用快进916289b。未reset/checkout/改index或历史run，随后标准同步逐次SHA mismatch0。详见[归档核对回执](../logs/masbench-context-deployment-2026-11-16/archive_reconcile_stdout.json)。

首次沙箱SSH被拒后按规则升级连接成功；cgroup-v2路径不适用、旧Git不支持branch --show-current，后续采用已知v1路径与symbolic-ref。没有把这些初次管理错误写成测试失败或环境不可用。

## 4. 工具链与来源

[CODE/官方元数据] Go1.26.11是当前仍受支持分支的维护版，官方Linux amd64压缩包66,999,944bytes、SHA256 `9849f4e04ee35303714e34fbc3ac8ab44ea3e448a95aa182f91e3b9b79c710ec`。实际下载后校验通过，安装仅在HPC临时隔离目录，不改PATH、系统编译器或两套Python环境。[官方清单](https://go.dev/dl/?mode=json)、[支持与维护记录](https://go.dev/doc/devel/release)。

[RUN] HPC访问proxy.golang.org与sum.golang.org返回Network is unreachable；goproxy.cn可达。改为镜像传输，保留Go默认`GOSUMDB=sum.golang.org`签名公钥验证，不关闭sumdb。固定模块的Go验证结果：

```text
github.com/ollama/ollama v0.11.11
Sum: h1:mErMiUGclp47rCDbSUmBiY2L76EpT0uIYRZVBO6qg/k=
GoModSum: h1:9+1//yWPsDE2u+l1a5mpaKrYw4VdnSsRU3ioq5BvMms=
```

[RUN/CODE] 模块分发不提供Origin commit字段，本轮没有伪造它。以固定release/signed模块身份及此前核定的source92b96d54...对应7份官方源码逐字节SHA对照，`go.mod/go.sum/template/template.go/server/prompt.go/openai/openai.go/llama/llama.go/runner/llamarunner/runner.go`均匹配。该记录不能称为整棵Git tree独立校验；本次再次取tag API因连接器传输错误失败，既有11/10 release映射身份保留。

## 5. 五个登记run及负结果

| run（统一前缀hpc-masbench-context-build） | runner elapsed | 实际结果 |
|---|---:|---|
| -20261116 | 0.423447s | 自有预分配文件以只写模式打开，posix_fallocate报Bad file descriptor；下载/编译0 |
| -v2-20261116 | 0.726638s | 修正为读写后，4GiB home预分配遇真实EDQUOT；下载/编译0 |
| -v3-20261116 | 32.448509s | 改用HPC tmpfs，Go archive校验/安装成功；官方模块网络不可达，停止 |
| -v4-20261116 | 5.425162s | 镜像传输且签名验证成功、7份源SHA匹配；复制的cmd目录仍只读，入口创建失败 |
| -v5-20261116 | 51.130733s | 修正仅临时副本目录权限、复用缓存后进入编译；C++头/标准库不足，exit1 |

[RUN] 五个run的status、stdout/stderr、build.json、源码快照与回执全部保留；最后receipt `20261116T074353Z-31a565` 为all_outputs_mirrored=true，前四轮分别072208Z-97c3a8、072420Z-c582d5、073425Z-d23292、074054Z-562807。失败不是5次成功测试，也没有正式pytest/模型任务结果。

[RUN/实现纠正] 首轮文件打开模式、第四轮复制目录权限是本轮实现遗漏，已明确记录并修正；修正没有修改旧失败身份。没有把这些当成原作者算法缺陷。每个后续run都有已定位问题与变化，未盲目重跑相同构建或重复旧科学实验。

## 6. 配额处理与资源实账

[RUN] 账户home无法完成4GiB分配，v2预留文件实际分配336,011,264bytes后失败。随后仅将本轮这一个已知占位文件截为0（保留inode与失败证据），回收其实际占用；没有删除其他项目、模型、原始结果或历史run。

`/tmp`是HPC的tmpfs，查询约376GiB available。因此将构建放在`/tmp/gosc-hpc-masbench-context-build-v3-20261116`，派生上限收紧为临时目录≤2GiB、构建进程组RSS≤2GiB，并监控tmpfs目录+进程RSS+父进程RSS合计≤原4GiB。它是采样watchdog，不是内核瞬时硬隔离。临时文件消耗内存已经披露，没有把它当免费磁盘。

[RUN] 五个runner登记时长合计90.154489s；不含SSH、同步和回传管理时间。累计下载payload81,272,231bytes（含最初Go archive，不按新run ID清零）；最后scratch逻辑字节488,416,377，低于派生2GiB。模型权重下载0；模型生成0；未测GPU推理峰值而保留null。v5 runner child_max_rss340548KiB包含runner子进程范围，不作为模型独占峰值。

编译目录是临时盘，可能被HPC清理；不能把当前Go安装当成永久部署。未产出helper二进制。完整源/失败日志留登记通道，临时构建缓存不复制进Git或home挤占账户配额。

## 7. 真正的构建阻断及下一关卡

[RUN] 现有GCC/G++7.5.0、glibc2.27，无clang++或已定位的较新g++。编译错误明确包含：

```text
fatal error: filesystem: No such file or directory
fatal error: nlohmann/json_fwd.hpp: No such file or directory
fatal error: miniaudio/miniaudio.h: No such file or directory
```

[CODE] Go模块zip会排除vendor目录，这是其[分发规则](https://go.dev/ref/mod#zip-files)，并非镜像或签名校验失败。因而“Go模块完整通过校验”不能替代“完整Git源码足以编译CGO”。本次helper引入legacy llama C++封装，需要补齐对应commit的vendor头文件及可用C++17标准库/编译链。

**当前停止同一构建重试。** 新增[current build status](../protocols/masbench_context_build_status_2026-11-16.json)将current_build_allowed=false，入口在下一次运行前拒绝继续；原Go安装授权保留历史含义。下一步应固定隔离C++17工具链与完整vendor源码的来源/版本/hash、许可证和总资源清单，核是否仍满足原cap，再就新增安装清单获得批准。未自动安装GCC/Clang、打第三方兼容补丁或换tokenizer近似实现。

离线合同代码已写：12组ASCII/中文/emoji/Unicode/空白/多角色/重复板等合成render、4组special-token和预算边界；**未运行**。它有独立模板展开，但tokenizer仍是同源调用，不冒充第二个独立tokenizer。未将helper候选或fixture binding置为verified。

## 8. 真实部署：已明确的验收边界

[CODE] 固定源码支持debug_render_only，可用来比对实际模板渲染，但它会scheduleRunner且`chatPrompt`可能裁剪输入；需与离线完整render逐字节比对。health只表示ready，不表示没有活动生成。源码存在断连取消链，实际部署没有新生成验收。

[HYPOTHESIS/待批准方案] 具体提案为480s（内部420s+60s清理）、2合成生成+2debug+最多2卸载、GET≤40、输出16MiB、无真实题目；context扩大/服务回滚、实际usage与停止/卸载栅栏各自核验。此提案不是已获批的新模型预算，也不是当前已可执行协议。不能在helper不通过时先改服务加载模型。

## Research Task Report

- **Research Question / Hypothesis**：三项准入工作能否形成可信链；不检验新方法收益。
- **已核验前人工作**：[CODE]固定Ollama源码及Go官方工具链/模块规则；[PAPER]未新增论文效果结论。
- **实际阅读源码**：Ollama固定template/prompt/routes/runner/openai/llama/go.mod/go.sum；本项目hpc_runs、sync_hpc、hpc_ollama、client、已有context预算入口。
- **本轮新增或修改**：D1决策；Go helper、隔离构建和离线合同入口；构建授权/临时盘修订/停止状态；真实部署方案、本报告、任务日志/源码参考；导航与状态新增本轮对象。
- **实际运行**：五个HPC infrastructure run，完整命令与同步hash见各run manifest；只读身份/版本/配额/元数据管理核查和自有占位回收；无科研seed/model任务。
- **测试与结果**：Go archive、模块签名和7份源码对照通过；构建失败，离线合同未运行，旧147+5/17/24未重跑；无新CI/任务分数。
- **失败/负面证据**：Bad FD、EDQUOT、网络不可达、只读副本目录、缺C++17/vendor均保留；不因来源校验成功标部署Go。
- **与原 GOSC 的差异**：不改原GOSC/旧估值/无线策略、client/wire/registry、原结果或cache；仅新准入原型与记录。
- **公平性与泄露检查**：用户选择D1；没有真实题目模型曝光，D2/正式划分未擅改；B1预算与本轮构建费用分开。
- **成本**：详见上；81,272,231下载payload、约90.15s登记执行，管理回传另计；0模型/GPU推理/任务收益N。
- **可否进入下一阶段**：D1方向Go；helper工程Blocked；真实部署/B1 Blocked；正式test/训练和G1/GP-ID科学No-Go保持。
- **用户需要批准的下一步**：先具体化新增C++17工具链/完整vendor清单再批准安装执行；之后才谈真实服务变更及合成部署预算。不将本轮Go授权扩成系统升级、GPU生成或四题授权。
