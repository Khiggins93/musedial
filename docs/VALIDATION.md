# Validación / Validation

This document separates measured hardware results from automated build checks. The public code preserves the animation assets and interaction state machines of the private 3.1 baseline, with the unused SDK pixel renderer removed.

## Baseline 3.1 (not a new public-build measurement)

On the original M5Stack Dial: 93 functional regression checks, five minutes alternating spells/tickles, 19.874–19.980 fps, 218592 bytes free heap throughout, zero decode errors. Physical controls were confirmed on earlier versions; USB simulations are not physical confirmation of this public build.

## Community 3.1.1

Public build/device/CI results are added after validation. The repository test suite validates resource checksums, corrupt/truncated images, offset bounds, exact layouts, manifest path/offset rejection, device-bound backups, palette preservation and the C++ input state machines. A host without g++ skips only the native C++ test; the device selftests and Linux CI cover it separately.

Hardware tests must record chip/display readiness, resources, both themes, all expressions, effects, memory, frame timing and reboot continuity. Captures pause rendering and are excluded from frame-rate intervals. Physical user confirmation is recorded separately.

Raw local logs, device identifiers, flash backups and personal paths are intentionally excluded. CI workflow output is available in the public Actions tab.
