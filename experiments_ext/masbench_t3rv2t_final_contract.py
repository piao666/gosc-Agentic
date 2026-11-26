"""Register only the narrow final-admission contracts on HPC."""
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET

from scripts.hpc_runs import ROOT, require_hpc, write_json
from extensions.masbench_reasoning.fair_final_v2_task import MATERIAL_FILES, file_sha


def main():
    require_hpc()
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2,) * 2)
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    xml = out / 'pytest.xml'
    test = 'tests_ext/test_masbench_t3rv2t_final_admission.py'
    code = subprocess.run([sys.executable, '-m', 'pytest', '-q', test, '-p', 'no:cacheprovider',
                           '--junitxml', str(xml)], timeout=110,
                          env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')).returncode
    tests = list(ET.parse(xml).iter('testcase'))
    previous = 'research/artifacts/masbench-t3rv2t-20261126/contract-final.json'
    names = (*MATERIAL_FILES, test, str(Path(__file__).relative_to(ROOT)))
    write_json(out / 'contract.json', dict(passed=code == 0 and len(tests) == 8, tests=len(tests), model_calls=0,
               previous_contract=previous, previous_contract_sha256=file_sha(ROOT / previous),
               source_files={name: file_sha(ROOT / name) for name in names}))
    raise SystemExit(code or int(len(tests) != 8))


if __name__ == '__main__':
    main()
