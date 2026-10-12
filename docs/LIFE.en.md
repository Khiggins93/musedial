# Life routines — 3.3.0-life

[Español](LIFE.md) · [Controls](CONTROLS.md) · [Restore](INSTALL.en.md)

I wanted Muse to feel like a quiet companion. I reused the existing animations;
this release adds no models, images, networking or persistent preferences.

| Automatic behavior | What I implemented |
|---|---|
| Startup, theme change or enabling auto | Awake and calm; reset inactivity |
| Every 20–35 s while awake | A two-second gesture, never the previous one, then calm |
| Three idle minutes | Calm, without spontaneous gestures |
| Five idle minutes | A two-second yawn, then breathing sleep with Z sprites |
| Touch while idle-asleep | Two-second greeting; consume the entire contact and release |
| Short button press while idle-asleep | Greet, keeping auto enabled |
| Wheel while idle-asleep | Wake and immediately select the requested expression |

I choose curious, thinking, happy and greeting in normal; curious, mischievous,
giggle and greeting in Halloween. Visible sleep keeps brightness unchanged.
The 1–3 second button release still toggles display-off sleep; holding longer
than three seconds changes the theme once. A short press with the display off
only wakes the display.

Normal wheel selection remains manual indefinitely. Halloween selection lasts
ten seconds before returning to awake/calm auto. Active reactions postpone that
return and life routines: petting, hugs, tickles and spells finish first. Explicit
mood/theme selection retains effect cancellation.

I reset inactivity on interactions, never on diagnostics, captures or internal
animation changes. Sustained contact blocks sleep; releasing resets inactivity.
`touch X Y` and `release` work in both themes; normal also supports gaze testing.
`pet` is an instantaneous contact. Manually selected sleepy expressions remain manual.

## Diagnostics and testing

I expose `life_state`, `idle_ms` and `spontaneous_active` in `status`, with states
`manual`, `awake`, `relaxed`, `yawning`, `asleep`, `greeting` and `screen_off`.

```sh
python -m unittest discover -s tests -v
python tools/diagnose.py --port PORT "selftest life"
python tools/life_test.py --port PORT --output local/life-test.json
```

The last command takes slightly over thirty minutes: controls first, then fifteen
continuous minutes per theme without captures. Do not touch the Dial during this
measurement; I check physical input counters. The script writes incremental and
final evidence to ignored `local/`. I verify physical controls separately and
record actual results in [Validation](VALIDATION.md).

I test exact boundaries and clock rollover with injected clock/random values.
`selftest life` runs those cases without changing the live clock or routines.
I added no public time-acceleration command.

## Installation and rollback

I kept partition locations, mode indices and graphic resources unchanged. The
installer checks hashes and makes a private full backup before writing. To restore
the exact previous state:

```sh
python tools/flash.py restore --backup BACKUP_PATH --port PORT
```

The restorer checks device identity and hashes, and backs up the state being
replaced. Keep full backups private. I also preserve the
[3.2.1 release](https://github.com/Khiggins93/musedial/releases/tag/v3.2.1-dreams)
with binaries and installation instructions; no rebuild is needed.
