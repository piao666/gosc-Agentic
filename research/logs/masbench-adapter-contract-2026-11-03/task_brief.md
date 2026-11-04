# Research Task Brief — 2026-11-03

- 问题：完整数据是否满足身份/schema/私有证据边界；独立消息适配能否在固定响应下保持MASBench原生行为并排除通信旁路？
- 授权：用户批准“数据核验＋最小无模型适配实施与HPC合同验收”。不调用LLM，不运行真实题目、不训练/扩样本/提交Git。
- 前人成果：[CODE] GOSC014b85d与冻结扩展；MASBench c0301a6；已有静态规格、独立环境就绪。G1/GP-ID科学No-Go保留。
- 修改：新增extensions/masbench_reasoning/、tests_ext/test_masbench_reasoning_adapter.py、scripts/masbench_reasoning_contract.py及研究文档；不改GOSC核心或原实验。
- 验证：HPC登记下载固定版本公开Reasoning数据和必要源码，完整blob/SHA/schema/分区/重复审计；仅合成固定响应对原源码做identity与权限/失败/账本合同。
- 资源上限：一次数据/源码下载≤16MiB、请求超时30s/文件；审计≤120s；每次合同≤120s；并行1、内存≤2GiB目标、无GPU、总新研究产物≤32MiB（runner源码快照另列）。失败不删除。
- 反例：共享证据/重复ID/答案在私有上下文出现不等于泄漏；全局板可绕过丢包；无通信禁答造成假收益；瞬时stub等价不能代替无线合同。
- 验收：数据身份与实际计数/异常可追溯；safe view不含gold/peer/raw/level；固定响应逐request/memory/board/parser/stop/legacy相等；真实UTF8/帧/ACK/重试/截止/幂等及全启动分母通过。支持域之外显式Pending。
- 下一阶段：本轮结束停止。真实模型能力、LLM调用预算、科学收益、正式实验均需另行决定。
