# Fixed-checkpoint R32 evidence and reconstruction

本轮用户2026-10-18批准旧next_stage_plan.md；源码执行commit83338a3fa38d049f924c23bde788936990433afa。旧执行源码48404fd、报告9196a61保持。根AGENTS/研究说明/README/最近日志在启动时读取，初始working tree clean。

## Source and integrity evidence

|问题/材料|证据锚点|边界|
|---|---|---|
|具体授权与预定范围|approval.json; protocol.md; ../2026-10-16-cf-pilot/next_stage_plan.md|14固定点、rep4–31、784新branches、2workers/900s、0新world|
|Windows路径/编码修复|implementation_repairs.json; implementation_gate.json/v2.json|两次失败均在新continuation前；未删失败记录/修改旧数据|
|反序列化前验bytes哈希|experiments_ext/run_receiver_cf_precision.py:39–56|可信本机自产pickle；不接受未知文件|
|旧数据/源码/实际依赖/point身份核验|同文件:58–95；checkpoint_preflight_v2.json|旧94项indexed artifacts、16项实际依赖版本、原14点/packet|
|完整state/alias/config/tape/feature/原生slot回放|同文件:98–117|只有单时隙校验，不是新增完整任务/MC重复|
|新增784与全批时限|同文件:120–217|复用v1 branch，源码不变；新增目录/append-only/partial保留|
|旧新重复隔离及配对差值SE|experiments_ext/analyze_receiver_cf_precision.py:15–69|拒绝重复、变packet、复用0–3；不完整层级不对子集推断|
|累计4层级、mission-cluster统计、精确R4回归|同文件:72–149|R4/8/16/32层级相互依赖；仍8世界，bootstrap探索性|
|执行前测试|implementation_gate_v2.json; full-tests-v2.log|完整135通过65.81s，其中9项new contracts；不与旧134/targeted相加|
|后处理独立数值核验|experiments_ext/audit_receiver_cf_precision.py|raw重新构造56个point×R的mean/MCSE；独立标量cluster bootstrap复核12个mean/CI；非新仿真|
|原GOSC及前人工作|../2026-10-16-mechanism/prior_art.md; code_map.csv|沿用本地定向精读，不宣称本轮查新/出版核验|

以上源码路径均以`E:\gosc-agentic-teams`为根。新的完整branch数据位于`.local/reproduction/2026-10-18-cf-precision-v1/point-*/branches.jsonl`；旧112条及snapshot仅从`.local/reproduction/2026-10-16-cf-pilot-v1/`只读使用。未向外部服务上传原始研究数据/PDF/快照。

## Saved-data rebuild（复查指令，不冒充新增执行）

保留旧raw根路径/manifest/index，将新run复制到**没有analysis子目录的新本机目录**，保持所有source/data hashes。使用当前已冻结分析器：

```powershell
.\.venv\Scripts\python.exe -m experiments_ext.analyze_receiver_cf_precision --run-dir <new-raw-copy>
.\.venv\Scripts\python.exe -m experiments_ext.audit_receiver_cf_precision --run-dir <new-raw-copy>
```

分析器只读合并旧新raw，在新analysis目录生成statistics_by_R.json、per_point_by_R.csv、convergence.csv和PNG；独立审计生成independent_audit.json。统计保留所有正/零/负结果、未定义rho/有效bootstrap数；没有调参/训练/重新选样。若缺完整层级，该层级只列缺失，不自动填400或选择完整点作推断。

需要原始raw进行重建，hash索引本身不能替代数据；不必反序列化snapshot就能重算全部统计。重跑future continuations是新实验，需要单独授权/目录/manifest，不能覆盖当前数据。原strictR4复现失败和R4-S1 inconclusive不能被MC R=32的标签精度检查改判。
