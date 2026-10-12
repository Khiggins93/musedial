"""Optional real-device USB tests. Leaves Halloween awake/automatic; no physical-input claims."""
import argparse,json,time
from pathlib import Path
from diagnose import port_open,request,capture
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',required=True);parser.add_argument('--output',type=Path,default=Path('local/hardware-test.json'))
    a=parser.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    report={'passed':False,'checks':[],'samples':[],'physical_confirmation':False}
    def check(name,ok):
        report['checks'].append({'name':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    try:
        with port_open(a.port) as p:
            def cmd(c):return request(p,c)
            def state():return cmd('status')
            initial=state();report['initial']=initial
            check('community version',initial['version']=='3.1.1-community')
            check('hardware ready',initial['detected_dial'] and initial['display_ready'] and initial['halloween_ready'] and initial['psram_bytes']==0)
            for name in ('input','assets','play'):check('selftest '+name,cmd('selftest '+name)=='OK selftest '+name)
            for theme,count in [('normal',9),('halloween',12)]:
                cmd('theme '+theme)
                for mood in range(count):
                    cmd('mode '+str(mood));time.sleep(.2);s=state()
                    check(f'{theme} mood {mood}',s['active_clip']==mood and s['theme']==theme)
                check('mode bounds '+theme,cmd('mode '+str(count))=='ERROR command')
            cmd('mode 0');cmd('pet');cmd('pet');cmd('pet');time.sleep(.2);s=state()
            check('tickles',s['tickled'] and s['bats_count']==4)
            cmd('mode 9');cmd('turn 8');check('charge',state()['magic_charge']==8)
            cmd('click');time.sleep(.2);check('cast',state()['casting'] and state()['active_clip']==9)
            capture(p,a.output.parent/'community-spell.png')
            cmd('sleep');check('sleep clears effects',state()['sleeping'] and not state()['casting'])
            cmd('wake');cmd('brightness 100');check('brightness',state()['brightness']==100);cmd('brightness 150')
            for theme in ('normal','halloween'):
                cmd('theme '+theme);previous=state()
                for i in range(10):
                    if theme=='halloween':
                        if i%2:cmd('mode 7');cmd('pet');cmd('pet');cmd('pet')
                        else:cmd('mode 9');cmd('turn 8');cmd('click')
                    time.sleep(3);s=state()
                    fps=(s['frames']-previous['frames'])*1000/(s['uptime_ms']-previous['uptime_ms'])
                    report['samples'].append({'theme':theme,'fps':fps,'free_heap':s['free_heap'],'max_frame_us':s['max_frame_us']})
                    check(theme+' fps >=18',fps>=18)
                    check(theme+' memory and decoder',s['free_heap']>=initial['free_heap']-1024 and s['decode_errors']==0)
                    previous=s
            cmd('theme halloween');report['final']=state()
            check('no reboot',report['final']['uptime_ms']>initial['uptime_ms'])
            report['passed']=True
    finally:
        a.output.write_text(json.dumps(report,indent=2))
        print(json.dumps({'passed':report['passed'],'checks':len(report['checks'])}))
if __name__=='__main__':main()
