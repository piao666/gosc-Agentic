# 隔离C++17安装、ABI合同与helper构建提案

2026-11-16。**提案；尚未批准新增编译器执行。** 旧Go构建停止门保持false，5次失败不重跑/改写。本次新增授权独立记录，不能当作原1800s预算重新开始。

## 已准备的具体清单

[RUN] `hpc-masbench-cpp-vendor-prepare-v5-20261116`，HPC n1/UID8301880，216.098090s、exit0；回执 `20261116T093042Z-b5454f`，全部已登记产物回传。源码同步1009文件/0差异，ID `20261116T091946Z`。这里只通过归档/源码检查，编译器未执行。

- **编译器候选**：官方Zig0.17.1 Linux x86_64，archive57,411,036bytes，SHA256 `3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a`。[官方元数据](https://ziglang.org/download/index.json)；实际经[官网镜像清单](https://ziglang.org/download/community-mirrors.txt)中的zigmirror.com分段传输，最终SHA/大小与官方元数据一致；未做minisign验证，不称已验证数字签名。
- **归档内容实测**：20,792成员、0 symlink/hardlink；常规文件展开374,407,381bytes（约357.06MiB），有 `lib/libcxx/include/filesystem`。尚未解压安装；路径及非普通文件在安装前再次拒绝检查。
- **许可证**：Zig根MIT；libc++/libc++abi等声明Apache2.0 with LLVM Exceptions，另有平台/第三方声明。9份显式LICENSE/COPYING已保存和核验，不代表工具链只有9种许可证；完整归档及全部原声明保留。不是“整包仅MIT”。
- **vendor**：Ollama v0.11.11 commit `92b96d54efd6b49322b7cf046f9a0dc16b00cd0a` 的 `llama/llama.cpp/vendor` 全目录，4文件5,268,882bytes；4个blob与3个tree逐一核验。miniaudio.h为MIT-0/公有领域二选，nlohmann json/json_fwd为MIT，stb_image为MIT/公有领域二选；保留完整头文件声明。完整大小/SHA见 `masbench_vendor_source_lock_2026-11-16.json` 与v5 `outputs/preparation.json`。
- **已有工具**：只复用 `/tmp/gosc-hpc-masbench-context-build-v3-20261116` 内已核验Go1.26.11、签名Ollama模块及缓存，不改系统GCC7.5、不改两套Python环境、不升级Ollama。默认system规则另核固定 `server/routes.go`（SHA256 `12d2889140fc0c84162bf7fe9fd84848670aed34caf1c1200631349cfbab3c8c`）。

## 申请执行范围与上限

1. 在上述自有临时根目录下新增 `cpp17-toolchain/`、`cpp17-wrappers/`、`cpp17-abi-probe/` 及Zig缓存，解压归档；不写系统路径。所有许可证随解压内容保留。
2. 用Zig bundled C/C++/libc++构建**仅此helper**，target固定 `x86_64-linux-gnu.2.27`、`-mcpu=baseline`。隔离wrapper将此构建的 `-lstdc++` 显式映射为 `-lc++`，避免混用两套C++ ABI；这是待验收的编译/链接选择，不是已证明兼容。
3. 先编译并执行小型C++17 `<filesystem>`/`std::string` 与Go CGO跨语言合同；失败即停。再复核7旧源码参考+新routes参考、恢复4个固定vendor到临时源码副本、编译离线helper并记录二进制SHA和Go build信息。不改原仓库算法、旧运行记录或部署二进制。
4. **新增构建阶段≤1200s**（包含失败清理）、实际CPU≤2；任务临时目录常规文件总量≤2GiB，构建进程组RSS≤2GiB，临时文件+进程组RSS+管理父进程RSS合计≤4GiB。临时盘是tmpfs，因此按内存一并计价；含已有Go/source/cache、工具链归档、旧镜像partial、67MiB管理归档临时副本和独立Git索引。采样监控不等于内核硬限制；CPU由现有2核cgroup限制，内存/磁盘超限时停止进程组并保留证据。
5. 不新增依赖下载（GOPROXY=off）；缓存不全即失败，不临时放开公网拉取。只运行上述固定工具链、固定源码和自有helper。
6. 构建通过后接原已批准的**离线合同≤120s/2GiB进程树RSS/16MiB产物**：14组纯合成消息render、42组窗口边界、4个special-token锚点；固定Qwen词表only，不加载权重、不建tensor推理context、不用GPU/HTTP。默认system依固定68字节层及首条role规则处理，保存原始/有效输入。独立renderer与special-token锚点不等于独立tokenizer，更不等于真实部署等价。

[HYPOTHESIS] 第一项ABI合同通过之前，不能称Zig候选兼容glibc2.27。helper+离线合同通过之后，也仅能称离线候选验收；真实context、无截断、服务端取消和恢复需独立部署授权/验收。当前Ollama默认1024及服务配置保持。

## 命令与停止条件

已实现待执行入口 `experiments_ext/masbench_cpp_vendor_build.py`，必须存在另行明确授权的sidecar `masbench_cpp_vendor_build_authorization_2026-11-16.json` 且绑定v5成功准备；当前该sidecar不存在。HPC `scripts/hpc_runs.py run` 登记，固定临时Git索引并先源码SHA同步；完成后标准pull。构建成功才登记 `experiments_ext/masbench_context_offline_contract.py <明确的成功build-run-id>`。

预算、源码/归档/SHA、ABI、格式或离线合同任一失败即停；保留失败，不重复运行整个1200s预算，不换编译器/关闭校验/放开网络/改服务来救结果。临时目录消失时不擅自重新下载。

**不包含**：实际模型加载/生成、真实题目、四题诊断、服务32768修改、正式test/训练、提交/push或其他目录清理。D1继续保留。

依据：AGENTS.md E明确“依赖安装、模型下载、第三方代码执行、收费API、长时GPU/CPU高占用任务先估算成本并征得用户同意”。先前确认指定官方Go及Ollama源码，未包含此新增Zig/Clang/libc++及链接ABI；因此本提案需一次新增明确确认。
