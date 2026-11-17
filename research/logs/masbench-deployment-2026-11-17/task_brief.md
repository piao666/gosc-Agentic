# Research Task Brief

2026-11-17。用户明确要求“进行真实部署验证”，承接已交付480s具体方案和离线成功合同。授权用于已有qwen2.5:7b、合成输入、临时1024→32768→1024服务窗口验证；无需重新安装/下载。

问题：真实V1请求是否在有效32768上下文中保留完整输入，计数是否与离线helper一致，断连后的卸载栅栏能否终止原runner？先前离线14/36/6/4合同已通过，不代表部署等价。

设计：2 debug、1正常V1生成(max16)、1流式断连(max512)、最多2卸载；GET≤40，总480s/420s停止新测试派发、单操作60s；CPU2、监测服务进程树RAM/GPU各16GiB、产物16MiB。临时服务参数修改有finally恢复，失败保留，模型/真实题目/训练/四题均排除；D1保持。原生即时idle没有直接接口时写未知，卸载后退出不可冒充原生取消。

修改：独立部署验收入口、授权记录、运行报告/索引。不修改现有算法/客户端/历史结果。当前本地dirty均为本会话已有交付，保留。前置只读已核n1 UID8301880、CPU2/24GiB、ps空、GPU0/34304MiB。验收要求固定helper/manifest/template/system SHA不漂移、长输入>1024并在32768内、render逐字节一致、正常usage一致/自然stop、卸载返回且ps空/旧runner消失、恢复原服务。

完成：run `hpc-masbench-real-deployment-20261117` 外层39.725243s、exit0；POST debug2/generate2/unload1，run内GET10。真实32768、两render和2443-token正常usage一致；取消后卸载栅栏通过，原生即时idle仍未观测。恢复PID37483/default1024/parallel1、ps空、旧runner37396不存在均独立只读确认。回执20261117T032230Z-620403全部已登记产物回传；报告 `research/reports/masbench_real_deployment_acceptance_2026-11-17.md`。没有真实题目/任务/训练/提交push。
