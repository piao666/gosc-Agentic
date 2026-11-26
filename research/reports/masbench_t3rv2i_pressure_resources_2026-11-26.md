# T3-R-v2-I 合成压力与资源合同验收

2026-11-26，Asia/Shanghai。**合成结构与离线精确计数的获批支持域通过；真实服务/硬资源上界仍Pending。**

## 实际输入与反例

[RUN] 三类人造ASCII/Unicode/JSON转义、Full/No各一组，无原四题或剩余池正文。现有35份完整请求（系统、LOCAL_TASK、原始历史、peer包与公共时钟）最大序列化72929B。ASCII与多字节两条件及转义No完成；转义Full在t4触发`IPC_packet_or_cumulative_cap`，未截断/压缩/补请求。35不是35个独立任务，均属工程字串。

该反例说明16384窗口内的token可行性并不保证64KiB序列化可行性；不能用样本最大值证明所有未来历史的最坏界。约4KiB注入字节压力也不假设真实输出同时满足512-token限制。

## 计数合同与原始失败

[RUN] 原pressure v1写审计文件出现OSError并持久栅栏，errno未保留，不能唯一归因为quota；同期元数据/同步有明确EDQUOT。v2把虚构bytes/4单位当窗口判断触发拒绝；修压力器为固定虚构计数单位，真实tokens只由词表helper判断，真实16384/512门未改。v3唯一初次helper在1GiB AS下Go runtime分配失败；未返回计数，不报告虚构tokens。

用户明确批准[资源修订](../protocols/masbench_t3rv2i_counter_budget_revision_v2_2026-11-26.md)，仅同一输入再1次，硬AS2GiB、helper≤20s、RSS512MiB采样停止阈值、无真实服务。输入SHA `f74a175d813aa004fa2135a13799e95575b3c68b6c443f7901bea6be3c4da0c2`不变。

补验成功35条：最大input15046，+512=15558，窗口余826 tokens；没有新生成消息。helper elapsed2.036729902s，观测RSS75030528B，raw stdout2175709B，完整保存在`counter-raw.json.gz`，解压SHA `89100991863c06172981e4020568cb6819190caf7d434f4487e0de7718567abc`。输入/模板/render/token_ids数目与SHA均由独立工具核验，vocab_only=true、tensor_context_created=false。失败+补验共2次词表调用，不是2次LLM推理。

helper/template/manifest SHA及GGUF路径/size核过；GGUF全文件SHA未重扫。AS解释得到补验支持，但不能由低RSS证明Go普适内存需求或把RSS采样当硬限制。真实服务model/PID、16384有效窗口、render及usage尚未现场核查。

## 预算与计量

冻结v1为2核、单worker、计算累计wall/CPU660s、登记wall900s、输出24MiB、新SSD64MiB/HDD新增0；仅获批计数单批AS由1GiB改2GiB。九run command wall30.013862s、child CPU16.883957s，均远低累计cap。合同仅2/3允许尝试、独立审计1/3；旧回归1次；压力失败前缀及只读结构汇总保留，没有再调用helper。源同步/归档/SSH等管理耗时未计入该command合计。

HTTP468、generation50、19100s均是未来真实候选上界。本轮对应计数测试只模拟分类操作，实际Ollama metadata/生成请求均0，不复用旧T3授权。input/output永久预留、分区/条件、唯一request、每epoch清理、预算与重开栅栏实际由C18–C28新合同覆盖，不是旧T1通过记录。

SSD逻辑文件/临时目录有cap检查，实际遇到个人quota失败后保留记录并转存/无损归档本轮临时数据；没有持续测量整个任务SSD峰值，**不能声称64MiB已成为OS硬配额保证**。未来须有个人配额与预留写空间核查。真实service RSS、GPU16GiB硬上界、同步/回滚最坏时限、完整真实任务IPC/token可行性仍Pending。

独立审计及全部回传通过；本轮仅工程Go，不支持内容价值、无线净收益或真实任务能力主张。
