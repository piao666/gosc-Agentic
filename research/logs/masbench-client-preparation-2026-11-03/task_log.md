# Task Log — MASBench P0–P2 preparation, 2026-11-03

## 授权与不变项

用户批准按顺序执行数据分组复核、开发清单、受控客户端及无模型验收，并给上下文/资源预算；真实四题Full/No-A2A仍未批准。保留全部已有dirty研究文件、原始数据、旧报告、失败记录和G1/GP-ID No-Go，不reset/clean/checkout/提交Git。

先写brief；Get-Content/rg读取AGENTS、README、总说明RQ/泄露规则、最近审阅/验收/环境与同步约束，git status/HEAD/origin只读核对。首次SSH超时stderr已保存；用户回复恢复后重试核实UID8301880、HEAD014b85d、2CPU/24GiB、无running。没有本地测试或数据分析回退。

## 顺序执行事实

1. P0/P1规则在新HPC计算前固定：空title/空support不连边，支持句绑定文章；所有共享context边和同题边保留；不同问题家族与2easy/2hard为硬条件，不同分量是审阅稿所述事前软偏好。选题不用gold、score、文本长短或模型输出。
2. `python scripts/hpc_runs.py launch --run-id hpc-masbench-registry-v2-20261103 --kind analysis --stage MASBENCH-P0-P1 ... -- {python} scripts/masbench_reasoning_prepare_registry.py`：0.794674s、exit0。排除14个空键，旧新均38组/最大242，同组关系差0；context-only也给出相同结构。4题覆盖4分量，预留248行/余52，模型未曝光。正式三分未冻结；原两异常及家族未入pilot，未清洗/改索引。
3. P2 `... launch --run-id hpc-masbench-client-contract-20261103 --kind test --stage MASBENCH-P2 ... -- {python} scripts/masbench_reasoning_client_contract.py`：119通过、2.191897s。实现ControlledClient、ContextBinding、端点/timeout/usage/hash/failure合同及新driver，只接替身。
4. `... launch --run-id hpc-masbench-context-budget-20261103 --kind analysis --stage MASBENCH-CONTEXT-BUDGET ... -- {python} scripts/masbench_reasoning_context_budget.py`：0.236796s、exit0；16个初始请求bytes/hash，max system16423bytes；独立env没有列明tokenizer模块，未安装依赖或推断token数。
5. 补充共同操作超时、exclusive持久审计/容量合同和实际httpx异常分类后，`... launch --run-id hpc-masbench-client-contract-v2-20261103 ... -- {python} scripts/masbench_reasoning_client_contract.py`：最终123通过/0失败，0.784098s；旧119保留，不加成242不同tests。
6. 同一已核验sync用hpc_runs.remote_command登记`hpc-masbench-httpx-mock-20261103`，实际子解释器为`.local/envs/masbench-reasoning-v1/bin/python scripts/masbench_reasoning_http_mock.py`：独立环境httpx0.28.1 MockTransport 5通过，0.296490s；socket.connect禁止、真实HTTP0/模型0。没有向独立env安装pytest，也不在原GOSC env安装客户端依赖。

每条登记run完整argv、cwd、Git dirty、资源和SHA在manifest。所有产物写各run outputs，未覆盖旧目录。所有pytest只在HPC运行，100s子进程/120s外alarm，单进程；新产物分组图约1.7MB，未越16MiB准备上限。时间/RSS含runner管理开销，不作模型独占性能。

## 回传、预算和停止

最终输出receipt `20261103T071309Z-841281.json`、all_outputs_mirrored=true，写回HPC；新增回传22,063,042bytes主要包含runner源码快照与metadata，不是LLM结果。verify_management.py本地仅文件/哈希/receipt检查，73冻结源/保护的旧审阅源不变，当前7个新Python文件与最终HPC测试snapshot一致；git diff --check通过。

预算提案为4家族×2提示族×2通信设置=16episodes，任务96＋合成预检2=98请求，512输出cap，总输出≤50176tokens；候选32768上下文下输入上界3161088tokens，60s操作共同期限、全局6000s/256MiB。候选qwen2.5:7b是事前单模型提案，未调用、未改模型/服务。真实部署tokenizer/effective num_ctx、实际吞吐/显存和余52行的未来独立评价充分性仍Pending；不能把bytes或模型metadata当验证，不将预算提案当授权。

本轮模型调用0、任务episodes0、训练0、安装/模型下载0、付费API0；数据/contract分析不等于新任务实验。通过后停止，实际诊断须另批；若要新增tokenizer依赖或改服务context，先提出具体方案。


## 最终driver等价补验

补充两提示族×12个既有原生fixture对新run_controlled逐request/memory/stop/legacy兼容验证；有效null completion按原生空串处理并留empty标记。hpc-masbench-client-contract-v3-20261103最终147通过，0.924613s；hpc-masbench-httpx-mock-v2-20261103用相同源码在独立env再次5通过，0.190794s。旧119/123与第一次5项原件保留，不累加为不同样本或单run总数。

预算明确限制：实际精确tokenizer/effective context未核；HTTP timeout/晚响应拒绝不冒称物理取消，未来执行driver需请求级与全局hard watchdog以及wire/审计共同产物cap。当前模型调用仍0；预算不是可执行授权。


## 最终文件核验与文档上行

最终输出receipt20261103T072351Z-cbea65，新增回传22,087,652bytes，all_outputs_mirrored=true且写回HPC；大部分为runner源码快照和元数据，不是新任务实验。verify_management确认7个HPC run、147最终pytest/5独立httpx、所有产物hash、原73冻结源码与旧审阅保护源不变，当前Python与最终执行snapshot一致；链接/空白和git diff --check通过。

源码/报告上行20261103T072635Z已verified，793文件、SHA mismatch0，修复此前文档仅本地的落后状态；最后增加本完成记录与“未本项目曝光不排除预训练污染”表述后再同步。最终源快照身份以HPC .local/hpc-sync/latest_manifest.json及同步工具stdout为准，不在源文件中回填其自身sync/hash。无running科研run；没有重跑已通过测试、真实模型或任务。同步结束即停止，不提交Git。
