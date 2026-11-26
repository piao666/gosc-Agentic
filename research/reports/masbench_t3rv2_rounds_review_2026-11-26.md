# T3-R-v2近轮成果云端审阅总入口

2026-11-26 Asia/Shanghai。本次Git归档只整理已有工作，不产生新模型/测试/实验，不改变原T3/G1/GP-ID科学No-Go。下表按证据支持域阅读，旧Blocked报告保持原时点含义。

| 轮次 | 已完成与结论 | 审阅入口 |
|---|---|---|
| v2-I独立实现及无模型验收 | 新公平六slot/本地final/来源/失败分母及预算；54新测试、另跑67旧synthetic适配器、独立审计通过。不是模型效果 | [最终报告](masbench_t3rv2i_implementation_acceptance_2026-11-26.md)、[C01–C32与附件](../logs/masbench-t3rv2i-2026-11-25/README.md) |
| 压力及精确词表计数 | 35个人工完整请求；72929B IPC反例被拒绝；1GiB AS计数失败，获批2GiB单次补验成功，最大15046+512≤16384。非真实服务窗口验收 | [资源报告](masbench_t3rv2i_pressure_resources_2026-11-26.md) |
| 真实部署准入审查 | 原SSD余6.29MiB、服务1024、无子树/GPU硬隔离证据；独立入口及预算修复具体化 | [原准入审查](masbench_t3rv2_deployment_admission_2026-11-26.md) |
| HDD复用 | 获批迁634个非活动管理文件/87764721B，原字节保全/独立读回，SSD曾恢复91.23MiB，源码及实验原件不动 | [存储报告](masbench_t3rv2_storage_resolution_2026-11-26.md)、[回滚清单](../logs/masbench-storage-hdd-2026-11-26/README.md) |
| 合成真实部署 | 最终32新合同；qwen2.5:7b恰2次人工t0生成，625/8720输入、14/14输出，108.091165s；16384绑定、两次卸载与1024回滚通过 | [真实验收报告](masbench_t3rv2_live_acceptance_2026-11-26.md)、[D01–D12与完整附件](../logs/masbench-t3rv2-live-2026-11-26/README.md) |
| 事后独立审计/回传 | 1151事件、43份HDD原件审计通过；458文件/7763327B完整回传。长输入格式失败；自动审批用量故障使原2000秒连续交付超期，未改旧截止 | [逐字节小型证据](../artifacts/masbench-t3rv2-live-20261126/README.md)、[续办登记](../protocols/masbench_t3rv2_postdeadline_closeout_2026-11-26.md) |

## 云端审阅顺序与边界

先读真实验收报告的限制/反证，再查D矩阵、单次授权与预算、独立审计JSON和run身份；随后回看v2-I C矩阵与压力反例。完整原始请求/响应、源码包、重复source_snapshot与大receipt均已在受控两端保留，Git只携带小型汇总、状态/命令/失败日志及[原件紧凑SHA索引](../artifacts/masbench-t3rv2-rounds-20261126/evidence_index.json)。原件链接在云端可能不可直接打开，不表示未生成或未回传；可据SHA定位本地/HPC，不用公开大原件替代审计。

实际模型run仍绑定458a96f、snapshot20261126T032819Z、HPC授权LF SHA8ee5cdd329bf8a73ffe7b9dd9bdb713e7e236e01d1849c240b9083e4a7a36fcd；事后审计使用20261126T064855Z。此次提交身份不回填两者。历史T3继续b05ea73+20261125T034132Z。

## 需研究决策的事项

1. 两次合成服务执行与事后证据闭环通过，不等于完整六slot真实任务已测；当前live profile只允许两份人工输入。
2. 长输入MESSAGE缺换行，invalid_exchange，未抢救或重跑；原连续2000秒交付要求未满足，不能称所有验收全绿。
3. RSS/GPU只在用户明确批准的监测停止语义下通过，非硬隔离；活跃采样最大间隔0.237718061s，不保证采样间无过冲。
4. [有界T3条件申请](../protocols/masbench_t3rv2_bounded_diagnosis_request_2026-11-26.md)未批准且不可直接执行；须另补任务profile/授权/合同及真实预算。原四家族已曝光，不作为确认性或显著性证据，剩余52条/D1不变。

**实现通过 ≠ 无模型合同通过 ≠ 合成服务真实执行通过 ≠ 科研能力成立 ≠ 消息内容价值/无线净收益成立。** 不自动进入T4、训练、正式校准或封存评价。
