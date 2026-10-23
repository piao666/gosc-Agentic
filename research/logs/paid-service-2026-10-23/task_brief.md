# Research Task Brief — 付费服务链与实验关卡

- 授权：用户要求开始接通完整付费UL/DL服务链、明确等待/计算成本并制定对照/新世界/样本与预算。本轮保留本会话此前未提交改动，在其上新增；不reset/clean/覆盖旧产物，不提交/推送。
- [CODE] base4ff4147654c07781d77a42acee3f31c0b8792f38；原核心不改。先沿用已映射的普通/realistic两条估值路径、PoseKnowledge与RTTLane。原GOSC ToM/公共广播/计费已有，不宣称新颖性。
- [HYPOTHESIS] 显式task与summary在相同UL/DL预算下竞争、CRC/反馈/广播付费、计算服务延迟后，数据能否只在真正到达时进入估值cache？首先验软件合同，不检验任务增益。
- 修改范围：独立bytes服务内核、HPC合同测试与协议/报告。已有原生task为抽象bit计数，没有完整wire codec；必须区分真实序列化的服务层输入与尚未完成的native task适配，不能伪称已完成闭环公平比较。
- 设计：外部冻结预算与slot时长、单CPU队列、task优先UL、共享DL串行队列、实际帧CRC、per-receiver loss、TTL、RTT重试与截止截断。codec/等待均付费，实验对照与停止标准在独立文档列出。
- 验证预算：HPC1数值线程、单进程pytest<=300s；0GPU/0LLM/0训练/0新收益campaign。检查身份/配额/源码sync SHA后执行；失败保留新runID修复，不本地回退。
- 反例：无DL容量仍能用摘要、未计帧可改变Planner、旧ACK删新代、CPU未完成即发射、task服务绕预算、无限任务后续slot或混用bit与byte。任一合同失败停止效果试验。
- 验收：服务层合同/HPC回归与时序账本、无摘要回退，明确native adapter与真实PHY仍未验；新world须查重，样本量须独立calibration方差/功效，未决项不填写猜测数值。本轮不擅自启动全量或改变原评估划分。
