# Context与真实部署归档小型证据

本次白名单为20份原始JSON、80,630bytes；每份复制前按原run的artifacts.json核验大小/SHA，字节不改，见[provenance](provenance.json)。包括失败build/preparation、成功构建、最终离线合同/合成输入计数/客户端边界和真实部署检查。不是完整数据集、模型或通用部署认证。

[15个run索引](run_index.json)记录4 completed/11 failed，包含2次主动SIGINT停止传输。配额导致未能收尾的一次prepare保留unknown结束/退出，后经授权补记failed，不编造耗时。

[精简回执索引](receipt_index.json)记录16份全量receipt的原路径、字节数、SHA与本轮run条目。原件共19,943,370bytes，继续保留本地/HPC；Git只归档该索引。旧回执的running快照仍表示当时状态，不被事后更正覆盖。

原outputs、所有source patch/tar/gzip、官方工具链及vendor payload、模型/环境仍忽略且保留原位置。源码参考和授权/失败元数据单独归档。文件ID仍用执行时的manifest Git/sync身份；不回填本次新提交SHA。

结论：同源离线候选通过；临时32768与2443-token长输入有限域部署检查/取消后卸载通过。原生即时idle、通用token IDs等价、生产Driver绑定仍未证实；默认服务恢复1024，无真实任务效果实验。
