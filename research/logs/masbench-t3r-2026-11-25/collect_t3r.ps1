param([string]$EvidenceRoot='E:\gosc\research\logs\masbench-t3r-2026-11-25')
$ErrorActionPreference='Stop'
$remoteRoot='/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs'
$specs=@(
 @{id='hpc-masbench-t3r-inventory-20261125';outputs=@('evidence_inventory.json','source_shapes.json')},
 @{id='hpc-masbench-t3r-traces-20261125';outputs=@('episode_trace_index.json','verification_summary.json')},
 @{id='hpc-masbench-t3r-context-20261125';outputs=@('episode_trace_index.json','verification_summary.json')}
)
$entries=@()
foreach($spec in $specs){
 $dest=Join-Path $EvidenceRoot ('hpc/'+$spec.id)
 New-Item -ItemType Directory -Path $dest -Force | Out-Null
 $files=@('manifest.json','status.json','artifacts.json','stdout.log','stderr.log')+@($spec.outputs|ForEach-Object{'outputs/'+$_})
 foreach($rel in $files){
  $target=Join-Path $dest $rel
  if(Test-Path -LiteralPath $target){throw "Refusing existing target: $target"}
  New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
  $source=$remoteRoot+'/'+$spec.id+'/'+$rel
  $line= & ssh -o BatchMode=yes hpc ('sha256sum '+$source)
  if($LASTEXITCODE -ne 0){throw 'Remote SHA failed'}
  $expected=($line -split '\s+')[0]
  & scp -q ('hpc:'+$source) $target
  if($LASTEXITCODE -ne 0){throw 'SCP failed'}
  $actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual -ne $expected){throw 'Mirror SHA mismatch'}
  $entries+=@{remote_path=$source;local_path=$target;bytes=(Get-Item -LiteralPath $target).Length;sha256=$actual;verified=$true}
 }
}
$receipt=@{schema_version=1;created_at=[DateTimeOffset]::Now.ToString('o');source_host='hpc';purpose='T3-R scoped non-private evidence mirror';all_selected_files_verified=$true;all_run_outputs_mirrored=$false;intentionally_not_pulled=@('controlled_read_aid.private.json','historical raw 684 files','source patch and untracked archive');files=$entries}
$receiptPath=Join-Path $EvidenceRoot 'scoped_receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Receipt already exists'}
[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
$entries|Measure-Object -Property bytes -Sum|Select-Object Count,Sum
