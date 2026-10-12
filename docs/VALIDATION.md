# Validación / Validation

Here I document the results measured on my Dial separately from automated build checks. For the public version, I kept the animation assets and interaction state machines from my private 3.1 baseline and removed the unused SDK pixel renderer.

## Baseline 3.1 (not a new public-build measurement)

On the original M5Stack Dial: 93 functional regression checks, five minutes alternating spells/tickles, 19.874–19.980 fps, 218592 bytes free heap throughout, zero decode errors. Physical controls were confirmed on earlier versions; USB simulations are not physical confirmation of this public build.

## Community 3.1.1

I collected these measurements on 2026-10-12 (America/Bogota), using the Windows-built community application on my original M5Stack Dial:

| Check | Result |
|---|---|
| USB hardware regression | 74 checks passed: all 9 normal/12 Halloween expressions, effects, brightness, sleep and input selftests |
| Timed coverage | 30 seconds normal + 30 seconds Halloween; captures excluded |
| Frame rate | 19.549–19.994 fps |
| Free heap | 219104 bytes, constant throughout the measured intervals |
| Maximum frame draw | 40609 microseconds |
| Decoder errors / restarts during the test | 0 / 0 |
| Blender preview regeneration | 9 normal + 12 Halloween images at 192 × 192 |
| Local host tests | 13 passed, native C++ test skipped because g++ was unavailable |
| Clean Linux GitHub Actions | All 14 tests passed, including C++ input boundaries; build and package verification passed |
| Extracted release ZIP | Every SHA256SUMS entry and standalone installer verification passed |

The 8 MiB original flash was backed up and compared against the device digest before installation. Large native USB read bursts stalled during initial attempts, before any write; the published installer uses sector-sized reads, per-read esptool digest validation, identity-checked reconnects and a final whole-flash digest. Unit tests cover reconnect interruption and wrong-device rejection. Release notes record the final restoration exercise.

The repository test suite validates resource checksums, corrupt/truncated images, offset bounds, exact layouts, manifest path/offset rejection, device-bound backups, palette preservation and the C++ input state machines. A host without g++ skips only the native C++ test; the device selftests and Linux CI cover it separately.

These are USB/software checks on real hardware, not a new physical-user confirmation of wheel/touch/button operation. The longer five-minute baseline measurement above belongs to 3.1 and is not attributed to this public build. Windows hardware flashing and Linux clean compilation were verified; macOS hardware operation was not tested.

I have excluded raw local logs, device identifiers, flash backups and personal paths from the repository. You can inspect the CI workflow output in the public Actions tab.
