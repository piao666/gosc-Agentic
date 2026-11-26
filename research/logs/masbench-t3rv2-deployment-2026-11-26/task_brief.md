# Research Task Brief — T3-R-v2 真实部署准入补齐

2026-11-26，Asia/Shanghai。用户要求“真实部署准入补齐，完成后再申请有界T3能力诊断”。

- **问题**：[HYPOTHESIS] 当前现场身份、配额、隔离能力和执行合同能否支持新版六阶段的安全部署？不检验真实任务能力或内容价值。
- **前人成果**：[RUN/既有] v2-I专用54、旧synthetic适配器67及独立审计通过；39冻结文件和10项执行源码绑定一致。此支持域不等于真实服务验收。
- **授权解释**：继续新增独立部署准入检查、必要合同和申请；允许本轮小型HPC无模型验证及只读现场身份/配额/有限metadata检查。保留所有既有未提交文件，不覆盖v2-I实现/报告。此前真实生成、服务配置调整和题目读取禁令没有具体新预算，故不自行运行生成、不切换服务窗口；若现场完成需要这些动作，先形成可审阅预算再请求授权。
- **拟新增**：`extensions/masbench_reasoning/fair_final_v2_deployment.py`、专用合成合同、HPC只读检查入口、准入矩阵/报告及下一运行申请。原base/protocol/v2-I默认、registry、T3结果/身份不改。
- **验证设计**：仅人工metadata与假后端验证准入和完整失败关闭语义；HPC现场检查UID/HEAD/同步、Python、CPU/RAM、Lustre个人配额、只读cgroup授权、服务PID+stamp/二进制/白名单环境、模型清单/helper小文件SHA、有限GET。不开模型、不读任何题文/gold、不创建tensor context。
- **本轮执行cap（运行前冻结）**：新增登记最多3次（readonly<=60s、contracts<=120s、audit<=60s），累计command wall<=240s；单worker/CPU至多2核，普通Python AS<=256MiB；输出<=4MiB、所有新增SSD管理/登记<=16MiB、HDD新增0、全量回传<=16MiB。HTTP仅GET `/api/version`、`/api/ps`、`/api/tags`各至多1次，失败不重试；生成/render/unload/计数helper/服务start-stop均0。记录实际值与未能证明的硬上界，不借旧授权。
- **停止**：版本/活动run/配额/身份不符即停依赖动作；不清理他人或历史目录，不更改cgroup/服务或下载依赖。无法证实的GPU/进程树硬隔离保持Blocked，采样不能代替强制。
- **反例**：空闲服务仍仅1024；当前用户无cgroup写权；GPU仅观察阈值；个人quota低于写前预留；旧HTTP worker只接受旧授权；64KiB IPC不足；服务defaults/render/usage仅有历史证据。
- **验收**：逐项证据和源码行范围、失败/未核项、明确Go/Blocked；只有部署前提齐全才提出条件明确的有界能力诊断申请，不自动开跑。不提交/push，不进入T4；T3/G1/GP-ID科学No-Go不变。
