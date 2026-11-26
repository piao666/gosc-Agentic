# 部署准入阻断修复申请（未批准）

2026-11-26 Asia/Shanghai。本申请只解除工程前置阻断，不授权模型生成、服务切换或T3能力诊断。

## 申请一：原样迁移明确的依赖下载缓存

当前SSD个人quota余6594560B。拟将下列三个**下载缓存**从`/home/u202520081000097/jupyterlab/Paper/gosc/.local/diagnostic-wheels/`原字节迁移到新目录`/hdd/u202520081000097/gosc-admin-archives/20261126-deployment-admission/diagnostic-wheels/`。不移动已安装的两个诊断环境、当前.venv、Go/helper、模型、结果、运行记录或Git对象。

| 文件 | bytes | SHA-256（本轮HPC只读核验） |
|---|---:|---|
| numpy-2.2.6-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | 16821570 | ba10f8411898fc418a521833e014a77d3ca01c15b0c6cdcce6a0d2897e6dbbdf |
| numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | 18252005 | 666dbfb6ec68962c033a450943ded891bed2d54e6755e35e5835d63f4f6931d5 |
| manifest.json | 864 | 72d15f398f7cc38f924154af96ab36ddd020b1589d4cfbdb2364b5538821dc74 |

合计35074439B；预计释放约33.45MiB逻辑文件空间，迁移后必须重新核实际quota，不保证Lustre计费立刻按逻辑大小减少。目的地必须独立HDD、当前UID、非symlink、新建不覆盖；先复制、逐件SHA读回并fsync、写双端manifest与回滚路径，再移除三个源副本；任一失败不删除源。HDD副本永久保留，不是销毁缓存；不重新安装或执行wheel。

此迁移改变旧下载缓存路径，因此依据AGENTS A.3/E/E1的现有文件保护与同步规则，**等待明确批准，不因缓存可再下载就擅自删除/迁移**。本轮已完成清单、大小与SHA，未移动。预算：120s管理墙钟、至多1CPU、普通Python AS256MiB、HDD新增<=64MiB、SSD应急receipt<=256KiB，无真实模型/服务/依赖安装。

迁移成功且SSD余>=32MiB，只解锁已冻结的16MiB无模型接入验收；不保证未来真实预检所需64MiB准入余量。不得因此继续删除其他目录。若仍不足则保留证据再申请具体清单或平台增加quota。

## 申请二：明确资源合同，禁止默许降级

默认严格路径要求独立driver/service内存树及GPU硬资源分配可核查；现场所查控制文件不可写，仅有容器总24GiB及GPU全设备34304MiB可见。当前没有driver2/service16/GPU16GiB的硬约束证据。

选项A：继续严格硬隔离，等待管理员提供可验的资源分配，保持真实执行Blocked。

选项B（未批准候选）：接受driver/helper逐进程AS2GiB、driver树2GiB/service树16GiB/GPU16GiB作为<=0.5s**观测停止阈值**，容器24GiB仍为整体硬限；去除子树双计。它不能保证采样间无过冲，不能写成硬隔离通过。越界、采样失败、异常服务身份即停派发，未知usage永久预留；仅自有安全清理，不增加请求重跑。

用户选择B只允许据此实现/无模型验证新的资源合同，不授权当场真实生成。未来两次纯合成部署预检仍要在新live入口、D01–D12、quota和rollback合同完成后，绑定具体源码/receipt/PID重新单独批准。[真实预检候选](masbench_t3rv2_deployment_probe_candidate_2026-11-26.json)现为approved:false；有界T3能力诊断申请尚未释放。

不能用增加模型规模、放宽D1、修改评分或历史No-Go解决这两个工程阻断。未完成部署前不进入T4。
