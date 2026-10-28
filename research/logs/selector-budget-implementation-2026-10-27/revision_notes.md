# 验收过程修订登记

[RUN] `hpc-budget-selector-red-20261027`为实现前缺模块的预期红测试，退出2；`hpc-budget-selector-unit-20261027` 66通过/1失败：测试替身闭包捕获旧Group，第二次调用传了新目录，触发正确的成员身份拒绝。仅改替身按传入gs返回，不放宽生产验证。两run及日志保留。

[RUN] 第一完整合同481项通过；首个prepare冻结199目录（7违规+192可行），独立原gzip行/确定性采样核验通过，未运行重选或短fixture结果。

[CODE] 结果前边界复核发现：即使price/value/symbols均有限，`price*symbols`或`value-price*symbols`仍可溢出，旧selector可能将非有限效用当作空选择。新版加入显式有限算术域检查，异常报`SelectorFailure`，而非“空选择成功”。这属于规格要求的溢出失败行为；可行调用兼容声明限于数值运算有定义的输入，不承诺保留非有限中间效用下的旧空返回。原函数不改，未调整实际price/任务/样本。

新完整合同与新prepare须使用独立runID和源码SHA；旧freeze/通过记录保留当时状态，不用于修改后的实现验收。采样规则、原始输入/协议/预算和N0保持，最终sample gzip SHA必须与首版相同。独立绑定脚本是补充审计工具，不是冻结producer依赖；其HPC合同/source snapshot另存。未重跑原156任务。

[RUN] 最终完整485测试通过；六子阶段主验收37.690869s完成并独立核验。52短fixture未触发修复，故另补7个派生control-only服务合同，不扩N或重放任务。前两次补充run均因夹具绕过run/phase_decide却遗漏`_start()`（缺curve）退出1；第二次补合法驻留目标尚未解决缺curve。已读取native `_start`/run/phase_communicate，随后补其初始化，原生产selector/入口/服务未改，前两失败保留。派生合同的原时间/发送者映射到slot0/sender0且去掉EVID，必须明确它们不是原历史闭环精确重放。
