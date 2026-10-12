"""Real-clock life regression: 15 continuous minutes per theme, no captures.

Do not touch the device during this automatic run. Physical confirmation is
recorded separately. All evidence goes to ignored local/ by default.
"""
import argparse
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from diagnose import port_open, request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, default=Path('local/life-test.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'checks': [], 'themes': [], 'physical_confirmation': False,
              'started_bogota': datetime.now(timezone(timedelta(hours=-5))).isoformat()}
    stream = args.output.with_suffix('.jsonl')

    def check(name, ok):
        report['checks'].append({'name': name, 'passed': bool(ok)})
        if not ok:
            raise AssertionError(name)

    try:
        with port_open(args.port) as port, stream.open('w', encoding='utf-8') as log:
            def cmd(command):
                result = request(port, command)
                if isinstance(result, str) and result.startswith('ERROR'):
                    raise AssertionError(command + ': ' + result)
                return result

            def state():
                return cmd('status')

            initial = state()
            check('life version', initial['version'] == '3.3.0-life')
            for name in ('input', 'life', 'companion', 'play', 'assets'):
                check('selftest ' + name, cmd('selftest ' + name) == 'OK selftest ' + name)
            # Regression outside the timed soak, including temporary selection.
            cmd('theme normal'); cmd('mode 4'); time.sleep(.2)
            check('manual dream is not life sleep', state()['life_state'] == 'manual')
            cmd('pet'); time.sleep(.2)
            check('manual dream can be petted', state()['companion'] == 'SONRISA')
            cmd('auto on'); time.sleep(.2)
            check('auto preserves current reaction', state()['companion'] == 'SONRISA')
            time.sleep(1.7)
            check('reaction returns to calm', state()['mood'] == 0)
            cmd('sleep'); check('screen off is separate', state()['life_state'] == 'screen_off')
            cmd('click'); time.sleep(.1)
            check('click only wakes display', state()['automatic'] and not state()['sleeping'])
            cmd('theme halloween'); cmd('mode 2'); time.sleep(9.7)
            check('Halloween selection still manual', not state()['automatic'])
            time.sleep(.5)
            check('Halloween returns awake/calm', state()['automatic'] and state()['mood'] == 0)
            cmd('mode 9'); cmd('turn 8'); cmd('click'); time.sleep(.2)
            check('spell has priority', state()['casting'] and state()['active_clip'] == 9)
            time.sleep(6)
            check('spell returns to calm', not state()['casting'] and state()['mood'] == 0)

            previous_global = state()
            for theme in ('normal', 'halloween'):
                cmd('theme ' + theme); time.sleep(.15)
                start = time.monotonic()
                baseline = previous = fps_baseline = state()
                summary = {'theme': theme, 'samples': 0, 'fps_min': 100.0,
                           'heap_min': baseline['free_heap'], 'heap_max': baseline['free_heap'],
                           'states': [], 'first_sleep_ms': None, 'wakes': 0}
                report['themes'].append(summary)
                phase = 0
                held_at = None
                last_spontaneous = None
                was_spontaneous = False
                while time.monotonic() - start < 900:
                    time.sleep(.5)
                    s = state()
                    check('no reboot', s['uptime_ms'] > previous_global['uptime_ms'])
                    check('decoder clean', s['decode_errors'] == 0)
                    check('visible unchanged brightness', not s['sleeping'] and s['brightness'] == baseline['brightness'])
                    check('heap stable', s['free_heap'] == baseline['free_heap'])
                    check('no physical interruption', all(s[k] == baseline[k] for k in ('touch_events', 'button_events', 'encoder_steps')))
                    # Five-second windows avoid single-frame quantization at 0.5 s.
                    fps = None
                    if s['uptime_ms'] - fps_baseline['uptime_ms'] >= 5000:
                        fps = (s['frames'] - fps_baseline['frames']) * 1000 / (s['uptime_ms'] - fps_baseline['uptime_ms'])
                        check('fps >=18 without captures', fps >= 18)
                        summary['fps_min'] = min(summary['fps_min'], fps)
                        fps_baseline = s
                    summary['samples'] += 1
                    summary['heap_min'] = min(summary['heap_min'], s['free_heap'])
                    summary['heap_max'] = max(summary['heap_max'], s['free_heap'])
                    if s['life_state'] not in summary['states']:
                        summary['states'].append(s['life_state'])
                        print(theme, s['life_state'], 'idle_ms', s['idle_ms'], flush=True)
                    if s['spontaneous_active'] and not was_spontaneous:
                        allowed = (1, 2, 5, 6) if theme == 'normal' else (1, 2, 4, 3)
                        check('eligible nonrepeating gesture', s['mood'] in allowed and s['mood'] != last_spontaneous)
                        last_spontaneous = s['mood']
                    was_spontaneous = s['spontaneous_active']
                    if phase == 0 and s['life_state'] == 'asleep':
                        summary['first_sleep_ms'] = s['idle_ms']
                        check('full inactivity cycle', 302000 <= s['idle_ms'] < 304000)
                        check('sleep has Z and auto', s['dreaming'] and s['automatic'])
                        cmd('touch 120 120'); held_at = time.monotonic(); phase = 1
                    elif phase == 1:
                        check('wake touch consumes affection', s['companion'] == 'NINGUNO' and not s['bats_active'])
                        if time.monotonic() - held_at >= 3:
                            cmd('release'); phase = 2; summary['wakes'] += 1
                    elif phase == 2:
                        check('wake release does not hug', s['companion'] == 'NINGUNO' and not s['bats_active'])
                        cmd('pet'); phase = 3
                    elif phase == 3:
                        check('later touch reacts', s['companion'] == 'SONRISA' if theme == 'normal' else s['bats_active'])
                        phase = 4
                    elif phase == 4 and s['life_state'] == 'asleep':
                        cmd('click'); phase = 5; summary['wakes'] += 1
                    elif phase == 5:
                        check('button wake keeps auto', s['automatic'] and s['life_state'] == 'greeting')
                        cmd('turn 1'); phase = 6
                    elif phase == 6:
                        expected = 7 if theme == 'normal' else 4
                        check('wheel selects immediately', s['mood'] == expected and not s['automatic'])
                        cmd('auto on'); phase = 7
                    previous = previous_global = s
                    log.write(json.dumps({'theme': theme, 'elapsed_s': time.monotonic()-start, 'fps': fps, **s}) + '\n')
                    log.flush()
                summary['duration_s'] = time.monotonic() - start
                check(theme + ' all wake phases', phase == 7)
                check(theme + ' all life states', all(x in summary['states'] for x in ('awake', 'relaxed', 'yawning', 'asleep', 'greeting')))
                print(json.dumps(summary), flush=True)
            cmd('theme normal'); time.sleep(.1)
            report['final'] = state()
            check('final normal awake auto', report['final']['life_state'] == 'awake' and report['final']['automatic'])
            report['passed'] = True
    finally:
        report['ended_bogota'] = datetime.now(timezone(timedelta(hours=-5))).isoformat()
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'passed': report['passed'], 'checks': len(report['checks'])}), flush=True)


if __name__ == '__main__':
    main()
