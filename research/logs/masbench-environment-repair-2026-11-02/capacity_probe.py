"""Bounded RDWR temporary preallocation; no scientific workload or persistent reserve."""
import datetime
import json
import os
from pathlib import Path
import signal

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880 and root.is_dir()
out=Path(os.environ['GOSC_OUTPUT_DIR'])
path=root/'.local'/('capacity-reserve-rdwr-'+str(os.getpid()))
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'requested_bytes':5*1024**3,'mode':'O_RDWR for libc fallback compatibility','path':str(path)}
def timeout(signum,frame):raise TimeoutError('Capacity probe 40s limit')
signal.signal(signal.SIGALRM,timeout);signal.alarm(40)
fd=None
try:
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
    os.posix_fallocate(fd,0,result['requested_bytes'])
    result.update(status='allocated_successfully',allocated_bytes=os.fstat(fd).st_blocks*512)
except (OSError,TimeoutError) as error:
    result.update(status='allocation_failed',errno=getattr(error,'errno',None),error=str(error))
finally:
    if fd is not None:os.close(fd)
    if path.exists():path.unlink()
    result['allocation_released']=not path.exists()
signal.alarm(0)
(out/'capacity_after_cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
