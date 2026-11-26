# Research Task Brief — T3-R-v2真实部署及合成模型验证

2026-11-26 Asia/Shanghai。用户要求“完成真实部署和真实模型验证”，并明确答复“接受该监测停止合同，继续有界合成真实验证”。

- **问题**：[HYPOTHESIS] 新版独立真实入口能否在固定身份/完整输入/render/usage、持久预算、清理退出/1024回滚与完整回传下完成两个人工服务请求？不是四题能力/内容价值/无线净收益。
- **授权**：独立实现和必要无模型合同；固定Ollama0.11.11/qwen2.5:7b，临时16384并恢复1024；最多2合成生成、各512输出、每请求准备150s/生成180s/清理40s，无重试/替代/失败后再生成。原System模板、人工短/长输入资产SHA保持，不读原四题/剩余52条/registry正文/gold。
- **资源合同明确修订**：用户已通过call_66ce45b43aab4601b7ff10059e9794cf批准driver/helper各AS2GiB、driver树2GiB/service树及GPU16GiB监测停止，检查间隔<=0.5s；非硬隔离，不保证瞬时无过冲，容器24GiB总硬限照旧。记录真实间隔及采样失败，不伪称硬限通过。
- **真实阶段冻结上限**：2generation+2render+8普通GET+14cleanup_GET+2unload+128lifecycle_GET=156 HTTP，counter2，start/stop各2。输入永久预留31744、输出1024；本阶段墙钟总2000s（准备300/生成360/清理80/生命周期含权重SHA600/应用120/审计120/完整回传300/失败余量120），失败前缀不退款、不重跑。阶段开始后单调deadline不可重置。
- **工程阶段上限**：最多2次合同登记，每次120s；1次独立审计<=120s，worker1/CPU<=2、普通测试AS256MiB；所有人造fixture临时树HDD，总新增HDD<=32MiB/SSD<=16MiB。历史C01–C32支持域保留但不冒充新版D01–D12结果。
- **真实存储**：新HDD独立run目录<=128MiB，含服务log16MiB/control8MiB/应急1MiB；SSD登记/索引<=32MiB；完整定向回传<=160MiB。进入真实阶段前SSD个人余>=64MiB/HDD>=256MiB。模型/helper只引用现有，不下载、不安装、不复制权重到SSD。
- **修改文件**：仅新增独立live适配器、受控worker/launcher、六slot独立入口、合同/审计/授权和本目录记录。原base/protocol/v2-I模块、旧授权/runner/服务脚本、历史结果及科学No-Go不改。
- **设计/验收**：新授权与源/plan/asset/receipt严格SHA绑定；单例service lease；所有请求/metadata/生命周期尝试调用前fsync扣账；精确计数与服务render/ps16384和usage一致；源/runner PID+stamp/模型map校验；未知usage永久保留；IPC/超时/资源/存储/回传故障停止；一次清理、退出证据、1024空闲基线和lease清空。独立审计不导入生产parser/scorer。
- **反证/停止**：身份漂移、计数/usage不符、quota不足、未知runner、清理/回滚不明、超预算或独立审计失败均No-Go，保留原始记录。两次生成额度一旦派发不得靠修复再发。无真实能力/训练/T4/校准/封存test/Git提交推送。
