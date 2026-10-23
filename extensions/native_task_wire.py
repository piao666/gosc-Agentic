"""Versioned lossless task-semantic codec; NOT the author's abstract bit format.

The outer paid-service frame adds 10 bytes (type/length/source/id/CRC16).
This payload carries every observation timestamp explicitly; no metadata oracle.
"""
import struct
import math
from gosc.belief import Obs
from gosc.messages import Packet
from gosc.schemes import GOSC,Group,Option
from gosc.voi import TeamModel

KINDS={'CONF':0,'INTENT':1,'EVID':2}


def integer(x,limit):
    if type(x) is not int or not 0<=x<limit:raise ValueError('wire integer bounds')
    return x


def encode_packet(packet,cfg):
    if cfg.grid>256 or packet.kind not in KINDS or packet.sent:
        raise ValueError('Unsupported task/fragment/grid')
    sender=integer(packet.sender,32);created=integer(packet.created,512)
    body=b'GP\x01'+bytes([KINDS[packet.kind],sender])+struct.pack('>H',created)
    if packet.kind in ('CONF','INTENT'):
        cell=packet.confirm if packet.kind=='CONF' else packet.intent
        if packet.records or (packet.intent is not None if packet.kind=='CONF' else packet.confirm is not None):
            raise ValueError('Mixed payload')
        return body+struct.pack('>H',integer(cell,cfg.grid**2))
    if not packet.records or packet.confirm is not None or packet.intent is not None:
        raise ValueError('Empty/mixed evidence')
    body+=struct.pack('>H',integer(len(packet.records),65536))
    for rec in packet.records:
        if rec.agent!=sender or rec.t>created:raise ValueError('Evidence identity/time')
        body+=struct.pack('>HHHH',integer(rec.t,512),integer(rec.pos[0],cfg.grid),
                          integer(rec.pos[1],cfg.grid),integer(len(rec.det),65536))
        for cell in rec.det:body+=struct.pack('>H',integer(cell,cfg.grid**2))
    return body


def decode_packet(body,cfg):
    if len(body)<9 or body[:3]!=b'GP\x01' or body[3] not in KINDS.values():
        raise ValueError('Task namespace/length')
    kind=next(k for k,v in KINDS.items() if v==body[3]);sender=body[4]
    created=struct.unpack('>H',body[5:7])[0]
    if kind!='EVID':
        if len(body)!=9:raise ValueError('Trailing task bytes')
        cell=struct.unpack('>H',body[7:9])[0]
        pkt=Packet(kind,sender,len(body)*8,created,**{'confirm' if kind=='CONF' else 'intent':cell})
    else:
        count=struct.unpack('>H',body[7:9])[0];pos=9;records=[]
        try:
            for _ in range(count):
                t,x,y,n=struct.unpack('>HHHH',body[pos:pos+8]);pos+=8
                cells=struct.unpack('>'+'H'*n,body[pos:pos+2*n]);pos+=2*n
                records.append(Obs(t,sender,(x,y),cells))
        except struct.error as e:raise ValueError('Truncated evidence') from e
        if pos!=len(body):raise ValueError('Trailing evidence bytes')
        pkt=Packet(kind,sender,len(body)*8,created,records=records)
    if encode_packet(pkt,cfg)!=body:raise ValueError('Noncanonical task')
    return pkt


def service_bits(packet,cfg):
    return 8*(10+len(encode_packet(packet,cfg)))


class WireGOSC(GOSC):
    """Reuse native values and scheduler; rebuild prefixes from actual wire sizes."""
    def __init__(self,cfg,channel,voi_mode='tom'):
        if cfg.task!='search' or cfg.tom_oracle or cfg.shared_budget or cfg.llm_agents or cfg.value_mode!='exact' or cfg.overhead_bits:
            raise ValueError('Wire adapter supports exact nonoracle orthogonal Planner search, H0')
        if voi_mode not in ('tom','bits','aoi'):raise ValueError('Unsupported value')
        super().__init__(cfg,channel,voi_mode=voi_mode,name='wire_'+voi_mode+'_adapter')

    def packet(self,agent,group,option,t):
        if group.kind=='CONF':return Packet('CONF',agent.idx,0,t,confirm=group.cell)
        if group.kind=='INTENT':return Packet('INTENT',agent.idx,0,t,intent=agent.target)
        return Packet('EVID',agent.idx,0,t,records=list(agent.pending_records[:option.n_records]))

    def build_groups(self,agent,snr_mean,sim):
        c=self.cfg;team=TeamModel(sim,agent,c.tom_temperature) if self.voi_mode=='tom' else None
        groups=[]
        def options(packet,value,n=0):
            bits=service_bits(packet,c)
            return [Option(r,bits,math.ceil(bits/r),value*float(self.channel.success_prob(r,snr_mean,n=math.ceil(bits/r))),n)
                    for r in c.rates if math.ceil(bits/r)<=c.symbols_per_slot]
        for cell in sorted(agent.confirmed_pending-getattr(agent,'acked_confirms',set())):
            pkt=Packet('CONF',agent.idx,0,sim.t,confirm=cell)
            value=c.confirm_value if team else (len(encode_packet(pkt,c))*8 if self.voi_mode=='bits' else 1e6)
            groups.append(Group('CONF',options(pkt,value),cell=cell))
        if agent.target is not None and agent.target!=agent.shared_intent and agent.target!=getattr(agent,'acked_intent',agent.shared_intent):
            pkt=Packet('INTENT',agent.idx,0,sim.t,intent=agent.target)
            value=max(team.intent_voi(agent.target),0.) if team else (float(sim.t-getattr(agent,'_intent_t',sim.t)+1) if self.voi_mode=='aoi' else len(encode_packet(pkt,c))*8)
            groups.append(Group('INTENT',options(pkt,value)))
        records=agent.pending_records;fits={}
        sizes=[service_bits(Packet('EVID',agent.idx,0,sim.t,records=records[:n]),c) for n in range(1,len(records)+1)]
        for r in c.rates:
            ns=[n for n,b in enumerate(sizes,1) if math.ceil(b/r)<=c.symbols_per_slot]
            if ns:fits[r]=max(ns)
        if fits:
            vals=self.evidence_voi(sim,records,fits.values(),team) if self.voi_mode!='bits' else {n:float(sizes[n-1]-80) for n in fits.values()}
            opts=[Option(r,sizes[n-1],math.ceil(sizes[n-1]/r),vals[n]*float(self.channel.success_prob(r,snr_mean,n=math.ceil(sizes[n-1]/r))),n) for r,n in fits.items()]
            groups.append(Group('EVID',opts))
        return [g for g in groups if g.options]
