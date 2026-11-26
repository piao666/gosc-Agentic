# 真实部署及续办日志

2026-11-26 Asia/Shanghai。用户明确要求完成真实部署/真实模型验证，另通过call_66ce45b43aab4601b7ff10059e9794cf接受监测停止合同。只授权两份冻结人工输入；不读原四题/剩余池/gold，不训练、不T4、不提交push。

## 实现、同步与新合同

本地实际Get-Content/rg读取AGENTS、说明书、既有v2/I/部署/存储材料与client/ledger/live/lifecycle/runner；Git status/HEAD/remote/diff只读，保留旧未提交成果。新增独立live/RPC/ledger、六slot入口、launcher/spawner、测试及独立审计，不改旧默认或冻结Prompt。

首sync以目录名.workbuddy作排除被工具在传输前拒绝；改精确未跟踪路径.workbuddy/memory/2026-11-25.md并排除两份用户任务文档，未读其内容。各成功SHA同步ID按run_index保存，失败命令不冒充run。远端无rg时管理查询改现有grep，未安装依赖。一次本地CIM进程诊断不可访问，未取得进程信息、不借此主张成功；只读检查未修改系统。

新contract首轮29过/1失败，原因是对实测CPU纳秒数要求相等；纠正为保留CPU实测值、比较其余wire和全部请求/历史/终答。第二轮31通过。真实启动前识别服务会继承driver AS2GiB的风险，新增受控服务spawner（服务树单独计量）和纯Python继承合同；工程第三登记32通过，累计6.196603s。原首轮失败、第二轮通过与修订前源码全部保留，不称单次32+31+29独立问题数。

## 实际真实run

唯一run hpc-t3rv2i-live-probe-20261126。首次CLI --kind acceptance不在runner枚举内，参数解析拒绝、无run和请求；改支持的infrastructure后才创建同一run。真实108.091165s，生成2/helper2/render2/unload2/start2/stop2；用户预算未增第3次真实请求。

实际调用用source20261126T032819Z、授权LF SHA8ee5cdd329bf8a73ffe7b9dd9bdb713e7e236e01d1849c240b9083e4a7a36fcd。19材料SHA与最终32合同回执绑定。Windows原字节与HPC规范化LF授权SHA不同，执行身份以HPC为准。

请求625/14与8720/14 tokens，输入总9345、输出28，输出永久预留1024不退款。长输入原文`Alice: MESSAGE <Q>Is the parcel blue?</Q>`缺规定换行，invalid_exchange，不修复、不重跑、不因服务成功而改为合法。两次模型请求仅t0，未实测六slot真实双方final。

1151账本事件、962资源采样，driver/service/GPU峰106934272/5251112960/6767509504B，最大活跃采样间隔0.237718061s；监测不是硬隔离。原runner两次退出、1024空闲回滚、marker清空，当前GPU0。

## 自动审批阻断及明确事后复核

原独立审计启动工具返回Automatic approval review failed: usage limit；明确说明是审批服务无法完成审查，不是动作被判不安全。命令未执行、原audit run目录未创建；没有绕过审批。用户随后明确“继续完成真实验收”。

续办SSH只读确认原run完成且原audit未登记；核得距原开始11905.539650s，已经超过原连续2000s。原账本/授权/deadline未重置；新增事后续办登记和显式--post-deadline-review模式，旧严格模式保留。

源码同步20261126T064855Z后，新登记hpc-t3rv2i-live-postaudit-20261126在0.500649s完成，独立审计不导入生产parser/scorer。审计passed仅指证据复核，original_continuous_2000s_closeout_met=false；不是事后抹掉超期。无额外LLM/counter/HTTP/服务切换。

## 回传、保护与停止

本地执行collect_evidence.py仅对本轮5个run定向取回受控镜像，HDD43原件及三套fixture常规文件全部SHA验证；458文件/7763327B，双端receipt20261126-t3rv2-live-d81f79a776.json。pytest便利symlink排除并列名；原常规数据完整保留。本地只做编辑/回传/轻量SHA/JSON管理，不跑测试或研究统计。

前序81交付原字节SHA、19执行材料LF SHA一致；模型run source和事后audit source区分。HPC原始结果、registry和旧T3身份/科学No-Go不动。结束时个人SSD余88031232B，后续大原件仍HDD。

完成最终报告、D矩阵、原件镜像、小型逐字节汇总、来源清单和有界T3条件申请后停止。结论：合成真实执行/证据闭环通过，长输入格式负例和按时交付不合规保留；完整任务能力/消息价值/无线净收益未建立，T4不进入。当前probe profile不能直接执行48任务生成；未来独立任务profile/授权/新准入仍须明确审阅。未提交推送。
