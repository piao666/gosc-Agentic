"""Finite, task-first residual-capacity protocol replay. No receiver feature enters a task policy."""
import math,binascii
from collections import defaultdict
from extensions.receiver_summary_audit import encode,decode,crc_frame,unframe
def _crc(data):return data+binascii.crc_hqx(data,0xffff).to_bytes(2,'big')
def _payload(frame):
    if len(frame)<4 or int.from_bytes(frame[-2:],'big')!=binascii.crc_hqx(frame[:-2],0xffff):raise ValueError('CRC')
    return frame[:-2]
def feedback(items):
    if len(items)>31:raise ValueError('Too many feedback entries')
    body=bytes([95,len(items)])
    for sender,tx_slot,good in items:
        if not 0<=sender<32 or not 0<=tx_slot<512 or not isinstance(good,bool):raise ValueError('Feedback bounds')
        body+=((sender<<11)|(tx_slot<<2)|(int(good)<<1)).to_bytes(2,'big')
    return _crc(body)
def read_feedback(frame):
    b=_payload(frame)
    if b[0]!=95 or len(b)!=2+2*b[1]:raise ValueError('Feedback format')
    out=[]
    for i in range(b[1]):
        w=int.from_bytes(b[2+2*i:4+2*i],'big')
        if w&1:raise ValueError('Reserved feedback bit')
        out.append((w>>11,(w>>2)&511,bool((w>>1)&1)))
    return out
def batch(apps):
    if len(apps)>31 or any(len(x) not in (3,4) for x in apps):raise ValueError('Batch bounds')
    return _crc(bytes([127,len(apps)])+b''.join(apps))
def read_batch(frame,now):
    b=_payload(frame)
    if b[0]!=127:raise ValueError('Batch kind')
    pos=2;out=[]
    for i in range(b[1]):
        if pos>=len(b):raise ValueError('Truncated batch')
        kind=b[pos]>>5
        if kind not in (0,1):raise ValueError('Nested kind')
        n=3+kind
        if pos+n>len(b):raise ValueError('Truncated summary')
        out.append(decode(b[pos:pos+n],now,max_age=511));pos+=n
    if pos!=len(b):raise ValueError('Trailing batch bytes')
    return out
def replay(rows,interval,with_pose,dl_loss,delay,seed,W,ttl=20):
    # Conditional data model: native task load/fading stay fixed, original mission is never rescheduled.
    import numpy as np
    if not rows or interval<1 or delay<0 or not 0<=dl_loss<=1 or W<1:raise ValueError('Replay bounds')
    by_t=defaultdict(list)
    for row in rows:by_t[row['t']].append(row)
    N=6;pending={};edge={};cache=[{} for _ in range(N)];events=defaultdict(list);attempt_map={}
    counts=defaultdict(int);ages=[];safety=[];events_log=[]
    for t in sorted(by_t):
        current=sorted(by_t[t],key=lambda x:x['agent'])
        assert [x['agent'] for x in current]==list(range(N))
        for kind,frame,tx_t in events.pop(t,[]):
            for receiver in range(N):
                loss=bool(np.random.default_rng([seed,902,tx_t,receiver,kind]).random()<dl_loss)
                counts[('feedback' if kind==0 else 'snapshot')+'_recipient_erased']+=loss
                if loss:continue
                if kind==0:
                    for sender,tx_slot,good in read_feedback(frame):
                        gen=attempt_map[(sender,tx_slot)]
                        if receiver==sender and good and sender in pending and pending[sender][0]==gen:
                            del pending[sender];counts['uplink_pending_cleared_by_received_ack']+=1
                else:
                    for item in read_batch(frame,t):
                        if t-item['created']>ttl:
                            counts['downlink_expired_items_ignored']+=1;continue
                        older=cache[receiver].get(item['sender'])
                        if older is None or item['created']>=older['created']:cache[receiver][item['sender']]=item
        for receiver in range(N):
            for sender in range(N):
                if sender==receiver:continue
                counts['possible_receiver_sender_slot_pairs']+=1
                item=cache[receiver].get(sender)
                if item is not None and 0<=t-item['created']<=ttl:
                    counts['usable_receiver_sender_slot_pairs']+=1;ages.append(t-item['created'])
        for row in current:
            k=row['agent']
            if k in pending and t-pending[k][0]>ttl:
                del pending[k];counts['uplink_pending_expired']+=1
            if t%interval==0:
                if k in pending:counts['uplink_pending_superseded']+=1
                pose=row['pose_cell'] if with_pose else None
                pending[k]=(t,encode(k,t,row['bucket'],pose));counts['generated_summaries']+=1
        acks=[];any_good=False
        for row in current:
            k=row['agent']
            if k not in pending:continue
            created,app=pending[k];wire=crc_frame(app);need=len(wire)*8 # frozen R=1 bit/use
            residual=W-row['original_used']
            if need>residual:counts['budget_deferred_sender_slots']+=1;continue
            counts['uplink_attempts']+=1;counts['uplink_symbols']+=need;counts['uplink_bytes']+=len(wire)
            counts['retransmission_attempts']+=created<t
            safety.append(row['original_used']+need<=W);attempt_map[(k,t)]=created
            good=math.log2(1+row['snr_instant'])>=1
            if good:
                item=unframe(wire,t,max_age=ttl);any_good=True;counts['uplink_decoded']+=1
                if k in edge and edge[k][0]==created:counts['duplicate_uplink_decodes']+=1
                edge[k]=(created,app)
            else:counts['uplink_outages']+=1
            acks.append((k,t,bool(good)))
            events_log.append({'t':t,'agent':k,'created':created,'wire_bytes':len(wire),'residual_before':residual,'used':need,'decoded':bool(good)})
        if acks:
            wire=feedback(acks)
            assert read_feedback(wire)==acks
            counts['feedback_frames']+=1;counts['downlink_feedback_bytes']+=len(wire)
            counts['downlink_feedback_symbols']+=math.ceil(len(wire)*8/2)
            events[t+1+delay].append((0,wire,t))
        if any_good:
            apps=[app for k,(created,app) in sorted(edge.items()) if t-created<=ttl]
            wire=batch(apps);assert len(read_batch(wire,t))==len(apps)
            counts['snapshot_frames']+=1;counts['downlink_snapshot_bytes']+=len(wire)
            counts['downlink_snapshot_symbols']+=math.ceil(len(wire)*8/2)
            events[t+1+delay].append((1,wire,t))
    for key in ['generated_summaries','uplink_attempts','uplink_symbols','uplink_bytes','uplink_decoded','uplink_outages','retransmission_attempts','duplicate_uplink_decodes','uplink_pending_expired','uplink_pending_superseded','budget_deferred_sender_slots','feedback_frames','snapshot_frames','downlink_feedback_bytes','downlink_snapshot_bytes','downlink_feedback_symbols','downlink_snapshot_symbols','uplink_pending_cleared_by_received_ack','downlink_expired_items_ignored']:
        counts.setdefault(key,0)
    counts['right_censored_pending_summaries']=len(pending)
    counts['right_censored_downlink_frames']=sum(map(len,events.values()))
    counts['total_added_channel_uses']=counts['uplink_symbols']+counts['downlink_feedback_symbols']+counts['downlink_snapshot_symbols']
    counts['usable_fraction']=counts['usable_receiver_sender_slot_pairs']/counts['possible_receiver_sender_slot_pairs']
    assert all(safety)
    return {'seed':seed,'W':W,'refresh_slots':interval,'with_pose':with_pose,'dl_loss':dl_loss,'dl_delay_extra_slots':delay,
       'earliest_use_age':1+delay,'ttl':ttl,'rate_UL':1,'rate_DL':2,'counts':dict(counts),'age_summary':
       {'n':len(ages),'min':min(ages) if ages else None,'median':float(np.median(ages)) if ages else None,'p95':float(np.quantile(ages,.95)) if ages else None},
       'ul_residual_budget_invariant':True,'events':events_log,
       'scope':'Explicit encoded frames and queued retries on fixed native calibration traces; no task policy uses cache; no task-effect estimate'}
