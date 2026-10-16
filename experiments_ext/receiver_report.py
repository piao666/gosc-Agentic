"""Export retained Receiver-D1 evidence without simulations or new hypothesis tests.

Run only after the frozen summarize diagnostic command. Refuses an existing
destination; original and completed statistical-reproduction files are read-only.
"""
import csv
import datetime as dt
import json
import math
from pathlib import Path
import shutil

from experiments_ext.campaign import diagnostic_jobs, config_key
from experiments_ext.reproduce import ROOT, BASE, save, sha, check_protected
from experiments_ext.statistical_reproduction import OLD


def finite_tree(obj):
    if isinstance(obj, dict):
        for value in obj.values(): finite_tree(value)
    elif isinstance(obj, list):
        for value in obj: finite_tree(value)
    elif isinstance(obj, (int, float)):
        if not math.isfinite(obj): raise ValueError('Non-finite retained value')


def ci(values):
    return f'[{values[0]:.2f}, {values[1]:.2f}]'


def export():
    run = ROOT / '.local/reproduction/2026-10-15-receiver-v1'
    source = run / 'diagnostic'
    target = ROOT / 'research/reproduction/2026-10-15-receiver'
    execution = json.loads((source / 'manifest.json').read_text())
    plan = json.loads((source / 'plan.json').read_text())
    stats = json.loads((source / 'statistics.json').read_text())
    rows = [json.loads(line) for line in (source / 'raw.jsonl').read_text().splitlines()]
    assert execution['status'] == 'passed' and len(rows) == execution['completed'] == 1200
    assert execution['raw_sha256'] == sha(source / 'raw.jsonl')
    assert plan['analysis_sha256'] == sha(ROOT / 'experiments_ext/summarize.py')
    assert plan['adapter_sha256'] == sha(ROOT / 'extensions/receiver_oracle.py')
    assert plan['admission']['scope'] == 'tom_path_diagnostic_only'
    finite_tree(rows)
    expected = {(j['setting'], j['mode'], j['seed']): j for j in diagnostic_jobs()}
    retained = {(r['setting'], r['mode'], r['seed']): r for r in rows}
    assert len(retained) == 1200 and retained.keys() == expected.keys()
    for key, row in retained.items():
        assert row['status'] == 'completed' and row['scheme'] == 'gosc'
        assert row['config_key'] == config_key(expected[key]['cfg'])
        assert len(row['output']['curve']) == expected[key]['cfg'].max_steps
    protected = check_protected(OLD)
    baseline = ROOT / '.local/reproduction/2026-10-15-statistical-v1'
    closure = json.loads((baseline / 'closure.json').read_text())
    assert sha(baseline / 'r4-statistical/gate.json') == closure['compact_artifacts']['gate.json']
    assert sha(baseline / 'r4-statistical/raw.jsonl') == '0bd0433ef40db011aa64a972e9165298092af3e1bfb885f902ec7dc56cb53780'
    target.mkdir(exist_ok=False)
    for name in ('statistics.json', 'contrasts.csv', 'time_contrasts.png', 'time_contrasts.pdf',
                 'time_and_resources.png', 'time_and_resources.pdf', 'configs.json'):
        shutil.copyfile(source / name, target / name)
    for src, name in ((source/'manifest.json', 'execution_manifest.json'),
                      (source/'plan.json', 'plan.json'),
                      (run/'approval.json', 'approval.json'),
                      (run/'preanalysis_audit.json', 'preanalysis_audit.json')):
        shutil.copyfile(src, target/name)
    # Retain all seed-level scalar outcomes, including harms and false declarations.
    scalar_keys = sorted(k for k, v in rows[0]['output'].items() if not isinstance(v, (list, dict)))
    with (target/'per_seed_outcomes.csv').open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['setting', 'mode', 'seed', 'config_key', 'elapsed_seconds', *scalar_keys])
        writer.writeheader()
        for key in sorted(retained):
            r = retained[key]
            writer.writerow({**{k:r[k] for k in ('setting','mode','seed','config_key','elapsed_seconds')},
                             **{k:r['output'].get(k) for k in scalar_keys}})
    primary, secondary, means, resources = [], [], [], []
    for setting, group in stats['settings'].items():
        for mode, metrics in group['modes'].items():
            time = metrics['completion_time']
            half = time['mean_ci_normal95']
            means.append(f"| {setting} | {mode} | 100 | {time['mean']:.2f} | "
                         f"{ci([time['mean']-half,time['mean']+half])} | "
                         f"{time['q25']:.2f}/{time['median']:.2f}/{time['q75']:.2f} | "
                         f"{metrics['symbols']['mean']:.2f} | {metrics['dl_symbols']['mean']:.2f} | "
                         f"{metrics['bits']['mean']:.2f} | {metrics['false_declarations']['mean']:.2f} |")
        for mode, contrast in group['contrasts'].items():
            t = contrast['time_shared_minus_mode']
            signs = f"{t['positive_seeds']}/{t['negative_seeds']}/{t['zero_seeds']}"
            line = (f"| {setting} | {mode} | {t['mean']:+.2f} | {t['relative_improvement_pct']:+.2f}% | "
                    f"{ci(t['ci95'])} | {ci(t['family_ci'])} | {t['practical_threshold_slots']:.3f} | {signs} |")
            (primary if mode in ('private','position') else secondary).append(line)
            ul, total = contrast['ul_mode_minus_shared'], contrast['total_recorded_uses_mode_minus_shared']
            resources.append(f"| {setting} | {mode} | {ul['mean']:+.2f} {ci(ul['ci95'])} | "
                             f"{total['mean']:+.2f} {ci(total['ci95'])} |")
    interaction = '\n'.join(f"- [RUN] {s}: {g['interaction_joint_gain_minus_single_gains']['mean']:+.2f} slots, "
                              f"95% CI {ci(g['interaction_joint_gain_minus_single_gains']['ci95'])}."
                              for s,g in stats['settings'].items())
    primary_effects = [g['contrasts'][m]['time_shared_minus_mode']
                       for g in stats['settings'].values() for m in ('private','position')]
    decisions = dict(primary_comparisons=6,
        point_gain_at_least_5pct=sum(t['relative_improvement_pct']>=5 for t in primary_effects),
        family_lower_above_zero=sum(t['family_ci'][0]>0 for t in primary_effects),
        family_lower_above_5pct=sum(t['family_ci'][0]>t['practical_threshold_slots'] for t in primary_effects),
        family_upper_below_5pct=sum(t['family_ci'][1]<t['practical_threshold_slots'] for t in primary_effects),
        stable_practical_single_factor_established=False,
        conclusion='No stable practical effect established; no equivalence or absence-of-effect proof.')
    assert decisions['family_lower_above_zero'] == decisions['family_lower_above_5pct'] == 0
    assert decisions['point_gain_at_least_5pct'] == 1 and decisions['family_upper_below_5pct'] == 0
    save(target/'decision_summary.json', decisions)
    commands = [
        ['.venv/Scripts/python.exe','-B','-X','utf8','-m','pytest','-q',
         'tests_ext/test_receiver_statistical_gate.py','tests_ext/test_receiver_oracle.py'],
        ['.venv/Scripts/python.exe','-B','-X','utf8','-m','pytest','-q','tests','tests_ext'],
        ['.venv/Scripts/python.exe','-B','-X','utf8','-m','experiments_ext.run_receiver_factorial',
         '--run-id','2026-10-15-statistical-v1','--output-run-id','2026-10-15-receiver-v1',
         '--admission','tom-path-diagnostic-only','--approval-file',
         '.local/reproduction/2026-10-15-receiver-v1/approval.json','--workers','4'],
        ['.venv/Scripts/python.exe','-B','-X','utf8','-m','experiments_ext.summarize',
         'diagnostic','--run-id','2026-10-15-receiver-v1'],
        ['.venv/Scripts/python.exe','-B','-X','utf8','-m','experiments_ext.receiver_report']]
    save(target/'command_ledger.json', dict(commands=commands,
        scope='Tests and simulations ran 2026-10-15; resumed integrity audit, frozen analysis and export on client date 2026-10-16.',
        logs={n:str(run/n) for n in ('contract-tests.log','full-tests.log','execution.log','analysis.log')},
        read_only_startup=['git status --short','git rev-parse HEAD','git remote -v','python --version'],
        additional_checks='Read-only verify_plan/verify_admission/check_protected and raw identity audit; no new simulation.'))
    manifest = dict(experiment_id=run.name, date=execution['start_utc'], analysis_client_date='2026-10-16',
        git_commit=plan['git_commit'], baseline_commit=BASE, working_tree_dirty=plan['working_tree_dirty'],
        scheme='gosc with named diagnostic views shared/private/position/joint',
        config_file=str(source/'configs.json'), config_sha256=plan['configs_sha256'],
        python_version=plan['python'], dependencies_lock='requirements-windows.lock.txt',
        dependencies_lock_sha256=plan['dependencies_lock_sha256'], os=plan['os'], hardware=plan['hardware_manifest'],
        agent_models=['Planner'], llm_cache_mode='not_used', seeds=list(range(4000,4100)),
        train_calib_eval_split='Independent diagnostic only; no training/calibration/eval tuning; no reuse of 0-99,1000-1079,3000-3099.',
        wireless_channel='Original outage/Rayleigh, no CSIT, ideal DL; search task.',
        bandwidth_or_channel_budget='Orthogonal per-agent W100 at +5dB; W50 at +5dB; W100 at -5dB. shared_budget=0. eta=1e-5.',
        commands=commands, raw_output_paths=[str(source/'raw.jsonl')],
        logs=[str(run/n) for n in ('contract-tests.log','full-tests.log','execution.log','analysis.log')],
        status='execution_complete_hypothesis_not_established', notes=stats['interpretation'],
        admission=plan['admission'], completed_fresh=1200, group_n=100, groups=12,
        raw_sha256=sha(source/'raw.jsonl'), raw_bytes=(source/'raw.jsonl').stat().st_size,
        elapsed_seconds=execution['elapsed_seconds'], workers=4,
        sum_worker_mission_wall_seconds=sum(r['elapsed_seconds'] for r in rows),
        cpu_seconds_and_peak_memory='not_measured', llm_calls=0, gpu_used=False,
        original_r4='failed_preserved', r4_s1='statistically_inconclusive',
        protocol_sha256=plan['protocol_sha256'], inherited_preregistration_sha256=plan['inherited_preregistration_sha256'],
        frozen_analysis_sha256=plan['analysis_sha256'], exporter_sha256=sha(__file__),
        all_tasks_completed=all(r['output']['completed'] for r in rows),
        total_false_declarations=sum(r['output']['false_declarations'] for r in rows),
        protected_inputs=protected, tests=dict(contract='11 passed in 6.04s',full='105 passed in 47.77s',
            resumed_date='Not rerun; no tested runner/adapter/core code change. Report export validated against retained data.'))
    save(target/'experiment_manifest.json', manifest)
    text = f'''# Research Task Report

**[RUN] 已完成1200次独立接收端诊断。未确证稳定且实用的接收端状态收益，不能据此宣称发现可支撑新方法的代表性性能缺陷。也没有证明receiver state无效。**

- **Research Question / Hypothesis**：[HYPOTHESIS] 固定原ToM、Planner、scheduler/channel与eta，分别开放receiver私有证据或真实位置，能否在default/W50/snr-5三设置稳定缩短任务时间至少5%？joint与交互为次要。
- **已核验前人工作**：[PAPER] 沿用此前D01 *Resource-Efficient Semantic Communication for Heterogeneous Agentic Teams*，arXiv:2609.39477v1，p.8 Table VI、p.11私有信息对照的核验；本轮未重新精读PDF或核验发表状态，无新增文献/新颖性主张。[CODE] 原run_revision.experiments已含shared/joint oracle，两因素拆分不是作者已有对照缺失的证明。
- **实际阅读源码**：[CODE] 上游{BASE}；执行与冻结分析commit {plan['git_commit']}。gosc/voi.py TeamModel.__init__/_belief_mass/_expected_utility（29–105行）；gosc/simulator.py Simulation.__init__/phase_decide/phase_communicate/result；gosc/config.py；extensions/receiver_oracle.py model_factory/receiver_oracle；experiments_ext/campaign.py diagnostic_jobs/_job、run_receiver_factorial.execute、receiver_admission.verify_admission、summarize.diagnostic/paired/plots。所有代码位置以本次commit核验，不将代理效用称为真实任务效用。
- **本轮新增或修改**：显式限定准入验证/runner及门控测试、批准绑定记录、冻结准入协议、brief；继续任务新增receiver_report证据导出器、本报告/CSV/图/manifest/证据索引与日志。原gosc/experiments/tests/results/cache/License与Obsidian未改，adapter和冻结summarize未改。
- **实际运行**：[RUN] 2026-10-15执行3设置×4模式×100 seeds4000–4099，1200次纯Planner；2026-10-16继续校验及一次冻结统计。完整命令见command_ledger.json；零重跑mission、零模型/依赖下载、零LLM调用。
- **测试与结果**：[RUN] 运行前契约/门控11 passed in6.04s；完整105 passed in47.77s（两个独立调用，不能相加为116个独立测试）。继续任务未重复执行测试；仅导出器为后加报告工具。原始1200条身份/配置/seed/有限值/400步curve与哈希核验通过，3×4组各N100。全部任务找到8个目标，false declarations合计45，均保留。主分析6项family CI全跨零，0项下界>5%阈值。
- **失败/负面证据**：[RUN] default/private的未校正95% CI为[0.45,11.82] slots，校正后[-1.41,13.92]，不能只摘录前者。W50/position点估计慢3.23 slots，但区间跨零，不能称确证伤害。joint三个设置与交互CI均跨零。所有6项family上界仍高于5%阈值，不能排除有实际收益，也不能宣称统计等价。[RUN] 原strict R4失败、R4-S1四项不确定均原样保留。
- **与原 GOSC 的差异**：只改变TeamModel可见状态的诊断view；shared与joint对应原tom_oracle False/True，新增private/position两个mask。未实现新估值器、改变真实Agent行为规则、scheduler或channel；不存在可投稿方法贡献的既定结论。
- **公平性与泄露检查**：相同mission seeds/初始世界/随机流生成、原配置/每时隙资源；轨迹分叉后观察/候选消息会内生分叉，不是每次通信前同状态的deliver/drop反事实。4000–4099未用于训练/调参，也未替换原eval/calibration。共享资源参数shared_budget=0，即正交上行，不能外推网络共享调度。oracle显式使用当前私有状态、未使用未来奖励；访问/同步免费且不可部署，固定eta不保证实际UL/DL成本匹配。
- **成本**：[RUN] 仿真墙钟{execution['elapsed_seconds']:.3f}s（{execution['elapsed_seconds']/60:.2f}min），4workers，每worker1数值线程；mission墙钟求和{manifest['sum_worker_mission_wall_seconds']:.3f}s，仅为并发任务耗时求和、不是测得CPU时间。raw {manifest['raw_bytes']:,}字节。测试/分析/报告另计；无GPU/收费API/LLM。无线bits是模型payload、不是实测序列化字节；packet-success、tokens、CPU/RAM峰值、估值器分项耗时未测。
- **可否进入下一阶段**：**No-Go for方法开发/收益主张；Pending for接收端假设。** 已批准的Receiver-D1执行和证据归档完成；总体R4仍未通过。不能用“执行passed”覆盖科学假设不成立/未确证的边界。
- **用户需要批准的下一步**：建议先审查估值代理与真实Planner行为的机制差异，起草同决策前状态、匹配外生随机流的离线反事实小实验与成本口径，再决定是否值得开发M0。此为[HYPOTHESIS]后续研究建议，尚未执行；不因本轮弱信号自动扩seed、改任务或增加模型。作者环境询问仍为未发送草稿。本轮到此停止。

## 1. 六个主要比较

[RUN] 正收益=shared completion_time−intervention completion_time，单位slots；百分比=均值差/shared均值。N=100 paired missions每模式。统计seed0，paired bootstrap4000，六个private/position比较用Bonferroni6 percentile区间（family近似95%；单项约99.167%）；4000次的极端尾部仅约17个重采样，存在Monte Carlo误差，不声称精确覆盖。5%阈值相对于观察到的shared样本均值固定；百分比为点估计，未给独立比率CI。正/负/零seed指任务时间差的方向。

| 设置 | 干预 | 收益slots | 收益% | 未校正95% CI | family CI | 5%阈值slots | 正/负/零seed |
|---|---|---:|---:|---|---|---:|---|
{chr(10).join(primary)}

[RUN] 点估计≥5%为1/6；family下界>0为0/6；family下界>5%为0/6；family上界<5%为0/6。private或position均未满足“三设置family下界均>5%”的冻结稳定实用标准。这是证据不足，不能推断因果效应为零或永远无法提升。

## 2. 全部模式的任务和资源分布

[RUN] completion_time均值的区间为正态近似边际95%，不用于主要显著性判断；Q25/median/Q75为样本分位数。statistics.json保留各指标N/均值/分位数/正态区间半宽；其mean_ci_normal95字段是半宽，表中已转换为端点。所有组completed=1.00，不把45次false declarations隐藏在完成率后。6 agents、32×32、8 victims、search、horizon400；default W100/SNR+5dB，W50 W50/+5dB，snr-5 W100/−5dB；原eta1e-5。

| 设置 | 模式 | N | 时间均值 | 均值边际95% CI | 时间Q25/median/Q75 | UL uses均值 | 记录DL uses均值 | payload bits均值 | false declarations均值 |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
{chr(10).join(means)}

## 3. 通信差异与次要联合干预

[RUN] 下表差值=intervention−shared，正值为更多开销。括号为未校正、仅描述性的paired95% CI（不是主要六项family区间）。UL+DL是原base模拟器记录的data UL + common-knowledge广播DL；未增加oracle同步bits/时延/失败、packet headers或真实协议栈成本。模型ack_bits默认字段不意味着base实际包含ACK，应以simulator._downlink/result为准。

| 设置 | 干预 | ΔUL uses [95% CI] | Δ(记录UL+DL) uses [95% CI] |
|---|---|---|---|
{chr(10).join(resources)}

[RUN] W50/private的UL与snr-5/position的UL点估计增加；虽部分边际成本CI排除零，也不是经过联合资源family校正的确证主张。不能将default/private的8.48%直接写为等成本净收益。bits/8不等于真实线路序列化字节。

以下joint仅次要、未校正95%，表中family列等于95%列，不能当作六项family结果：

| 设置 | 干预 | 收益slots | 收益% | 95% CI | 同一95% CI | 5%阈值slots | 正/负/零seed |
|---|---|---:|---:|---|---|---:|---|
{chr(10).join(secondary)}

交互=joint收益−private收益−position收益，以下为次要未校正95% CI：

{interaction}

## 4. 机制解释与外推限制

- [CODE] voi.py:46–57/97–105中dist同时进入预测policy分数和sender侧u_true；position干预不是只修正policy预测误差，不能将其差异唯一归因“接收者位置不准确”。private同时开放pending_llr和confirmed_pending，不等于只改变单个belief标量。
- [CODE] joint仍用Boltzmann softmax代理、sender侧belief效用和shared deconfliction信息；实际Agent.plan有argmax与hysteresis。原joint不是最优决策oracle，也不是真实任务收益上界；增加信息可能改变错误代理的排序，单因素收益不保证可加。
- [CODE] simulator.phase_decide的private_tv为未归一化概率图L1差的时间平均代理，不能当作接收者任务正确率或标准归一化TV。其变化也可能随轨迹/通信变化，未做中介效应识别。
- [HYPOTHESIS] 代理目标、决策规则差异、轨迹非线性和资源变化均可能解释信号不稳定；本轮未分别识别，不可断言某一个原因已证实。
- [RUN] 仅一个网格search任务的三参数设置、纯Planner，不能推广为开放式多轮LLM任务、rescue任务或共享无线系统的结论。未执行LLM cached/live、重新calibration、等成本frontier或新方法。
- [RUN] 接收端诊断是用户批准的ToM路径限定准入；前置1900条ToM已有保存字段匹配，不能将此改写成原5200全部精确复现。此前throughput数值敏感性与本receiver假设是不同问题。

## 5. 证据与重建

- 原始完整raw/curve、source/config/plan/approval/log保留在 `{run}`；raw SHA256 `{manifest['raw_sha256']}`。
- 所有1200逐seed标量（含不利seed与错误声明）在per_seed_outcomes.csv；总体/配对统计由冻结experiments_ext.summarize计算，无手工改图点。time_contrasts为主要区间加次要joint；time_and_resources为边际95%的描述散点，不能用于family显著性判定。
- preanalysis_audit.json与experiment_manifest.json记录身份/配置/哈希/原准入/76项保护；原statistical-v1的raw和gate哈希保持不变。复制的历史approval日期与运行日期保留，不以继续日期冒充新运行。
- command_ledger.json列真实命令。`summarize diagnostic`和本导出器均拒绝已有输出；重建时复制完整run证据到新隔离目录并选择新的输出实现，不覆盖本次完成记录。
- 测试日志：contract-tests.log、full-tests.log；继续任务不重复耗时测试，报告工具没有作为已通过105项的一部分。图PNG已目视检查：标签/区间/图例完整，未修改冻结绘图结果。
'''
    with (target/'report.md').open('x', encoding='utf-8') as f: f.write(text)
    save(target/'evidence_index.json', dict(raw=str(source/'raw.jsonl'),
        primary='statistics.json settings.*.contrasts.private/position.time_shared_minus_mode',
        resources='statistics.json settings.*.contrasts.*.ul_mode_minus_shared/total_recorded_uses_mode_minus_shared',
        all_seeds='per_seed_outcomes.csv', masks='extensions/receiver_oracle.py',
        tested_execution_commit=plan['git_commit'], analysis='experiments_ext/summarize.py',
        report_generation='experiments_ext/receiver_report.py', decisions='decision_summary.json'))
    files = {p.name:sha(p) for p in target.iterdir() if p.is_file()}
    save(target/'artifact_hashes.json', files)
    print(json.dumps(dict(destination=str(target), records=1200, decisions=decisions,
                         artifacts=len(files)+1, protected=protected), indent=2))


if __name__ == '__main__':
    export()
