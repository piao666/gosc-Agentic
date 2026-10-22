# 必须保留的负证据（2026-10-20）

- [PAPER] D02 p.5 III-A/B：receiver上下文失真、匹配提供/撤回/延迟interaction credit已经存在，否定“概念首次”。
- [PAPER] A02 Eq.6、Sec.IV-C/D与D08 Sec.3.3：反事实式监督、metadata低成本估值、对方目标建模已有先例；B10 Alg1/2已有offline-online查表。
- [PAPER] GOSC p.8–9：ToM对bits/AoI的多数CI跨0、15比较只有1个未校正阳性；反事实下一目标变化少，真值排序弱；exact joint并非普遍更好。高精度估值未必有净收益。
- [RUN] resume-c-analysis-20261020：W100/10000uses，bits相对ToM完成时间差1.8869slots，95%区间[-5.0367,8.4565]；仍不能证明ToM优势或等价。数值来自HPC原函数的paired bootstrap输出，不是本地重新计算。
- [PAPER] A03 p.11 TableIII：10dB Im的SR82低于LC+SC94，Complete仍均yes；KB改善质量也增加通信。复杂模块/LLM自评不保证真实任务成功。
- [PAPER] B10 p.6 TableI：CIFAR10 RB32 ours0.870低于CVX baseline1 0.885，不能写全工作点最好；±定义/N未充分核验，不能擅作显著性。
- [PAPER] B01 p.8：AWGN高SNR传统Brotli+Turbo可优于DeepSC；A01端到端LoRA与固定模型baseline不能用来单独归因调度收益。
- [RUN] C-frontier/where与历史结果有479/364条差异；36诊断mission确定当前重复性和部分浮点分支敏感，但未恢复所有历史值。旧结果不改、不能统一写“复验通过”。
- [RUN] NumPy诊断首次PyPI下载超时失败已留档；官方环境未降级。原独立校准脚本缺失，不拿公开选参顶替。
- [HYPOTHESIS] 任何新方法若只在免费oracle/额外LLM calls或挑选seed后有效，应作为失败结果保留；不通过新增模块和删点来修补主张。
