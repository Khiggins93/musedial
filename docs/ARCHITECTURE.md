# Arquitectura / Architecture

Arduino-ESP32 application using M5Dial/M5Unified/M5GFX; entirely offline. ESP32-S3 internal RAM holds a 240 × 240 RGB565 framebuffer (115200 bytes). The renderer reads 192 × 192 baseline JPEG frames at 20 fps and decodes in blocks; no PSRAM required. Normal frames are compiled into application flash. Halloween data is mapped from flash and checked before use. Sprites/particles use fixed-size state without per-effect allocation.

Hardware pins are provided by the pinned vendor drivers: display DC4/MOSI5/SCLK6/CS7/RESET8/BL9; I²C 11/12; touch interrupt14; encoder41/40; button21. No external wiring is required. Audio, networking, IMU, RTC and RFID features are disabled by this sketch.

## Flash map (8 MiB)

| Partition | Offset | Size |
|---|---:|---:|
| NVS | 0x9000 | 0x5000 |
| OTA boot metadata | 0xe000 | 0x2000 |
| Application | 0x10000 | 0x330000 |
| Halloween data | 0x340000 | 0x330000 |
| SPIFFS | 0x670000 | 0x180000 |
| Core dump | 0x7f0000 | 0x10000 |

The partition table is at 0x8000. Halloween replaces the second OTA application slot; no firmware OTA updater is implemented. Existing data ranges are retained during installation; full backup restoration replaces everything.

Halloween format: 48-byte little-endian header (`<8s10I`), magic `HWEEN3\0\0`, format1, twelve clips, 40 or 32 frames per clip, 192 × 192, 20 fps, total length, JPEG offset, silhouette offset, payload CRC32. Followed by `(frame_count+1)` uint32 JPEG offsets, 384 silhouette bytes per frame (192 inclusive xmin/xmax pairs, 255/0 empty), then JPEG data. The package is capped at 3 MiB; quality selection is 82, 80, 78, 76, then a 32-frame fallback. Current resource: 40 frames, quality80, 3136959 bytes.

Firmware validates dimensions, bounds, CRC, monotonic offsets, JPEG markers and row spans. Invalid data prevents Halloween activation while normal remains operational. Four bats switch apparent front/back depth using the silhouette mask. Ghosts and sparks are foreground overlays.

I use pure state machines in `button_actions.h`, `play_effects.h`, `companion.h` and `life.h` for input timing, effect priority and unsigned clock wrap behavior. In `life.h` I inject time and random values for deterministic tests; the firmware supplies `millis()` and `esp_random()`. Pending base-clip changes never clear reaction effects. I track inactivity separately from animation start times and retain a consumed-touch latch until release. Screen-off overrides the reported life state and suspends routines. No interaction preferences are written to flash. [Life routines](LIFE.en.md).

Normal companionship adds 145 flash-resident JPEGs (nine gaze poses, 32 smile, 32 affection, 40 hug, 32 tickle frames). It reuses the existing framebuffer and block decoder, with no extra canvas or heap allocation. Gaze uses nine pre-rendered directions with boundary hysteresis, not continuous real-time 3D. Finite gesture clips ease in and out; switching from an arbitrary base expression can still produce a visible cut.
