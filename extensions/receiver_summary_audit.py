"""Audit-only summaries: local information and an explicit binary envelope, no policy."""
import binascii, math
import numpy as np
from gosc.belief import sigmoid
EDGES=np.array([.125,.25,.5,1.,2.,4.,8.])
def private_novelty_bucket(common_llr,own_pending,declared):
    live=~np.asarray(declared).reshape(common_llr.shape)
    tv=float(np.abs(sigmoid(common_llr+own_pending)-sigmoid(common_llr))[live].sum())
    return int(np.searchsorted(EDGES,tv,side='right')),tv
def _integer(x,limit):
    if isinstance(x,bool) or not isinstance(x,(int,np.integer)) or not 0<=x<limit:
        raise ValueError('Integer field outside explicitly supported range')
    return int(x)
def encode(sender,created,bucket,pose=None):
    """Standalone audit namespace only. Header8 + payload16/24; no wire interoperability claim."""
    sender=_integer(sender,32);created=_integer(created,512);bucket=_integer(bucket,8)
    if pose is None:
        word=(created<<7)|(bucket<<4)|8
        return bytes([sender])+word.to_bytes(2,'big')
    pose=_integer(pose,1024)
    word=(pose<<14)|(created<<5)|(bucket<<2)|2
    return bytes([32|sender])+word.to_bytes(3,'big')
def decode(data,now,max_age=20):
    now=_integer(now,512);max_age=_integer(max_age,512)
    if len(data) not in (3,4):raise ValueError('Invalid length')
    kind,sender=data[0]>>5,data[0]&31
    w=int.from_bytes(data[1:],'big')
    if kind==0 and len(data)==3:
        created,bucket,valid,pad=w>>7,(w>>4)&7,(w>>3)&1,w&7
        pose=None
    elif kind==1 and len(data)==4:
        pose,created,bucket,valid,pad=w>>14,(w>>5)&511,(w>>2)&7,(w>>1)&1,w&1
    else:raise ValueError('Unknown standalone namespace kind')
    if pad or not valid or created>now or now-created>max_age:raise ValueError('Invalid, future or expired frame')
    return {'sender':sender,'created':created,'bucket':bucket,'pose':pose}
def crc_frame(app):
    return app+binascii.crc_hqx(app,0xffff).to_bytes(2,'big')
def unframe(frame,now,max_age=20):
    if len(frame) not in (5,6):raise ValueError('Invalid framed length')
    app=frame[:-2]
    if int.from_bytes(frame[-2:],'big')!=binascii.crc_hqx(app,0xffff):raise ValueError('CRC mismatch')
    return decode(app,now,max_age)
def symbols(app_bits,overhead_bits,rate):
    if app_bits<0 or overhead_bits<0 or rate<=0:raise ValueError('Invalid cost inputs')
    return math.ceil((app_bits+overhead_bits)/rate)
