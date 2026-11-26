# T3-R-v2 合成真实部署验证执行预算（本轮获授权）

2026-11-26 Asia/Shanghai。用户明确要求完成真实部署/真实模型验证；另明确批准“接受该监测停止合同，继续有界合成真实验证”。只执行两份既有人工输入，不包含真实MASBench任务或四题能力诊断。

固定Ollama0.11.11、qwen2.5:7b既有digest、16384有效窗口、temperature0、stream=false、输出各<=512、retries0。输入资产仍为`research/logs/masbench-t3rv2-deployment-2026-11-26/probe_inputs.json`，SHA9a1c1191f1a41a70f24c787f8698cec354ea78fbc0afc9d6366b2f2188cb104a，禁止按模型输出改写/补救。长期服务当前1024，只允许一次临时16384切换及最终1024回滚，start/stop各至多2。

生成至多2次，helper至多2次；生成/render各2、普通GET8、清理GET14、unload2、生命周期GET128，HTTP总156，所有尝试派发前永久扣账；读取超时/未知usage仍保留输入/输出预留，不重跑。输入总预留上界31744、输出1024，无真实任务分区额度。每请求150s准备（helper20、render120均在其中）、180s生成、40s当前epoch清理。生成前必须留足600s安全尾部，不用余额多发请求。

真实阶段总wall2000s：准备300/生成360/清理80/生命周期含权重全SHA600/应用120/独立审计120/完整回传300/故障余量120。执行入口1460s alarm，540s独立审计/回传/故障尾部；每请求及owned RPC另有限时。不可重置父journal deadline；失败后只安全收尾不恢复派发。

CPU现有容器硬2核、workers1、数值线程<=2；driver与helper逐进程AS硬2GiB，driver树2GiB、service树16GiB、GPU16GiB为用户已接受的监测停止阈值，**不是硬隔离**。主动阶段检查起点间隔<=0.5s，逾期/观测失败同样停派发；不保证两次采样之间无过冲。空闲切换/全权重SHA阶段单列观测，不冒充活跃生成的间隔证明。容器合计24GiB硬限不变，无驱动/模型/依赖变更。

真实HDD<=128MiB：ledger/artifacts<=99MiB，两个service log各硬文件8MiB（总16MiB），控制/应急及索引保留余量；SSD新增登记/源码快照/摘要<=32MiB。进入前SSD个人可用>=64MiB/HDD>=256MiB，每个大artifact写前再核SSD>=32MiB/HDD>=128MiB保护空间。原始请求/响应/计数/token ids/退出证据都在新HDD run目录，不使用symlink；完整定向回传<=160MiB。

前置新D01–D12无模型合同最多两次登记、每次120s，另一次独立审计120s；普通测试AS256MiB、fixture树放HDD，新HDD<=32MiB/SSD<=16MiB；不借旧54/67通过记录。测试/真实/审计均用hpc_runs登记并绑定source snapshot与未提交源码归档。

授权JSON由本轮明确用户授权具体化，仍须把实际新合同receipt/source/plan/Prompt/input资产与唯一run绑定；旧T3授权不接受。metadata返回/原始生成、usage、清理及1024回滚与全部产物读回均须独立审计。无法确认退出、陌生runner或回滚时保留marker/配置与证据，不强清、不卸载他人模型。

无真实题文/gold/registry正文读取、无能力成绩/内容因果/无线净收益主张、无T4/训练/正式test/校准、无Git提交push。未通过则记真实负结果，不能增加第3次生成解决工程问题。
