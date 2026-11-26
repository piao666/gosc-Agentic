# T3-R-v2-T 唯一一次开发诊断条件申请（未批准）

2026-11-26 Asia/Shanghai。审批对象：原四已曝光开发家族、Full/No-A2A共8episode、每episode固定6机会，**最多48次真实任务生成，新增合成生成0**。profile与无模型新增25项/独立审计通过只支持工程接线，不证明任务效果。当前真实开跑判定Blocked。

执行计划见`masbench_t3rv2t_plan_2026-11-26.json`，新授权见`masbench_t3rv2t_authorization_2026-11-26.json`（approved:false，run/baseline/view字段Pending）。旧probe授权cap2及固定输入限制保持，不能授权此任务。新阶段明确18360秒，不伪称原2000秒连续截止的续跑；父两次生成永久消耗，历史ledger SHA/失败状态已绑定。

申请上限48生成/440 HTTP/56 vocab-only helper（8初始+48逐slot）、761856输入预留/24576输出预留、qwen2.5:7b、16384窗口、每次512最大输出、串行2CPU/合计cgroup24GiB；driver/helper硬AS2GiB和已批准RSS/GPU监测停止语义；HDD1GiB/SSD新增32MiB及独立审计120s/完整回传600s。分项、反证和硬约束局限见[最终预算](masbench_t3rv2t_final_budget_admission_2026-11-26.md)。既有2人工probe不可退款、不再申请新合成生成。

批准前尚缺：合法四视图HDD bundle实际SHA及历史pair绑定；当前baseline PID/stamp与现场quota/空闲核查；新run/source规范化SHA及独立任务审计/回传/deadline流程具体化。之后仅在明确授权的新阶段最多8次初始无生成计数和48次逐slot计数内检验真实输入支持域；任何不适配立即Blocked，不裁剪/纠错/更换模型/选择新题/补请求。不能把人工700计数或旧15046压力例当成四题已通过。

无条件直接放行48次：**No-Go/Blocked**。可审阅有条件预算，不在本轮请求即时批准。若研究者接受这些前置条件，应另行明确批准具体run与预算，并保留已启动失败/未启动NA；一旦基础设施或信息边界失败，停止，不增加调用或重跑来完成计划。完整8×6工程、现场退出/回滚、独立审计、完整回传与截止全部通过后，再独立计算冻结探索性门；仍只属已曝光开发诊断。

不包含T4、封存测试、正式校准、训练、新算法/新题、模型替换、D1变更、历史No-Go撤销或Git提交推送。完成此申请及证据交付后停止，等待用户审阅。
