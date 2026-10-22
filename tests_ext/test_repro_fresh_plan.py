import json
import pytest
from repro_fresh_plan import audit

def test_native_fresh_catalog_rejects_missing_seed_or_changed_configuration(tmp_path):
    expected={'missions':100,'jobs':[{'config_sha256':'abc','scheme':'gosc','missions':100}]}
    p=tmp_path/'pool-plans.jsonl';p.write_text(json.dumps({'arguments':[[{'config_sha256':'abc'},'gosc',s] for s in range(3000,3100)]})+'\n')
    assert audit(tmp_path,expected)['exact_configs_schemes_seeds_match']
    p.write_text(json.dumps({'arguments':[[{'config_sha256':'other'},'gosc',s] for s in range(3000,3100)]})+'\n')
    with pytest.raises(RuntimeError,match='differs'):audit(tmp_path,expected)
    p.write_text(json.dumps({'arguments':[[{'config_sha256':'abc'},'gosc',s] for s in range(3000,3099)]})+'\n')
    with pytest.raises(RuntimeError,match='differs'):audit(tmp_path,expected)
