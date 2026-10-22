# 开放问题与下一行动（2026-10-20）

| 问题 | 检验方法 | 预期反例/否定 | 下一行动 |
|---|---|---|---|
| 历史C差异从何而来？ | 现有输出覆盖/配置/trace＋版本受控诊断 | 两版本均不恢复历史，单一原因不足 | 保留当前环境独立结果与未知；原顺序继续，不强行拟合历史 |
| 新receiver摘要是否比现有common belief/intent多信息？ | 同容量M0/M1、去摘要/shuffle/oracle headroom | 全状态oracle也无收益，或shuffle同样好 | P1后先冻结feature ledger和低成本pilot，未运行 |
| 克隆反事实是否可比？ | event-index外生随机数、状态/事件hash、跨mission split | 相同seed但分支随机消费错位 | 先写协议/校验，标签采集未开始 |
| 更好value预测是否改变阈值/任务？ | threshold错误、mission paired质量和成本前沿 | MSE下降但任务没变 | M0优先，复杂训练No-Go直到headroom证据 |
| 同步更新应多频繁？ | 全bit/control/latency计费的age/loss/刷新网格 | 频繁开销和过期错误抹平增益 | 在独立calib中冻结协议与预算，未运行 |
| 跨模型/任务是否成立？ | 同任务真实LLM与后续独立迁移协议 | 只有更强LLM/更多tokens有效 | 完成原cached/live，不能用smoke代替；新任务另立协议 |
| 创新是否超出D02/BANDMAS/ToM2C/iCoTASC？ | 近邻机制/信息权限/可执行代码审查 | 只落实现有建议或不胜简单对照 | 当前不宣称首次或SOTA；继续定向文献与代码核验 |

独立1000–1079上游材料缺口不再向用户重复索要；依据用户给出的唯一源仓库如实登记。参见[RQ](../ideas/RQ_v1.md)和[拒稿自查](../ideas/reviewer_objections.md)。

## 历史差异调查补充（2026-10-20）

[CODE]/[RUN] [调查报告](../reports/upstream_gap_investigation_2026-10-20.md) 已收敛公开查询：第243次调度处存在1 ULP敏感选择，旧分支与当前HPC证据相互支持；仍不能解释作者全部逐seed差异。原校准选参过程在已查公开材料中未恢复，固定frontier/where路径不读取校准产物，两项缺口分别保留。旧统计100/104 equivalent、4 inconclusive，整体仍为Pending/NoGo，不能冒作本轮验收。

当前冻结HPC队列继续，本轮只做静态取证与恢复本地回传；新增报告尚未上行，待当前运行结束后按正常manifest同步。

## 2026-10-22总审计更新

[RUN] [结案报告](../reports/final_reproduction_audit_2026-10-22.md)：作者cache在390个含LLM任务中不覆盖当前首prompt；15个受限排序/已有NumPy变体未恢复。新live cache可重现570/570预设字段。412条历史差异含22条Planner/bits，不能全部归因模型随机性。P1精确一致性与原校准缺口继续单列，创新/训练仍未开始。

[RUN] 补齐了两张被原最终重绘跳过的LLM表，完整产物为17PDF/18TeX。修正旧零共同key成功标签，v2覆盖审计识别.gz参考。没有覆盖旧失败或原作者数据。
