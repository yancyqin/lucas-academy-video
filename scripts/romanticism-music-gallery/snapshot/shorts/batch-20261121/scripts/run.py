from pathlib import Path
import json,subprocess,os,sys,concurrent.futures

ROOT=Path(__file__).resolve().parents[1]
PYTHON='@RUNTIME_DEPS@/python/bin/python3'
NODE='@RUNTIME_DEPS@/node/bin/node'
batch=json.loads((ROOT/'batch.json').read_text())
qa='--qa' in sys.argv
filters={x for x in sys.argv[1:] if not x.startswith('--')}

def finish(job,env):
    log=Path(job['root'])/'checks/finish.log'
    with log.open('w') as output:
        subprocess.run([PYTHON,str(ROOT/'scripts/finish.py')],env=env,stdout=output,stderr=subprocess.STDOUT,check=True)
    print('FINISHED',job['id'],flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    futures=[]
    for job in batch['jobs']:
        if filters and job['id'] not in filters:continue
        env=os.environ.copy();env['ROMANTIC_SHORT_JOB']=job['root']
        log=Path(job['root'])/'checks'/('qa.log' if qa else 'capture.log')
        print('QA START' if qa else 'CAPTURE START',job['id'],flush=True)
        with log.open('w')as output:
            args=[NODE,str(ROOT/'scripts/capture.mjs')]+(['--qa'] if qa else [])
            result=subprocess.run(args,env=env,stdout=output,stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text()[-5000:],flush=True)
            raise RuntimeError(job['id']+' capture failed')
        print('QA PASSED' if qa else 'CAPTURE PASSED',job['id'],flush=True)
        if not qa:futures.append(pool.submit(finish,job,env))
    for future in futures:future.result()
print('ALL QA PASSED' if qa else 'ALL FOUR FILMS FINISHED',flush=True)
