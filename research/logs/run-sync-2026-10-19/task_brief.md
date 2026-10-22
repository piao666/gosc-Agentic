# Research Task Brief - execution ledger and two-way output sync

- 用户请求：在 research/sync 持久化每次测试、训练、仿真的完成状态/内容输出，同步到 HPC；核验现有 uv Python 3.11；按阶段规划执行地点。
- [CODE] 当前 HEAD=876fc52，既有修改均来自本会话已授权盘点和 HPC 同步，保留全部内容。
- [RUN] 已核验 uv=0.11.19，管理的 Python=3.11.15；裸解释器缺 numpy/matplotlib/pytest；项目 .venv 不存在。
- 假设：独立源代码上行与 HPC 运行记录下行，可防止旧本地状态覆盖远端真实结果。
- 文件：research/sync 目录、HPC 运行登记/回传 helper、现有同步脚本的运行数据保护、AGENTS、路径与环境说明。
- 验证：所有代码验证在 HPC；执行短小 infrastructure 成功/预期失败记录，验证状态、日志、产物哈希和回传；不运行 GOSC pytest/仿真/训练、不装依赖。
- 成本：元数据/文件传输与秒级基础设施验证，无模型/GPU/收费 API。
- 反例：失败被误标完成、回传状态与运行状态混淆、本地旧记录覆盖远端、远端依赖缺失被误记为可运行。
- 验收：两端 sync 协议一致，真实可用 Python 路径有证据；成功与失败均留痕；输出按 SHA-256 回传；明确下一步计算在 HPC，文档维护在本地。
