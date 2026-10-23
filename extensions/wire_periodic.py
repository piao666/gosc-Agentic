"""Periodic admission, CONF priority, FIFO prefixes, actual-wire goodput rates.

Same GOSC source filter as all GP-v1 arms. This is a new common-wire control,
not the author's SEMA fragmentation implementation. ACK retries run every slot.
"""
import math
from gosc.messages import Packet
from gosc.schemes import Group,Option
from .native_task_wire import WireGOSC,service_bits


class WirePeriodic(WireGOSC):
    def __init__(self,cfg,channel):
        if type(cfg.sem_interval) is not int or cfg.sem_interval<1:
            raise ValueError('Positive periodic interval required')
        super().__init__(cfg,channel,'bits')
        self.voi_mode='periodic'

    def select(self,agent,known,view):
        c=self.cfg;remaining=c.symbols_per_slot;chosen=[]

        def admit(kind,cell=None):
            nonlocal remaining
            records=agent.pending_records if kind=='EVID' else []
            opts=[]
            # Size is additive in GP-v1, including the count/header once.
            sizes=[];bits=8*19
            for rec in records:
                bits+=8*(8+2*len(rec.det));sizes.append(bits)
            for rate in c.rates:
                n=0
                if kind=='EVID':
                    fits=[i for i,b in enumerate(sizes,1) if math.ceil(b/rate)<=remaining]
                    if not fits:continue
                    n=max(fits);b=sizes[n-1]
                else:
                    pkt=Packet(kind,agent.idx,0,view.t,**{'confirm' if kind=='CONF' else 'intent':cell})
                    b=service_bits(pkt,c)
                uses=math.ceil(b/rate)
                if uses>remaining:continue
                good=float(self.channel.success_prob(rate,known,n=uses))
                opts.append(Option(rate,b,uses,(b-80)*good,n))
            if not opts:return
            # Useful bits per channel use, matching rate-aware goodput rather
            # than maximizing reliability of a short packet at any airtime.
            opt=max(opts,key=lambda o:(o.value/o.symbols,o.value,-o.symbols,-o.rate))
            if opt.value<=0:return
            chosen.append((Group(kind,[opt],cell=cell if kind=='CONF' else None),opt))
            remaining-=opt.symbols

        for cell in sorted(agent.confirmed_pending-getattr(agent,'acked_confirms',set())):
            admit('CONF',cell)
        if (view.t+1)%c.sem_interval==0:
            if agent.target is not None and agent.target!=agent.shared_intent and agent.target!=getattr(agent,'acked_intent',agent.shared_intent):
                admit('INTENT',agent.target)
            if agent.pending_records:admit('EVID')
        return chosen
