"""Read-only preflight / backed-up descendant Git reconciliation. No local tests."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
LOG = Path(__file__).resolve().parent
OLD = '253a14b19c4410a4606a40c98b8ba24791c7ee43'
NEW = '014b85dfc472c45d8ea5f15e83e0c1ed8e938daf'
BRANCH = 'research/progress-audit-2026-10-19'
prior = ROOT/'research/logs/information-identifiability-acceptance-2026-10-27/manage_hpc.py'
spec = importlib.util.spec_from_file_location('prior_hpc_management', prior)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'reconcile'])
    args = parser.parse_args()
    if args.mode == 'preflight':
        source = module.PREFLIGHT.replace("git_status=git('status','--short')",
            "timeout_program=__import__('shutil').which('timeout'),git_status=git('status','--short')")
    else:
        before = json.loads((LOG/'preflight.json').read_text(encoding='utf-8'))
        if before['head'] != OLD or before['mismatches'] or before['running']:
            raise RuntimeError('Unreconciled preflight mismatch/running task')
        bundle = ROOT/'.local/hpc-sync/native-contract-20261030.bundle'
        bundle.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', OLD, NEW], check=True)
        subprocess.run(['git', '-C', str(ROOT), 'bundle', 'create', str(bundle), BRANCH, '^'+OLD], check=True)
        remote_bundle = '/tmp/gosc-native-contract-20261030.bundle'
        subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', str(bundle), 'hpc:'+remote_bundle], check=True)
        template = module.RECONCILE.replace('20261027-before-information-acceptance',
            '20261030-before-native-contract').replace('refs/gosc-transfer/information-20261027',
            'refs/gosc-transfer/native-contract-20261030')
        source = ('OLD='+repr(OLD)+'\nNEW='+repr(NEW)+'\nBRANCH='+repr(BRANCH)+
                  '\nBUNDLE='+repr(remote_bundle)+'\n'+template)
    result = module.remote_script(source)
    attempt = 1
    while (LOG/(args.mode+'-attempt'+str(attempt)+'-stdout.txt')).exists():
        attempt += 1
    stem = args.mode+'-attempt'+str(attempt)
    (LOG/(stem+'-stdout.txt')).write_bytes(result.stdout)
    (LOG/(stem+'-stderr.txt')).write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    data = json.loads(result.stdout.decode('utf-8').strip().splitlines()[-1])
    (LOG/(args.mode+'.json')).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    data.pop('git_status', None)
    print(json.dumps(data))


if __name__ == '__main__':
    main()
