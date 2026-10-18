"""Precision-extension integrity and paired-statistics tests; no new rollouts."""
import hashlib
import pickle

import numpy as np
import pytest

from experiments_ext.run_receiver_cf_precision import NEW_REPLICATES, normalized_files, verified_unpickle
from experiments_ext.analyze_receiver_cf_precision import LEVELS, merge_rows, point_at_R


def sample(n=32):
    f={"point_id":"5000:8","packet_id":"test-packet","seed":5000,"t":8,"sender":0,
       "kind":"EVID","tom":.2,"tv":.4,"aoi":1.,"bits":32}
    rows=[]
    for rr in range(n):
        for success in (False,True):
            delta=(-2,0,2,4)[rr%4]
            r={"point_id":f["point_id"],"packet_id":f["packet_id"],"replicate":rr,
               "success_branch":success,"status":"ok","snapshot_state_sha256":"same",
               "future_rng_initial_sha256":{"sense":"paired"},"future_seed_key":[5000,8,0,rr],
               "current_slot":{"current_cost":{"bits":32,"symbols":16},
                 "attempts":[{"packet_id":"test-packet","effective_decode":success}],
                 "shadow_pre_motion_replan":[{"agent":1,"target":1}]},
               "next_actual_decision":[{"agent":1,"target":int(success)}],
               "result":{"completion_time":100+(0 if success else delta),"completed":True,
                   "found":8,"false_declarations":0,"bits":1000,"symbols":500,"dl_symbols":200,"delivered_bits":900}}
            rows.append(r)
    return f,rows


def test_snapshot_hash_checked_before_unpickle(tmp_path,monkeypatch):
    p=tmp_path/"snapshot.pkl";p.write_bytes(b"untrusted-test-bytes")
    def forbidden(_):raise AssertionError("Must not deserialize mismatched bytes")
    monkeypatch.setattr(pickle,"loads",forbidden)
    with pytest.raises(ValueError,match="hash mismatch"):
        verified_unpickle(p,"wrong")


def test_known_self_generated_bytes_round_trip(tmp_path):
    p=tmp_path/"own.pkl";p.write_bytes(pickle.dumps({"owned":"synthetic"}))
    assert verified_unpickle(p,hashlib.sha256(p.read_bytes()).hexdigest())=={"owned":"synthetic"}


def test_windows_index_normalization_and_collision_rejection():
    assert normalized_files({"files":{"seed-5000\\snapshot-8.pkl":{"sha256":"x"}}})=={"seed-5000/snapshot-8.pkl":{"sha256":"x"}}
    with pytest.raises(ValueError,match="Colliding"):
        normalized_files({"files":{"a\\b":{},"a/b":{}}})


def test_scope_exact784_new_branches_and_fixed_cumulative_levels():
    assert NEW_REPLICATES==tuple(range(4,32)) and 14*len(NEW_REPLICATES)*2==784
    assert LEVELS==(4,8,16,32)


def test_merge_rejects_duplicate_changed_packet_and_reused_old_repetitions():
    f,rows=sample()
    old=[r for r in rows if r["replicate"]<4];new=[r for r in rows if r["replicate"]>=4]
    assert len(merge_rows(old,new,[f]))==64
    with pytest.raises(ValueError,match="Duplicate"):
        merge_rows(old+old[:1],new,[f])
    with pytest.raises(ValueError,match="out-of-scope"):
        merge_rows(old,new+old[:1],[f])
    with pytest.raises(ValueError,match="packet changed"):
        merge_rows(old,[{**new[0],"packet_id":"different"}],[f])


def test_mc_standard_error_is_of_paired_differences_and_scales_for_repeated_sample():
    f,rows=sample();lookup=merge_rows(rows[:8],rows[8:],[f])
    for R in LEVELS:
        p,error=point_at_R(f,lookup,R)
        assert error is None and p["delta_T"]==1.
        d=np.asarray(([-2.,0.,2.,4.]*(R//4)))
        assert p["mc_se_delta_T"]==pytest.approx(d.std(ddof=1)/np.sqrt(R))
        assert (p["pair_positive"],p["pair_zero"],p["pair_negative"])==(R//2,R//4,R//4)
        assert p["next_receiver_changes_mean"]==1.


def test_partial_replica_level_is_not_silently_reduced():
    f,rows=sample();lookup=merge_rows(rows[:8],rows[8:-1],[f])
    p,error=point_at_R(f,lookup,32)
    assert p is None and error["missing_or_failed_replicates"]==[31]
    assert point_at_R(f,lookup,16)[1] is None


def test_pair_draw_or_cost_mismatch_is_rejected():
    f,rows=sample(4)
    changed=[{**r} for r in rows]
    changed[1]={**changed[1],"future_rng_initial_sha256":{"sense":"different"}}
    with pytest.raises(AssertionError):
        point_at_R(f,merge_rows(changed,[],[f]),4)
