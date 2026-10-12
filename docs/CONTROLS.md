# Controles / Controls

**Arranque / Startup:** normal, brillo/brightness 150/255, automático/automatic. No preferences are persisted. Sin red, audio ni RTC / no network, audio or RTC.

| Acción / Input | Comportamiento / Behavior |
|---|---|
| Hold >3000 ms | Toggle theme exactly once while held; wake, reset effects, enable auto. Release does nothing else. |
| Release at 1000–3000 ms | Toggle sleep; display does not sleep while still holding. |
| Release before 1000 ms | Toggle auto. If asleep, only wake. During charge: cast only if full; during casting: consume click. |
| Normal wheel | Select expression indefinitely; auto off. |
| Halloween wheel | Select for 10 seconds then resume auto. At HECHIZO, further turns charge instead of selecting. |
| Charge / Carga | Eight detents in either direction; expires 10 seconds after last turn. Short press at full charge casts for 6 seconds. Wheel/click during cast are consumed. Wait for charge timeout to resume selection. |
| Touch / Toque | Wake and pet; normal gestures described below, four Halloween bats for 5 seconds. |
| Triple touch / Tres toques | At most 900 ms between taps: 5-second Halloween tickles, laugh and faster wavy bat paths. More taps restart duration; no new objects accumulate. |

Theme changes, selecting another mood and sleep clear new effects. Changing theme enables auto. Automatic expressions advance every 16 seconds in normal and 8 seconds in Halloween, deferring while petting or casting.

## Caricias normales / Normal companionship

En el tema normal añadí estas interacciones sin cambiar la selección de expresiones con la rueda:

- Toca suavemente y desliza el dedo: la mirada sigue nueve zonas de la pantalla; no presiones el botón mecánico.
- Al soltar, sonríe. Otra caricia antes de seis segundos provoca una reacción de cariño; la tercera da un abrazo. Para ver las etapas, deja más de 650 ms entre toques.
- Tres toques rápidos (hasta 650 ms entre ellos, cada uno menor de 450 ms) provocan cosquillas.
- Mantén contacto táctil durante dos segundos y suelta para pedir un abrazo directamente. Esto es distinto de mantener pulsado el botón mecánico, que conserva reposo/cambio de tema.
- Los gestos duran 1,6 segundos; el abrazo, dos segundos. Tras seis segundos sin contacto se reinicia la progresión. Cambiar tema, girar la rueda o entrar en reposo cancela la reacción.

In normal mode, lightly touch and drag to choose among nine 3D gaze directions. Release for a smile; repeat within six seconds for affection and then a hug (space releases more than 650 ms apart). Three quick taps trigger tickles. Hold **touch contact**, without clicking the mechanical button, for two seconds and release for a hug. Gestures last 1.6 seconds, hugs two seconds. Theme/mood/sleep changes cancel them; no preferences are written to flash.

## Expresiones / Expressions

Normal `mode 0..8`: TRANQUILO, CURIOSO, PENSANDO, ANIMADO, DORMILON, FELIZ, SALUDO, SORPRESA, SUENO.

Halloween `mode 0..11`: TRANQUILO, CURIOSO, TRAVIESO, SALUDO, RISITA, SORPRESA, BOO, CARCAJADA, BAILE, HECHIZO, DORMILON, BOSTEZO.

## USB

115200 baud, newline-terminated commands. Use the repository's diagnostic tool:

```sh
python tools/diagnose.py --port PORT status
python tools/diagnose.py --port PORT "theme halloween"
python tools/diagnose.py --port PORT --capture local/screen.png
```

Commands: `status`, `snapshot`, `theme normal`, `theme halloween`, `mode N`, `pet`, `sleep`, `wake`, `auto on`, `auto off`, `brightness 20..255`, `turn -100..100` (nonzero), `click`, `selftest input`, `selftest assets`, `selftest play`, `selftest companion`, `touch X Y` (normal only, coordinates 0–239), `release` (normal only). Repeated `touch` commands move an existing simulated contact. `pet` simulates an immediate centered touch/release.

`turn` and `click` use the physical input handlers but do not prove electrical operation. `snapshot` streams a 240 × 240 RGB565LE framebuffer and pauses rendering; exclude it from fps measurements.

`status` is JSON: version, theme, mood, active_clip, animation, automatic, sleeping, brightness, free_heap, min_heap, uptime_ms, frames, max_frame_us, decode_errors, halloween_ready, asset_error, bats_active/count, temporary_selection, magic_charge (0–8), casting, tickled and physical event counters. Normal interactions add `companion` (MIRADA, SONRISA, CARINO, ABRAZO, COSQUILLAS or NINGUNO), `affection` (0–3), `gaze_x` and `gaze_y` (-1–1). `active_clip`/`animation` retain the selected base expression; `companion` identifies its temporary override. These counters are not incremented by USB simulations.

Optional hardware regression (changes modes and leaves Halloween awake/automatic): `python tools/hardware_test.py --port PORT`. It checks all expressions, USB interactions and 30 seconds per theme; its output stays in ignored `local/`. Do not touch the controls during timed measurements. This does not replace physical confirmation.
