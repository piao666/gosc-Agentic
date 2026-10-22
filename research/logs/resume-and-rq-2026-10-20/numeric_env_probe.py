"""Isolated diagnostic NumPy environments; never change the official project venv."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from hpc_runs import ROOT,require_hpc,write_json
require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR'])
plan=ROOT/'research/sync/runs/hpc-difference-probe-20261020/outputs/probe_plan.json'
shutil.copyfile(plan,out/'probe_plan.json')
uv=Path.home()/'.local/bin/uv';assert uv.is_file()
records=[]
for version in ['1.26.4','2.2.6']:
 envpath=ROOT/('.local/diagnostic-numpy-'+version)
 if not envpath.exists():
  subprocess.run([str(uv),'venv','--python',sys.executable,str(envpath)],check=True,timeout=60)
 else:
  assert (envpath/'pyvenv.cfg').is_file() and envpath.parent==ROOT/'.local'
 runtime=envpath/'bin/python'
 manifest=json.loads((ROOT/'.local/diagnostic-wheels/manifest.json').read_text())
 item=next(row for row in manifest if row['version']==version)
 wheel=ROOT/'.local/diagnostic-wheels'/item['filename']
 with wheel.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==item['sha256']
 subprocess.run([str(uv),'pip','install','--offline','--python',str(runtime),str(wheel)],check=True,timeout=120)
 shutil.copyfile(ROOT/'.local/diagnostic-wheels/manifest.json',out/'official_wheel_manifest.json')
 frozen=subprocess.check_output([str(uv),'pip','freeze','--python',str(runtime)]).decode()
 subprocess.run([str(runtime),str(ROOT/'scripts/repro_differences.py'),'probe','--plan',str(out/'probe_plan.json'),'--variant','numpy-'+version],check=True,timeout=850)
 rows=json.loads((out/('probe-numpy-'+version+'.json')).read_text())
 records.append({'version':version,'python':str(runtime),'freeze':frozen,'missions':len(rows),'records':rows})
 write_json(out/'numpy_environment_comparison.json',{'status':'completed','environments':records,'official_project_environment_unchanged':True})
print(json.dumps([{'version':r['version'],'cases':[{'source':s['source'],'scheme':s['scheme'],'matches_published':not s['different_from_published'],'matches_current':not s['different_from_current']} for s in r['records']]} for r in records]),flush=True)
