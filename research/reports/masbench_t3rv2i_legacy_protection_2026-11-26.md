# T3-R-v2-I 冻结源码与旧行为实际核查

2026-11-26，Asia/Shanghai；base458a96f59b620a02e6872d038b87912eb39e92e4。

[RUN] 本地39项冻结文件raw SHA保持；HPC独立审计39项LF SHA全部匹配，范围为原应用/client/evaluation/wire/Ledger/fixture/live driver、GOSC、旧测试、管理器、registry与四份静态文档。registry只hash、不解析；D1未改、无新题/正文/gold读取。新协议只在`fair_final_v2*`独立命名入口，没有更改base/protocol默认行为或旧评分。

[RUN] 旧synthetic adapter在新run `hpc-t3rv2i-legacy-20261126` **67 passed**（新执行，不借用旧结果）；新版专用文件另含1项旧语义桥接。stdout/JUnit及冻结reference源码验证支持所测语义，不证明所有旧程序路径普遍等价。

[RUN/管理] HPC原HEAD/index/refs/status备份后，仅metadata快进至458a96f，1320个原工作文件SHA无差异；没有reset/checkout/clean或新Git提交。标准源码同步逐项SHA通过，旧运行数据通道不被上行覆盖。原T3 identity仍b05ea73+20261125T034132Z及旧授权，未回填新base。

新登记适配器仅在新manifest声明排除HPC-owned运行通道的源码diff，原hpc_runs.py和sync_hpc.py字节未改；原完整运行记录仍在数据通道和回传。个人quota管理只处理本轮生成的重复/临时记录，原始文件经SHA验证无损归档，原manifest/artifact index、失败状态和旧684原件不改。管理与归档receipt见任务目录。

T3/G1/GP-ID科学No-Go保持。真实服务配置、Ollama、模型缓存、算法训练、T4、正式校准/封存test未触及。当前没有本地tracked diff，既有三项用户untracked保留；没有提交或推送。

结论：**原冻结源码保护与所测旧synthetic行为Go；真实部署与科研能力不由此放行。**
