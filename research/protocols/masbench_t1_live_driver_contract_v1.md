# MASBench T1-A真实Driver静态接线与无模型合同 v1

2026-11-17。base d5f5522。用户当前仅批准T1-A，T1-B真实合成端到端另批；不调用真实模型/helper，不修改服务。本合同不授予T1整体Go。

## 复用与边界

复用原ControlledClient/ContextBinding/LivePermit、CampaignLedger/Limits及run_controlled/LocalAgent/ContractTransport；不改旧fixture sandbox/语义。新增live_driver是单独命名空间，禁止fixture证据用于Qwen verified。T1-A注入无网络IO时模型身份全零且固定fixture名称；真实RPC默认拒绝缺失/未批准的T1-B授权sidecar。测试可运行固定无网络子进程fixture，不执行任意argv。

## 不变量

1. 启动身份绑定runtime、协议/registry/plan/source SHA与资源上限；服务PID+starttime、binary/helper/model/template/system及实际context派发前复核。未知和漂移拒绝。
2. 完整messages经同源模板/计数，overflow在任何HTTP前拒绝；实际debug/render与runtime证据才可构造当次ContextBinding，fixture域与live域分开。旧2443样例不授予通用verified。
3. CampaignLedger预留后fsync才释放HTTP worker输入；失败/未知usage不退款。保留started/inflight/uncertain，不重置deadline、requests/token或control额度；不重派失败ID。
4. 根目录单写者/全局服务lease、拒绝symlink/未知文件。科学产物和cleanup control各有持久上限，普通metadata不能消费cleanup reserve；原始RPC/信号及HTTP动作持久记录。
5. 锁持有人或服务独占无法确认时不卸载。清理前先验证当前自有服务身份与驻留model/context，不能卸载共享/身份漂移服务，更不能kill服务PID。信号只发给已登记PID/starttime的自有worker组。
6. 断连/超时/外层异常与unload分开。恢复凭证必须引用经哈希链验证的control事件及原始unload/ps/runner观察；仅提供ps_empty/old_runner_exited布尔必须拒绝。原生即时idle一直unknown。恢复闸门不擦除历史fence或unknown成本。
7. 请求正常/usage缺失/usage错/length/空回答/HTTP非200/超时/崩溃分别留audit；空回答沿用原client空应答标记，不事后删除。

## T1-A验证与T1-B停止门

新增无网络合同验证身份、C−1/C/C+1准入集成、fsync预留时序、总预算/恢复/失败、control拒绝/lease/目录/写盘错误、worker TERM/KILL/guardian与实际application两提示/Full-NoA2A路径。fixture不执行旧helper合同，不冒称真实服务取消验证。

独立审查使用另写的读档校验器核WAL/恢复事件与预算，不把writer passed字段当证据；静态审查若仍有不可封闭的真实路径或outer guard缺口，报告Conditional Go/Blocked，不以fixture数量掩盖。

交付T1-A报告/矩阵/原始HPCrun与回执后暂停。T1-B具体提案最多4次真实合成生成/1088预留输出tokens、debug4/unload4/GET40、480s、RAM/GPU各16GiB采样及恢复方案；仍需用户明确批准，当前不执行。T2长期窗口、T3四题（需先T5a）另行审阅。
