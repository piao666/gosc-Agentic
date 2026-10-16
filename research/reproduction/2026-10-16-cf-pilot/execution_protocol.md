# Receiver-CF v1 approved execution record

2026-10-16。用户“批准”上一报告具体执行方案；此前冻结协议和proposal保留历史not_run状态，不回写。此次authorization见approval.json，绑定原协议SHA。

- 上一阶段base37cf326f163a25faafc6c3d439b7068e6528f990；原核心387b49389385b51c275dc5a22ec1672087edda1d不修改。保留strictR4 failed、R4-S1 inconclusive与ToM路径限定诊断准入。
- 实现仅临时包装原生实例的transmit/decodes/step/plan；实际组建候选、调度、ACK、fusion、移动与后续策略仍为原方法；hook在finally移除。不替换核心算法。
- 固定Config()与seeds5000–5007、t8/24、每点一个原生已选E/I、SHA256最小ID选择、R4、双分支；不可补空点或多选。packet ID是agent/type/ordinal/rate/bits/symbols/prefix records/intent/confirmation的canonical SHA256。选择时不看decode/outcome。
- 原生当时所有UL尝试先录tape；两分支原始decoder均执行并消耗同一draw，仅选包effective return覆盖；current selected options/其他packet decode必须一致。每个现场点native direct与tape完整state hash先核对，再运行分支。
- 每个replicate只在本时隙通信完成后重置五条future RNG，keys[seed,t,sender,replicate,stream]。保持native顺序流，不称逐格相同噪声。shadow当前融合后/移动前假想规划与下时隙移动后＋新感知后的真实规划分列。
- 不新增encoder/真实网络字节：native UL payload bits（含内置header）、UL symbols、delivered bits、DL broadcast bits/ceil uses逐branch保存；ACK/CRC/PHY/state-sync额外成本标not_modeled，不写实测0。独立进程peak RSS是lifetime peak，不能当每branch增量内存；CPU/process_time及wall单独记录。
- features白名单只含sender/共享可得信息与原代理值，不含private receiver/world truth/future labels；offline状态pickle可信自产且仅存.local，features与branch结果文件分离。未训练任何模型、无LLM/API/GPU。
- 2workers各1数值线程、整批wall900秒/128branches硬上限。输出新.local/reproduction目录；每seed独立append-only原始JSONL，异常/超时保留并终止批次，不自动重跑。未完成不是伪造completion_time400。
- 分析前固定：point标签先平均4配对差，再mission内等权、最后mission等权。bootstrap4000、seed0、mission cluster；重复抽到同一mission时保留其抽样重数。Spearman average ties；少于3点或2个不同mission/常数时undefined，记录有效bootstrap数。8clusters只是pilot，R4的MC SE逐点报告，cluster CI不另传播MC方差。无事后挑类型/调整阈值/确认性显著性主张。
- no-op/native回放、prefix/多包/ACK/队列/重传/终止、RNG、observer不变性、空选包、错误tape拒绝、特征泄露、timeout、统计重数等契约在tests_ext/test_receiver_cf.py；完整测试通过且source hash一致才准入，执行前提交并冻结commit。

新CLI只接受output-dir与gate-file，拒绝dirty checkout、旧输出目录、非.local/reproduction输出、未经批准协议、未测源码。`--help`和写入行为已审查后再执行。报告/数据不得改称新policy实验或严格基线通过；完成后停在报告节点。
