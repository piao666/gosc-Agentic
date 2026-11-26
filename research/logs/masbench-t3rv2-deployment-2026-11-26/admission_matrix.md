# 真实部署准入矩阵（现场核查后）

2026-11-26 Asia/Shanghai。原始证据：[HPC只读快照](hpc_readonly_inventory.json)。管理检查不冒充hpc_runs测试；新部署测试0、新LLM0。前序54/67为v2-I支持域。

| 项 | 事实与来源 | 当前判断/释放条件 |
|---|---|---|
| Git/host/Python | 本地/GitHub/HPC均458a96f；n1/8301880；.venv3.11.15 | 管理身份匹配，后续run仍需新同步SHA |
| 活动任务 | 扫status，无running/planned | 本次观测空闲，不是永久独占 |
| CPU与容器RAM | cgroup200000/100000、cpuset0–1、25769803776B | 总容器2CPU/24GiB核过；子树隔离未核 |
| SSD个人quota | 余6594560B，16MiB工作预算无法预留 | **Blocked**；3文件迁移申请待批，不能把共享df当quota |
| HDD个人quota | 余517812883456B | 当前容量充足，不自动获得写/迁移授权 |
| 服务及模型清单 | binary/helper/manifest/template/system SHA匹配；API0.11.11 | pin匹配；权重全SHA未重扫，不能写全部权重已验 |
| 空闲/lease/GPU | ps空、连接空、marker0B、GPU34304/0MiB | 只读快照通过；未试退出/rollback |
| 实际有效窗口 | 当前env1024、无override | **Blocked**；没有16384逐请求render/ps/usage新证据 |
| 应用真实入口 | v2.run_episode只接受FixtureDriver | **Pending**；须独立live版本与逐slot相等合同，不能删旧门 |
| 真实worker授权 | old RPC.require_authorization只白名单旧T1/T2/T3 | **Pending**；须新schema及唯一run/source/plan/receipt绑定 |
| 计数/usage | v2-I离线35请求成功；当时AS2GiB一次补验 | 既有离线证据；不是新服务render/usage绑定 |
| 持久预算 | FairLedger含fake_operation/live_authorized:false | 新live全路径账本/跨run父上限仍须实现和测试 |
| IPC | v2-I转义Full已有72929B拒绝反例 | 保持64KiB安全拒绝；不能声称所有合法历史可执行 |
| 资源硬上界 | 所查CPU/memory/devices不可写；GPU无16GiB分区证据 | **Blocked**；管理员硬隔离或明确批准监测合同变更 |
| D01–D12 | 设计在部署合同§3 | **未运行**，quota失败前停止，无虚构通过 |
| 服务切换/退出/回滚 | 当前未stop/start/render/unload | **未运行**；仅成功空闲快照不能代替 |
| 回传 | 只读快照从SSH直接保存本地；无新增run | 管理证据已收；无测试run receipt可声称 |
| 数据与历史 | 48份前序交付SHA不变；registry/题文/gold未解析 | D1/历史T3身份及科学No-Go保持 |
| 总判定 | 静态修复合同/预算已具体化 | **真实部署Blocked；有界T3申请未释放；T4不放行** |

新部署D01–D12、真实纯合成预检、完整回传均通过前，不能把本矩阵的身份通过项合成为部署Go。
