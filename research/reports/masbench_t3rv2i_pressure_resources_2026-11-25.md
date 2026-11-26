# T3-R-v2-I 合成压力与资源合同状态

2026-11-25，Asia/Shanghai。**压力与精确词表计数未运行；本报告是已实现合同及阻断状态，不是压力通过报告。**

## 1. 本轮冻结预算

[HYPOTHESIS/执行前冻结] [model-free budget v1](../protocols/masbench_t3rv2i_model_free_budget_v1_2026-11-25.json)：HPC、≤2核、workers1、每进程AS≤1GiB；最多3次合同×120s、最多3次独立审计×60s、旧合成回归60s、压力60s，计算累计wall/CPU≤660s，登记执行总wall≤900s。新SSD（含同步/源码快照/pytest临时目录）≤64MiB、HDD新增0；单run输出≤8MiB、累计≤24MiB、输出文件≤512，pytest临时树≤4096文件/16MiB，完整回传≤64MiB。任何累计边界将超出前停止，不能偷偷追加修复轮数。

合同、回归与审计只用固定人造数据和假后端。压力可在其60s预算内进行最多一次、≤20s、≤1GiB AS的既有pinned词表helper批计数；必须验证vocab_only=true且tensor_context_created=false，不是模型生成，不发任何服务API、不下载依赖或模型。失败保留，不回退到字符计数冒充真tokens。

468 HTTP、50生成、19100s只是实现中模拟的**未来待审真实候选cap**，不是本轮实际模型额度。本轮实际Ollama包括metadata请求、实际模型生成、GPU和任务正文读取均0。

## 2. 合成输入压力实现

[CODE] `experiments_ext/masbench_t3r_v2_pressure.py::main/vocab_count`独立构建三类人为字节模式：ASCII、Unicode多字节、JSON转义字符；每类Full/No各一完整六slot候选。private information只含重复synthetic字串；不存在原四题问题、支持句或gold。

记录每次完整请求（包括System、LOCAL_TASK、原始己方历史、合法送达peer封装与全部公共时钟）的UTF-8字节、SHA、slot状态及可选完整render/token_ids计数。强制普通packet≤64KiB、累计普通packet≤512KiB、terminal≤8MiB。若JSON重复转义造成超界，只能拒绝并留失败状态，不能截断或压缩后继续。

注：约4KiB注入消息是保守应用字节压力，不假设它在真实词表上同时满足512输出token。合成压力样本不证明所有可能历史的最坏界；真实运行仍需逐请求完整计数、实际窗口/渲染/usage绑定。

## 3. 精确计数器接入合同

[CODE] `fair_final_v2_guard.py::CountProof.validate`绑定完整请求SHA、非负整数tokens、模型manifest、16384窗口和计数器身份；15872+512可接受、15873+512必须在派发前拒绝。FixtureCounter明确标记`fixture-byte-counter-not-qwen`，其数值仅合成单位。对应C18/C19测试尚未运行。

可选词表计数使用既有helper SHA e4d2da192c9bfcf126462eddfa2a8b8519b9d8293ff47bf500007ca2d82a66d5、固定template与manifest。验证输入bytes SHA、rendered SHA/bytes、token_ids个数及SHA、vocab-only与无tensor context。只用新的人造完整请求，不导入旧T2 development_inputs。GGUF仅核manifest关联与文件大小，不把它称本轮完整权重SHA重验或真实服务部署绑定。

**当前没有任何新真实token计数结果**，不能用字节/4或旧10288峰值替代。接入合同、helper可用性及完整结构的动态证据均Pending。

## 4. 持久预算与故障合同

[CODE] FairLedger复用原Ledger的fsync/hash链/锁/boot/deadline/token字节预留，采用新schema及不可扩大caps；generation/render/get/cleanup_get/unload/lifecycle_get统一持久收费，失败尝试不退，生成必须有唯一inflight预留、不能重复扣同一请求来派发。计划限8任务epoch+2合成、条件各最多24、任务48/合成2；每任务6次，每合成epoch至多1次。

准备/生成/管理、阶段时间与尾部安全余量有独立计数接口；不通过重开对象、journal或清理恢复生成额度。已派发unknown usage/崩溃永久栅栏；存储写失败保留预留、停发并在重开时校验已预约产物。FakeService只验证合成身份/退出观察，不触及实际服务。C21–C28未运行。

## 5. 实测与Pending清单

[RUN/管理] SSH只读：n1/UID8301880、Python3.11.15、cgroup v1 CPU2/24GiB，running登记为空。共享文件系统df不是个人quota证明；个人可用SSD、源快照实际增量、计数helper与实际资源峰值尚未核实。HPC旧HEAD/索引阻断尚未解决，故测试与压力登记数0、产物实耗未测。

真实服务RSS/GPU硬上界、模型身份/窗口现场绑定、真实管理RPC/清理/回滚、完整回传最坏时间均继续Pending。AS与CPU的拟执行RLIMIT代码、资源纯观察守卫和假服务测试不能证明真实部署通过。没有资源匹配实验或真实任务，本轮不讨论无线净收益。
