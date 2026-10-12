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
| Touch / Toque | Wake and pet; happy normal expression for 4 seconds, four Halloween bats for 5 seconds. |
| Triple touch / Tres toques | At most 900 ms between taps: 5-second Halloween tickles, laugh and faster wavy bat paths. More taps restart duration; no new objects accumulate. |

Theme changes, selecting another mood and sleep clear new effects. Changing theme enables auto. Automatic expressions advance every 16 seconds in normal and 8 seconds in Halloween, deferring while petting or casting.

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

Commands: `status`, `snapshot`, `theme normal`, `theme halloween`, `mode N`, `pet`, `sleep`, `wake`, `auto on`, `auto off`, `brightness 20..255`, `turn -100..100` (nonzero), `click`, `selftest input`, `selftest assets`, `selftest play`.

`turn` and `click` use the physical input handlers but do not prove electrical operation. `snapshot` streams a 240 × 240 RGB565LE framebuffer and pauses rendering; exclude it from fps measurements.

`status` is JSON: version, theme, mood, active_clip, animation, automatic, sleeping, brightness, free_heap, min_heap, uptime_ms, frames, max_frame_us, decode_errors, halloween_ready, asset_error, bats_active/count, temporary_selection, magic_charge (0–8), casting, tickled and physical event counters. These counters are not incremented by USB simulations.
