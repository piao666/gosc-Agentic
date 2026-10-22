# Research Task Report — exact paper/code/figure audit and R4 protocol

- **Research Question / Hypothesis**: 原论文编号公式/图表能否定位到源码、输入与已重建输出？实际候选族是否与论文口径相同？本轮不测试新算法。
- **已核验前人工作**: [PAPER] 本地D01 arXiv2609.39477v1，13页；已阅读原文§III–V、Appendix、图1–5与表I–XIII并定位5式和Algorithm1；SHA256 e99130b27965bc4b6c06ccca8fc2dd9a3fd8b2dd5f6880964b6e0a4003c01923。未推断最终发表状态，表I其余文献创新性尚未独立全文验证。
- **实际阅读源码**: [CODE] gosc agent/belief/channel/messages/voi/schemes/realistic/rescue/simulator/llm_agent，全部plot函数、run_belief_divergence、run_revision、validate_headline/realistic、analyze_theory/scheduler/fidelity/diagnose与相关tests。HEAD保持876fc52，原算法与结果不改。
- **本轮新增或修改**: 完整GOSC_paper_code_map、figure_table_audit、独立印刷参考值JSON、paper_audit.py/r4_preflight.py、R4协议与60mission计划JSON、任务证据、进度/README/AGENTS；更正说明书的Genie上界口径；管理入口R2追加已验证的原补表命令，未改原实验模块。
- **实际运行**: [RUN] 本地只读提取/渲染原13页和回传17图用于阅读；HPC hpc-paper-audit-20261019做405单元与25默认字段/6冻结点核验，并在隔离目录运行原 --table；HPC hpc-r4-preflight-20261019核对候选/seed元数据。没有新mission、校准搜索、训练或LLM调用。
- **测试与结果**: [RUN] 表IV–XII共9张，8原表匹配，VI缺5格；补齐后10行40格匹配。原图2/3/4/5分别对应fig_rescue/noise/snr_pair/shared_col，架构图1是静态语义图。原配置25项与冻结点6组匹配。已有R1 85/85不重复运行，因为原算法/测试未改；脚本/JSON结构与文件一致性作管理核验。
- **失败/负面证据**: TableVI仅三plot不能全表复现，需仓库已有table-only helper；Fig2第三轴minor tick标签重叠；实际搜索37候选、救援38；源码注释Proposition3是旧编号；原研究说明书把genie当上界已纠正。首次PowerShell读命令误用Bash花括号和PDF日志GBK输出错误均已纠正，未改原文与计算结果。
- **与原 GOSC 的差异**: 无新策略/算法；只补齐复现步骤与证据，保持原R2数据/图表不被重写。完整表VI作为补充run输出，不抹掉最初缺项。
- **公平性与泄露检查**: 印刷参考值独立抄自PDF，不由summary反推；核对均值/CI/†‡和目标未达条件。37候选严格轨与补38敏感性分轨；R4-A0预留9000–9009不参与调参，原1000–1079/0–99/3000–3099各保留语义；新的方法测试划分未执行。
- **成本**: 两个HPC审计run墙钟55.91s/2.16s；线程上限2，未运行GPU/模型、未收费。runner RSS含管理子进程，不当作算法基准。私有PDF/全文/阅读截图保留本地，不随项目同步。
- **可否进入下一阶段**: 本轮三项交付完成：纸码/全编号图表映射、印刷数据核对（显式差异）、R4协议。后续可按协议实现和执行60条A0 pilot；完整P1、多seed正式结果、R5真实LLM、P2问题审查仍未完成，不能启动或宣称新方法训练成果。
- **用户需要批准的下一步**: 本轮交付无需额外批准；不以协议自动发起完整campaign/训练。未向公网提交、未push Git。

## 验证与证据入口

精确命令、开始结束、退出码、Git/sync/资源见两run的manifest/status；每阶段原文件前后哈希见outputs/input_integrity.json；逐格原始差异和补齐复核见paper-audit输出；元数据明细见r4-preflight输出；回传完成以最新receipt为准。

R2管理入口现自动追加同一个 `experiments.run_belief_divergence --table`；补表实际执行已在本轮独立run验证，没有为此重复三份已通过的绘图计算，历史R2不能改称包含补表。
