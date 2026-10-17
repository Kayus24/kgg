#!/usr/bin/env python3
"""Run existing patient acceptance suites on one immutable candidate; never deploy."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, signal, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CONFIG=ROOT/'release-pipeline/patient-integrated-suites.json'
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def git(*args:str)->bytes:return subprocess.check_output(['git',*args],cwd=ROOT,timeout=20)
def write_json(p:pathlib.Path,obj:dict)->None:
 p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def fingerprint()->str:
 state=hashlib.sha256(git('rev-parse','HEAD')+git('diff','--binary','HEAD'))
 for name in git('ls-files','--others','--exclude-standard','-z').decode('utf-8').split('\0'):
  if name and not name.startswith(('.tmp/','tmp/')):
   state.update(name.encode());state.update((ROOT/name).read_bytes())
 return state.hexdigest()
def kill_owned(p:subprocess.Popen)->None:
 if os.name=='nt':subprocess.run(['taskkill','/pid',str(p.pid),'/T','/F'],capture_output=True,timeout=12)
 else:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass

def main()->int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--engine',choices=['chromium','webkit'],required=True)
 parser.add_argument('--out',type=pathlib.Path,required=True)
 parser.add_argument('--resume',action='store_true')
 parser.add_argument('--allow-dirty',action='store_true',help='Local diagnosis only: cannot yield release-ready report')
 parser.add_argument('--max-steps',type=int,default=100)
 args=parser.parse_args();out=args.out.resolve()
 if out.name!='patient-ui-parity':raise ValueError('isolated patient-ui-parity output required')
 config=json.loads(CONFIG.read_text());source=git('rev-parse','HEAD').decode().strip()
 dirty=bool(git('status','--porcelain').strip())
 if dirty and not args.allow_dirty:raise ValueError('dirty worktree: commit or use explicit local-only diagnostic mode')
 digest=fingerprint();ledger_path=out/'execution-index.json'
 if ledger_path.exists():
  if not args.resume:raise ValueError('existing evidence: use --resume; never silently erase it')
  ledger=json.loads(ledger_path.read_text())
  if (ledger['sourceSha'],ledger['fingerprint'],ledger['engine'])!=(source,digest,args.engine):
   raise ValueError('candidate changed: use a new evidence directory; no stale reuse')
 else:
  ledger={'schema':1,'sourceSha':source,'fingerprint':digest,'engine':args.engine,'candidateDirty':dirty,
    'requiredSteps':config['requiredSteps'],'steps':[],'startedAt':time.time()}
 out.mkdir(parents=True,exist_ok=True)
 groups=json.loads(subprocess.check_output(['node','--input-type=module','-e',
  "import {GROUPS} from './release-pipeline/kgg_patient_full_acceptance_report.mjs';console.log(JSON.stringify(GROUPS))"],cwd=ROOT,timeout=15))
 groups={g['id']:g for g in groups}
 values={'engine':args.engine,'sha':source,'out':str(out),'previewRoot':str(out.parent/'preview-runtime'),
  'preview':str(out.parent/'preview-runtime/previews/patient-gate-self-test')}
 external_log=out.parent/'core-running.log';completed=0
 for job in config['jobs']:
  previous=next((s for s in ledger['steps'] if s['id']==job['id']),None)
  if previous and previous['status']=='PASS':
   lp=out/previous['log']
   if not lp.is_file() or sha(lp.read_bytes())!=previous['sha256']:raise ValueError('completed evidence modified: '+job['id'])
   continue
  if completed>=args.max_steps:break
  if fingerprint()!=digest:raise ValueError('source changed during acceptance; stop without claiming PASS')
  # All core cleanup happens before any supplemental proof; core stdout is outside its cleanup path.
  log=external_log if job['id']=='core' else out/'logs'/(job['id']+'.log')
  log.parent.mkdir(parents=True,exist_ok=True)
  command=[str(x).format(**values) for x in job['command']]
  if command[0]=='python':command[0]=sys.executable
  env=os.environ.copy();env.update(KGG_PARITY_HEAD_SHA=source,KGG_PARITY_OUT=str(out),PYTHONIOENCODING='utf-8')
  env.update({k:v.format(**values) for k,v in job['env'].items()})
  print(json.dumps({'event':'START','step':job['id'],'engine':args.engine}),flush=True)
  began=time.monotonic();timeout=False
  with log.open('wb') as stream:
   child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0,start_new_session=os.name!='nt')
   try:exit_code=child.wait(timeout=job['timeoutSeconds'])
   except subprocess.TimeoutExpired:kill_owned(child);exit_code=124;timeout=True
  if job['id']=='core':
   (out/'logs').mkdir(parents=True,exist_ok=True);target=out/'logs/core.log';target.write_bytes(log.read_bytes());log=target
  data=log.read_bytes();entry={'id':job['id'],'status':'PASS' if exit_code==0 else 'TIMEOUT' if timeout else 'FAIL',
   'completed':not timeout,'exitCode':exit_code,'log':log.relative_to(out).as_posix(),'sha256':sha(data),
   'seconds':round(time.monotonic()-began,3)}
  if exit_code==0 and 'group' in job:
   try:
    rows=[]
    for line in data.decode('utf-8',errors='replace').splitlines():
     if job['prefix'] and not line.startswith(job['prefix']):continue
     raw=line[len(job['prefix']):]
     if not raw.startswith('{'):continue
     item=json.loads(raw)
     if item.get('engine')==args.engine and item.get('sourceSha')==source and (not job.get('mode') or item.get('mode')==job['mode']):rows.append(item)
    g=groups[job['group']];wanted=[job['mode']] if job.get('mode') else g['modes']
    if len(rows)!=len(wanted) or sorted(r.get('mode') for r in rows)!=sorted(wanted):raise ValueError('missing/duplicate/wrong-mode proof')
    for item in rows:
     assertions={key:item.get(key) for key in g['requiredAssertions']}
     if any(v is not True for v in assertions.values()):raise ValueError('scope assertion not true')
     proof={'schema':1,'status':'PASS','syntheticOnly':True,'sourceSha':source,'engine':args.engine,
       'mode':item['mode'],'featureIds':g['ids'],'assertions':assertions,
       'execution':{key:entry[key] for key in ['completed','exitCode','log','sha256']}}
     write_json(out/(g['id']+'-'+item['mode']+'.json'),proof)
   except Exception as e:entry.update(status='FAIL',reason=str(e))
  ledger['steps']=[x for x in ledger['steps'] if x['id']!=entry['id']]+[entry]
  ledger['updatedAt']=time.time();write_json(ledger_path,ledger);completed+=1
  print(json.dumps({'event':'END',**entry}),flush=True)
  if entry['status']!='PASS':break
 ledger['complete']=len(ledger['steps'])==len(config['jobs']) and all(x['status']=='PASS' for x in ledger['steps'])
 write_json(ledger_path,ledger)
 for filename in ['kgg_patient_ui_parity_report.mjs','kgg_patient_full_acceptance_report.mjs']:
  result=subprocess.run(['node','release-pipeline/'+filename,str(out)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=30)
  if result.returncode:print(result.stderr[-1500:],flush=True)
 status=json.loads((out/'acceptance.json').read_text()).get('status') if (out/'acceptance.json').exists() else 'INCOMPLETE'
 print(json.dumps({'engine':args.engine,'complete':ledger['complete'],'candidateDirty':dirty,'acceptance':status,'out':str(out)}),flush=True)
 return 0 if ledger['complete'] and status=='AUTOMATED_SCOPE_PASS_FINAL_PENDING' and not dirty else 2
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:print('Integrated acceptance stopped: '+str(exc),file=sys.stderr);raise SystemExit(1)
