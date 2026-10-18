# Fixed-checkpoint MC precision protocol — approved 2026-10-18

本轮用户“批准执行”2026-10-16 next_stage_plan.md 的R4→32提案；绑定原提案hash于approval.json。起点9196a61；原协议/112条结果/14个point_id与packet_id/8个开发world不变，原strictR4 failed及R4-S1 inconclusive不改判。

- 只新增replicate4–31，两分支，共14×28×2=784条continuations；0–3原结果只读合并。固定R4/8/16/32全部报告，不根据结果加减R/点/world；2个空时隙保持空缺。
- 对旧94项indexed artifacts验SHA，旧原生核心与5项v1运行源码验hash；Python、lock、所有实际依赖版本须匹配。仅读取可信本机自产pickle，先验证同一bytes的SHA再反序列化；验证snapshot完整state、内部alias、cfg、tape、feature及一次原生单时隙回放。预检查曾因旧Windows反斜杠索引lookup失败，修正内存路径规范化后通过，原索引/数据未改，失败发生在任何新continuation前。
- 复用不修改的extensions.counterfactual与v1 branch，原GOSC scheduler/channel/Planner保持；相同当前发送尝试、ACK/队列/融合与5条future stream keys定义。旧112条不重跑，不重新采样或生成前缀。
- 2workers各1数值线程，新增批次wall900s硬上限；估计495s，仅为外推。错误/timeout保留partial并停止，不自动追加预算。每point独立append-only raw文件；输出新.local/reproduction子目录，拒绝旧目录/dirty源码/测试hash不符。
- features沿用原sender/shared白名单，与offline标签/receiver状态分离；只作离线条件解码效应，无训练/新估值器/API/LLM/GPU/安装/下载。
- 配对标签DeltaT=failure−success，点级先对R个差值平均，MCSE=std(paired differences,ddof1)/sqrt(R)；正/零/负配对分布与next-real-target变化每层级报告。两个分支future RNG起点、当前尝试cost与非干预packet须一致；不完整的R层级只列missing，不对完整子集推断。
- 每层级复用v1的mission等权均值与cluster bootstrap4000/seed0、average-tie rho；bootstrap重复抽样重数保留，未定义数量保留。R4统计必须与旧统计精确一致。仍只有8个mission clusters，累计层级互相依赖，不能当独立重复确认；没有多重比较校正的确认性声明，未另传播finite-MC噪声。
- 描述性收敛量：每点R4/8/16/32的mean/MCSE、R32−R4漂移、符号变化、四层级同非零号、MCSE比值（R4为0时undefined），以及全部点曲线。它们不构成正式符号检验或好坏包训练标签，不事后筛样本。
- 输出不可变manifest/source/config/旧数据/approval/gate hashes，逐branch全结果/轨迹/成本/RNG/目标，合并统计与全56个point×R单元的CSV及图。成本沿用native UL/DL模型；真实wire bytes、额外ACK/CRC/PHY/sync仍not_modeled，禁止改称部署增益。
- 新源码/gate先提交，完整测试真实通过后执行；运行后读原始结果生成报告和证据索引，保持旧原始hash不变。本轮完成即停止；增加world、改变任务、开发模型或更高R均另审。
