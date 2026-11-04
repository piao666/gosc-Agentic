# Research Task Brief — HPC工程合同检查

- 授权：用户明确“授权执行HPC合同检查”。仅工程合同/旧回归及必要故障修复、源码同步与证据回传；不执行Shadow runner prepare/run、不开展两world诊断/任务效用/扩N/训练/正式test、不提交推送。
- 问题：新局部G0/G1、真实入口身份/观察中性、同wire/预算/标量审计、授权/源身份/产物上限等合同能否通过，并保持旧实现回归。
- 基线：014b85dfc472c45d8ea5f15e83e0c1ed8e938daf；dirty均为本会话前序文档与新增独立实现，保留。已验收规格/审稿正文SHA保护；原gosc/native/GP-ID/BF不修改。
- 先决条件：只读SSH核验UID/host/路径、Python/依赖/2CPU与RAM配额、活动run和上一同步manifest。若远端仍为253a14b，先核对严格祖先与字节一致，备份index/patch后仅推进远端HEAD/index，不checkout/reset或覆盖工作文件，再正常SHA同步；不改远端URL或原结果。
- 执行：先新合同定向检查（240s上限、单worker/数值线程1），失败定位/保留并用新runID复测；通过后完整tests+tests_ext（240s上限）。必要针对失败补测/完整复测总计预期<12min，实际失败/成本按run记账；不扩到机制诊断。
- 成本：此前485全回归约50s，仅作历史成本参考，不当本轮保证。CPU-only，无LLM/GPU/安装/下载/收费API。工程fixture不计独立任务收益N；JUnit/日志与全部产物回传，默认100MiB下载上限如不足先核对原件体量。
- 反例/停止：越权/重复/目录或非EVID改动/观察不等/审计被篡改而放行均阻断下游，先定位新代码，不放宽既定合同掩盖失败。科学No-Go和Shadow执行授权false保持。
- 验收：完整实际HPC测试证据+源码/同步/资源/run manifest+回传receipt，失败保留；本轮输出工程结论与剩余缺口，不答复G1机制或任务收益问题。
