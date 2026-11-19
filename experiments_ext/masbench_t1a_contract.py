"""HPC-only T1-A runner with a kernel network denial inherited by children."""
import ctypes
import errno
import os
from pathlib import Path
import platform
import resource
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
from hpc_runs import require_hpc


def deny_network():
    if platform.machine() != 'x86_64':
        raise RuntimeError('network filter requires Linux x86_64')

    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                    ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]

    class Program(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]

    rules = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e),
             (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0),
             (0x35, 0, 1, 0x40000000), (0x06, 0, 0, 0x80000000)]
    for syscall in [*range(41, 56), 288, 299, 307, 425, 426, 427]:
        rules.extend([(0x15, 0, 1, syscall), (0x06, 0, 0, 0x50000 | errno.EPERM)])
    rules.append((0x06, 0, 0, 0x7fff0000))
    filters = (Filter * len(rules))(*(Filter(*row) for row in rules))
    program = Program(len(rules), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) or libc.prctl(22, 2, ctypes.byref(program), 0, 0):
        raise OSError(ctypes.get_errno(), 'network denial unavailable')


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    output = Path(os.environ['GOSC_OUTPUT_DIR'])
    fixture = output / 'fixtures'
    fixture.mkdir()
    os.environ['T1_FIXTURE_ROOT'] = str(fixture)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    deny_network()
    suite = unittest.defaultTestLoader.loadTestsFromName('tests_ext.test_masbench_t1_live_driver')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    print(f'fixture_artifact_bytes={total}')
    return int(not result.wasSuccessful() or total > 16 * 1024**2)


if __name__ == '__main__':
    raise SystemExit(main())
