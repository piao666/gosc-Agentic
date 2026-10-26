# Research Task Brief — 2026-10-25 校准续接审计

- 科学问题：[HYPOTHESIS] 已冻结GP-v2的paid-pose净收益是否在同world/成本/功效关卡下成立？本轮只核对已完成校准和交付，不新增任务样本或调参。
- 授权：沿用用户对1200s、21候选×12world的明确批准；本轮用户“继续任务”要求恢复状态核验和成本前沿/消融审计。既有dirty来自上述授权的实现/报告/回传；保留、不reset/checkout/clean，不请求重复授权。
- 前序证据：[RUN] hpc-causal-independent-calibration-20261024在2026-10-24完成，252任务、12新world，447.369435s，exit0，原分析No-Go。上次续接因自动审批服务用量失败未完成后续读取/审计；这不是HPC仿真失败。该失败已在对话工具输出记录，不绕过审批。
- 科研边界：[CODE] HEAD47389eba9c6e2838139df3aa47863ab88634e97a；冻结方法/候选/price/CRN/world/config/停止规则不变。原480s门槛blocked和批准后1080/1200s修订均保留。既有190不同合同不冒充本轮重跑。
- 阅读：[PAPER] 沿用既有纸码映射/总说明书，未新增原文核验；[CODE] scripts/repro_causal_service.py、audit_causal_service.py、audit_causal_frontier.py及其frozen/approved_budget接口。
- 文件：审计脚本只补充独立检查/产物生成；新增续接报告/任务日志、更新README/状态入口。旧run、原results、缓存、旧报告不覆盖。
- 执行：先同步SHA不改实验源，再用hpc_runs.py登记两个独立分析run，每项<=120s，单worker/数值线程1、2CPU/24GiB配额内。只分析既有252数据，无新simulation/LLM/GPU/训练/正式test。
- 验收：252逐任务记录/逐事件账本、CPU/RTO/重播、world/候选/CRN、CI/N、选参/成本前沿/公平支持/No-Go条件独立复算；全部输出回传且receipt哈希通过；科学PNG可读；命令和失败如实留存。
- 反例/不确定性：同校准数据选参的探索性CI不是确认性显著性；均值更快但无联合成本支持不构成净收益。age可能更强但不能事后改主方法/追加样本；CPU固定服务假设与实测process成本分开。
- 停止：原分析No-Go只允许审计/报告，不运行正式test、扩N或训练。P1作者校准/cache链和历史数值差异仍单列。

## 验收结果（追加）

[RUN] 独立账本/CI/N审计6.652592s通过，950,281事件；前沿v1 3.226462s、措辞澄清v2 2.072158s均通过，数值字段一致。最终图2.101523s重绘并已目视，保持已审计数据点不变。252校准任务均完成，独立N12，实际447.369435s；No-Go，规划N21907超200且主比较联合成本支持缺失。正式test/扩N/训练均未执行。本地只做Git、JSON字段完整性/哈希核验和文档编辑，未运行项目测试或统计。

[RUN] 全部输出回传receipt为research/sync/receipts/20261025T133502Z-8fa9fc.json，all_outputs_mirrored=true。最终同步/交付SHA见同目录delivery.json。精确命令及source/config身份已保存actual_commands.json；本轮未Git提交/推送。无须再次批准已完成的预算。
