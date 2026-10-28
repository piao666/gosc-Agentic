# 新独立校准的结果前审阅记录

2026-10-27；人类用户已明确批准执行，限定新探索校准及其合同/完整预算/独立审计，不含正式test、训练或Git发布。

## 规格审阅（只读，无数值执行）

审阅者calibration_spec_review先指出须在结果前明确：ratio-of-means、共享bootstrap种子/线性分位、15端点双尾族区间、保守joint screen、合法horizon删失与软件失败、零/退化分布、预算按13个case逐一求最大再求和。上述项已写入设计/机器配置后复核，结论为固定13×12×400、原paid-pose主方法及无正式test/训练范围内无具体规格阻断。

## 代码质量复核（只读，无测试/SSH）

审阅者identifiability_review读取新runner、分析、独立审计及3个合同文件，确认源码/预算证明精确SHA绑定、完整gzip双哈希/行数、每case最坏world的2倍投影、实际存储上限、完整配对矩阵/删失/ratio-of-means与独立复算对应；未发现阻断。最终summary IO单列、投影不是保证等限制保留。

两个审阅者均未执行测试或统计，不能把这些意见冒称独立运行复现。真实HPC合同为hpc-information-calibration-contract-20261027：379 passed（pytest47.20s，runner47.533837s）；旧红run因新增模块尚未实现的导入失败完整保留。新预算/校准尚未运行时完成以上审阅。
