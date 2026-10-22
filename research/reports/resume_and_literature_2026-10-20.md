# Research Task Report — 顺序续跑与文献/RQ（2026-10-20）

这是后续长队列启动前的证据快照；动态进度读取research/sync/runs/hpc-ordered-resume-20261020/outputs/pipeline_status.json与各子run/status.json。执行完成与本地回传完成分看status/receipts。该报告不把未来排队阶段写成完成。

## Research Question / Hypothesis

[HYPOTHESIS] 修复历史比较覆盖与失败入口后，能否在不改原算法/数据、保留原预算与差异的条件下恢复复验？文献上检验“有限可观测receiver摘要在完整同步/估值成本下，能否超出已有强简单估值器”，不预设创新或收益。

## 已核验前人工作与阅读成果

[PAPER] 启动必读C02/B01/B04/A03/A01/A02/D03/D02/D01/D04已形成笔记，另有D08/D10/B10，共13篇。每篇附页码/式/图/表、SHA、五句话记忆卡与相邻比较；两篇长综述等为明确范围的重点阅读，不冒称42篇全部全文精读。私人PDF/提取全文/渲染仅在本地.local目录，未上传HPC或公网，原Obsidian不改。

交付：research/literature/reading_review_2026-10-20.md、reading_manifest_2026-10-20.json、reading_notes/，以及Research-Gap-Matrix.md、Formulation-Library.md、Baseline-Library.md、Negative-Evidence.md、Open-Questions.md；research/ideas/RQ_v1.md和reviewer_objections.md。

最直接先例是D02 Sec.III-A/B的匹配交互credit及receiver-context distortion，A02 RCE/metadata/adaptive prices、D08删消息KL与B10离线lookup也已有。不能以接收者感知、反事实或offline-online命名宣称创新。原GOSC bits/AoI及joint/反事实负证据写入拒稿门槛。三项RQ分别考察额外信息、净成本区间与机制/泛化边界，新方法没有实现/训练。

## 实际源码与变更

[CODE] HEAD876fc523b113b3b65e19f0b730f1573ccc2ee17f，上游387b493。读过原experiments/run_belief_divergence.py、run_revision.py、run_realistic.py、validate_realistic.py、diagnose_value.py及gosc/llm_agent.py；保护目录gosc/experiments/tests/results/LICENSE不修改。

外层新增repro_compare.py显式schema/唯一性/缺identity/coverage；0共同键或0科学指标标未比较。repro_differences.py受控诊断；repro_resume.py核验隔离workspace/原产物/失败/原72h，跳过已完成阶段，新ID续跑。repro_fresh_plan.py在完成grid后冻结原规则选出的实际fresh配置/seed目录并与native pool计划对照。repro_llm_transport.py只观测原HTTP、重试tokens/时间/格式错误，不改变prompt/options/retry，无新模型下载。

## 实际运行与结果

- [RUN] hpc-compare-tests-20261020：16passed/2.93s；hpc-resume-tests-20261020：20passed/3.06s；hpc-resume-final-tests-20261020：24passed，证据各run stdout/status。最终hpc-resume-freeze-tests-20261020完成25passed/3.12s（精确pytest时间以stdout为准），含fresh config/seed目录保护，全部回传。
- [RUN] hpc-difference-probe-20261020：24条诊断mission，六个预先选定案例×repeat1/repeat2/scalar-exp/no-SIMD，约12.36s。全部重复当前输出稳定，非SIMD变量没有改变这6例。
- [RUN] hpc-numpy-diagnosis-relay-20261020：12条（6例×1.26.4/2.2.6）约7.90s，依赖隔离，official NumPy2.4.6不变。1.26.4改变两例但不匹配作者；2.2.6六例同当前。首次联网下载hpc-numpy-diagnosis-20261020超时失败留档；官方wheel经PyPI SHA与两端核验后离线安装，非在本地运行科学测试。
- [RUN] 新coverage audit确认Genie300条全部共同匹配；selection导出rescue3300共同键/18条差异/部分覆盖，另有完整catalog26100比较的22条差异，不能相加当独立统计。
- [RUN] trace对照显示scalar-exp在两案例、NumPy1.26.4在另两案例的相同候选结构下改变选择；重复/no-SIMD/2.2.6没有这些选择变化。scalar-exp一个where-AoI案例恢复作者指标，不能推出全部479/364差异根因已解决。完整trace与首次分歧见hpc-c-resume-20261020/outputs/trace_divergence.json。
- [RUN] resume-c-belief-20261020：1400/1400 jobs，156.63s，max workers2；1400共同键、无重复/缺失、0指标差异，protected inputs unchanged。
- [RUN] resume-c-analysis-20261020：原matched函数10000 bootstrap，117.86s。W100/10000uses bits–ToM完成时间差1.8869slots，95%CI[-5.0367,8.4565]；不能证明ToM优势或等价。保留null不可达预算、有效bootstrap数和15-family Bonferroni。完整matched_statistics.json。
- [RUN] 父hpc-c-resume-20261020完成280.17s，跳过旧4阶段、保留旧失败；receipt20261020T031651Z-d86285.json all_outputs_mirrored=true。上述分析在HPC，未在本地做统计。

## 失败/负证据与边界

C-frontier6800/C-where5000虽执行完成，479/364条历史记录仍不一致，其中完成时间228/146条；部分浮点分支敏感不能等同纯舍入无影响，不能挑NumPy版本强行通过。原calibration1000–1079材料缺失，公开0–99选参不是替代。A1/selected-fresh重复3000–3099不增独立N。完整cached/live仍未运行；服务smoke不代表科学阶段成功。

## 后续已授权的执行

HPC继续noise23400→overhead82600→shared18400，共124400候选；fresh3000–3099只跑原规则可行点，上限10300，精确目录在fresh启动前冻结/核验。再main/revision-rest/joint/scheduler/theory/value-fidelity/fidelity-analysis→cached/live→38候选敏感性/fresh→Genie fresh600→final replot。原全局截止2026-10-22T10:36:15.888633Z（北京时间18:36:15），不重置72h。每阶段独立cap保留，science workers2、数值线程1、RAM24GiB；CPU-only阶段不人为占GPU，live才调用既有3模型。

本地只编辑/读论文/镜像完成输出；后台镜像在.local/resume-follow记录运行状态和回执，运行中输出不假称已完整同步。源码/研究资产在长队列前同步冻结，后续动态内容走run channel。

## Go / No-Go

原可执行复验续跑Go；文献/RQ资产完成可供审阅；创新成立Pending，新方法实现与训练No-Go，等P1边界审计、可观测特征/共同随机流/全成本合同和M0 headroom。无付费API、投稿、push或新方法训练。本轮用户授权范围内不需重复批准。

主要命令：python scripts/hpc_runs.py launch --run-id hpc-c-resume-20261020 --kind simulation --stage ordered-c-resume --purpose ... -- {python} scripts/repro_resume.py resume --through c-analysis；完整命令及source snapshot在每个run manifest。正式全续跑入口为同工具登记hpc-ordered-resume-20261020，命令{python} scripts/repro_resume.py resume；实际是否启动、何阶段和退出码以run ledger为准。

## 最后启动前核验

[RUN] hpc-resume-evidence-20261020完成0.447s，六阶段完成前缀/全部已关闭产物哈希/隔离源码/无残留science worker/受保护Git路径不变/13篇笔记SHA检查均通过。C simple-value原函数汇总15个可用比较，未校正阳性1、Bonferroni阳性0；不是等价检验。receipt20261020T033248Z-b42f11.json完整回传。

续跑冻结清单research/protocols/ordered_resume_20261020.json。后续长队列是否启动及状态仅由run ledger确认，静态报告不回写未来结果。
