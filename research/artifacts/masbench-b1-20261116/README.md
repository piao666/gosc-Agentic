# MASBench B1小型证据白名单

2026-11-16归档，6份JSON逐字节复制原HPC outputs，SHA/原路径/run ID见[provenance](provenance.json)。原outputs、源码快照和失败记录继续在HPC/本地保留，不通过force-add改变忽略边界。

[回传摘要索引](receipt_index.json)保存7份完整receipt的原路径/大小/SHA、mirror标志及本轮B1文件条目；反复列出全历史的原始清单继续留在本地/HPC，不新增入Git。失败回执034339Z-eaef8e仍标明quota上行失败，恢复以034520Z-f62d10为准。

| 文件 | 含义 |
|---|---|
| deployment_data_preflight.json | 11月10日部署metadata/默认context与既有registry的只读汇总，无生成/新任务成绩 |
| safety_17_contract.json | 17项独立保护原型合同，不是正式Driver/模型验收 |
| integration_20_contract.json | 第一版20合同历史证据 |
| integration_22_contract.json | Prompt绑定/共同截止补验后的22合同 |
| integration_23_contract.json | 外层→实际fixture Driver中断链补验后的23合同 |
| integration_24_contract.json | 最终24合同，测试通过；其后quota管理失败单列保留 |

20/22/23/24不相加成一次总测试数或独立任务样本，17亦不与旧147+5混作本轮重跑。真实Reasoning任务/模型生成仍为0；G1/GP-ID科学No-Go保持，实际tokenizer/context与服务取消仍Pending。工程证据不支持任务收益或可发表性结论。
