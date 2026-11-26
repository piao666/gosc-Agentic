# HDD复用任务日志

2026-11-26 Asia/Shanghai。用户对存储处理给出明确授权；不扩大为资源合同/服务切换/真实生成授权。新task_brief在执行前冻结文件管理白名单、顺序1worker/AS256MiB、300s/4GiB上限。

## 实际命令与读取

本地Get-Content/rg读取AGENTS、研究说明/README、前序部署brief/remediation/tasklog及HPC同步规则；git status/rev-parse/remote/diff/cached diff只读，保留所有旧untracked，不reset/checkout/clean。

HPC命令均通过`ssh -o BatchMode=yes -o ConnectTimeout=10 hpc`到固定项目根：

1. id/hostname/HEAD/.venv Python版本；原Lustre quota管理脚本；`du -x -B1 -s`仅五个项目管理目录。当前无资源/服务变化。
2. 查看sync_hpc.py:45–70确认同步备份语义；`find .local/git-checkpoints -maxdepth 2 -type f ...`及sync-backups批次目录名只读。没有读取/扫描其他用户项目、凭据或实验正文。
3. 新relocate_archives.py通过SSH stdin在HPC执行，退出0，12.237841524s；三类根合计634常规文件87764721B。先全部copy/fsync/SHA并落manifest，三个源根留下恢复索引，再逐件去除已保全源副本。目标HDD独立设备/current UID，硬AS256MiB/1CPU affinity。
4. `scp`定向取migration_plan/copy_verified/migration_receipt/removal_journal；独立verify_archive.py同样SSH stdin执行，退出0，0.221276321s，634大小/SHA/源副本去除与19项保护SHA全部一致。
5. 保存独立stdout，再scp原格式independent_readback.json；远端`sha256sum`仅5份管理凭证，逐项与本地原字节比较。无原始管理归档内容下载或公开提交。

没有启动任何hpc_runs测试/模型/服务调用；这是纯管理搬迁，不伪造成工程测试run。没有新增失败或删旧失败。原实验目录、模型/环境、源码、Git索引和registry保持原字节。

## 空间与实际边界

个人SSD余6594560B→93724672B→95662080B；最后91.23MiB通过现阶段32/64MiB容量门，仍未达到理想1GiB缓冲。HDD增加约88.62MiB配额占用，余约482GiB，低于4GiB上限。目录分配/延迟回收可使quota与逻辑字节不完全相等，不承诺持续剩余值。

后续按HDD布局策略为新大产物预留HDD，当前源码和小型metadata保留SSD；当前没有自动化清理/迁移常驻程序或原sync修改。再次归档必须新目标、明确新增范围、先核SHA；不重跑已完成的一次性迁移脚本。

本地只做文件编辑/JSON/SHA/回传管理。前序48项v2-I和14项部署审查交付按原manifest核SHA，全部保持；本轮报告/索引在新路径，不将旧Blocked状态改写为当时已通过。

## 下一项

存储阻断已解除，可继续原预算内独立live入口的无模型接入准备；当前尚无新live实现/新合同通过证据。GPU/RSS监测候选仍未批准，严格资源缺口、实际16384/render/usage/清理回滚保持Pending。未启动真实能力诊断/T4/校准/test/训练，不提交push。无需再次请求本次已获授权的存储搬迁。
