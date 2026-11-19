"""Query the current UID's read-only Lustre Q_GETQUOTA without installing lfs."""
import ctypes
from datetime import datetime, timezone
import fcntl
import json
import os


class DqInfo(ctypes.Structure):
    _fields_ = [('bgrace', ctypes.c_uint64), ('igrace', ctypes.c_uint64),
                ('flags', ctypes.c_uint32), ('valid', ctypes.c_uint32)]


class DqBlocks(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ('bhardlimit', 'bsoftlimit', 'curspace', 'ihardlimit', 'isoftlimit', 'curinodes', 'btime', 'itime')]
    _fields_ += [('valid', ctypes.c_uint32), ('padding', ctypes.c_uint32)]


class UserQuota(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in ('cmd', 'type', 'id', 'stat', 'valid', 'idx')]
    _fields_ += [('info', DqInfo), ('data', DqBlocks), ('obd_type', ctypes.c_char*16),
                 ('obd_uuid', ctypes.c_char*40)]


uid = os.getuid()
assert uid==8301880 and os.uname().machine=='x86_64' and ctypes.sizeof(UserQuota)==176
command = (3 << 30) | (176 << 16) | (ord('f') << 8) | 162
result = {}
for name, mount in [('ssd','/home/u202520081000097'), ('hdd','/hdd/u202520081000097')]:
    data = UserQuota(cmd=0x800007,type=0,id=uid)
    buffer = bytearray(data)
    fd = os.open(mount,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
    try:
        fcntl.ioctl(fd,command,buffer,True)
    except OSError as error:
        result[name] = {'mount':mount,'errno':error.errno,'error':error.strerror}
        continue
    finally:
        os.close(fd)
    entry = UserQuota.from_buffer_copy(buffer)
    returned = {field:getattr(entry.data,field) for field,_ in entry.data._fields_ if field!='padding'}
    limit = returned['bhardlimit']*1024
    result[name] = {'mount':mount,'quota_status':entry.stat,'id':entry.id,'type':entry.type,
                    'hard_limit_bytes':limit,'used_bytes':returned['curspace'],
                    'remaining_to_hard_limit_bytes':limit-returned['curspace'] if limit else None,
                    'raw_quota_fields':returned}
print(json.dumps({'host':os.uname().nodename,'queried_at':datetime.now(timezone.utc).isoformat(),
                  'uid':uid,'interface':'read-only Lustre user quota ioctl','volumes':result}))
