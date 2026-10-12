# Third-party notices / Avisos de terceros

The project does not relicense its dependencies. Exact source revisions are in `dependencies.lock.json`; `tools/bootstrap.py` downloads them from their upstream repositories.

| Component | Source | Licensing / notices |
|---|---|---|
| M5Unified 0.2.25 | https://github.com/m5stack/M5Unified | MIT; full notice in `licenses/M5Unified.txt` |
| M5GFX 0.2.32 | https://github.com/m5stack/M5GFX | MIT plus upstream per-file notices; `licenses/M5GFX.txt` |
| M5Dial 1.0.3 | https://github.com/m5stack/M5Dial | Pinned revision has no top-level LICENSE; retain upstream per-file notices; no blanket Apache/MIT claim is made for this wrapper |
| Encoder inside M5Dial | https://www.pjrc.com/teensy/td_libs_Encoder.html | Paul Stoffregen / PJRC, MIT-style notice in `licenses/Encoder.txt` |
| MFRC522 inside M5Dial | https://github.com/arozcan/MFRC522-I2C-Library | Header declares public domain; RFID is disabled in this firmware |
| Arduino-ESP32 3.3.2 | https://github.com/espressif/arduino-esp32/tree/3.3.2 | LGPL-2.1 and separately licensed bundled ESP-IDF components; consult upstream source/license files |
| esptool 5.1.0 | https://github.com/espressif/esptool | GPL-2.0-or-later; installed separately through pip |
| pyserial 3.5 | https://github.com/pyserial/pyserial | BSD-3-Clause; installed separately |
| Pillow 12.3.0 | https://github.com/python-pillow/Pillow | HPND and bundled component notices; installed separately |
| Blender 5.2.1 | https://www.blender.org | GPL; separately installed rendering tool, not bundled |

M5GFX's `JD_BAYER` is changed from 1 to 0 to disable ordered JPEG dithering. No other dependency source changes are intended. Its upstream copyright notices remain intact.

El código del SDK Muse y las fotografías externas se excluyen de esta publicación. Los scripts de escena y los recursos generados son una recreación propia, no los assets originales de Meta. Véase `NOTICE` y `docs/ASSETS.md`.
