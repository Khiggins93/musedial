"""Hardware USB regression for normal companionship; leaves normal/auto active."""
import argparse
import json
import time
from pathlib import Path
from diagnose import port_open, request, capture

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--output',type=Path,default=Path('local/companion-test.json'))
    parser.add_argument('--seconds',type=int,default=300)
    a=parser.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    report={'passed':False,'checks':[],'samples':[],'physical_confirmation':False}
    def check(name,ok):
        report['checks'].append({'name':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    try:
        with port_open(a.port) as p:
            def cmd(c):return request(p,c)
            def status():return cmd('status')
            cmd('theme normal');initial=status();report['initial']=initial
            check('selftest companion',cmd('selftest companion')=='OK selftest companion')
            for y in (20,120,220):
                for x in (20,120,220):
                    cmd(f'touch {x} {y}');time.sleep(.1);s=status()
                    check(f'gaze {x} {y}',s['companion']=='MIRADA' and s['gaze_x']==(x-120)//100 and s['gaze_y']==(y-120)//100)
            cmd('release');cmd('mode 0')
            for gesture in ('SONRISA','CARINO','ABRAZO'):
                cmd('pet');time.sleep(.2);check(gesture,status()['companion']==gesture)
                if gesture=='ABRAZO':
                    time.sleep(.65)
                    capture(p,a.output.parent/'normal-hug.png')
                time.sleep(.65)
            time.sleep(2);check('gesture expires',status()['companion']=='NINGUNO')
            cmd('mode 0');cmd('pet');cmd('pet');cmd('pet');time.sleep(.2)
            check('tickles',status()['companion']=='COSQUILLAS')
            cmd('sleep');check('sleep cancellation',status()['companion']=='NINGUNO');cmd('wake')
            cmd('touch 20 120');time.sleep(2.1);cmd('release');time.sleep(.7)
            check('hold touch hug',status()['companion']=='ABRAZO')
            cmd('turn 1');check('wheel cancellation',status()['companion']=='NINGUNO')
            cmd('touch 220 20');cmd('theme halloween');check('theme cancellation',status()['companion']=='NINGUNO')
            check('halloween accepts touch',cmd('touch 120 120')=='OK touch')
            cmd('release')
            cmd('theme normal');check('invalid coordinate',cmd('touch 240 0')=='ERROR command')
            # No captures during timed coverage. Exercise every new gesture.
            start=time.monotonic();i=0;previous=status()
            while time.monotonic()-start<a.seconds:
                cmd('mode 0')
                if i%4==0:cmd('touch 20 20')
                elif i%4==1:cmd('pet')
                elif i%4==2:
                    cmd('pet');time.sleep(.7);cmd('pet');time.sleep(.7);cmd('pet')
                else:cmd('pet');cmd('pet');cmd('pet')
                time.sleep(2.2);s=status()
                fps=(s['frames']-previous['frames'])*1000/(s['uptime_ms']-previous['uptime_ms'])
                report['samples'].append({'fps':fps,'heap':s['free_heap'],'uptime_ms':s['uptime_ms'],'companion':s['companion']})
                check('fps >=18',fps>=18)
                check('stable heap',s['free_heap']==initial['free_heap'])
                check('no errors or restart',s['decode_errors']==0 and s['uptime_ms']>previous['uptime_ms'])
                previous=s;i+=1
            cmd('theme normal');report['final']=status();report['passed']=True
    finally:
        a.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'samples':len(report['samples'])}))
if __name__=='__main__':main()
