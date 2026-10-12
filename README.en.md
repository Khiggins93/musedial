# MuseDial 🎃

[Español](README.md) · [Install](docs/INSTALL.en.md) · [Build](docs/BUILD.en.md) · [Controls](docs/CONTROLS.md)

An animated companion for **M5Stack Dial**: a prerendered 3D character, petting, Halloween costumes, orbiting bats, tickles and wheel-charged spells. Entirely **offline**: no account, SDK token, microphone or speaker required.

<p><img src="docs/images/normal.png" width="240" alt="Normal character"><img src="docs/images/spell.png" width="240" alt="Halloween spell"><img src="docs/images/tickles.png" width="240" alt="Tickles"></p>

An independent community project by **Khiggins93**, visually inspired by Muse. Not an official product or affiliated with Meta or M5Stack. It does not contain Muse's AI models, backend or apps.

## Hardware

- Original M5Stack **Dial**, Stamp-S3 / ESP32-S3, 8 MiB flash, no PSRAM.
- Integrated 240 × 240 round touchscreen, rotary encoder and button.
- USB-C **data** cable and Windows, Linux or macOS computer. USB power; no additional wiring or peripherals.
- Python 3.12 to install release binaries. Git and Arduino CLI 1.5.1 to compile; Blender 5.2.1 only to regenerate animations.

Only the original **M5Stack Dial** has been physically tested. An ESP32-S3 with 8 MiB flash is not automatically a compatible board. [Official hardware documentation](https://docs.m5stack.com/en/core/Dial).

## Get started

Download the ZIP from the [latest release](https://github.com/Khiggins93/musedial/releases/latest), extract it and follow the [installation/backup guide](docs/INSTALL.en.md). The installer makes a private full-flash backup before writing. Hold the button **longer than three seconds** to enter Halloween.

You can also [build from source](docs/BUILD.en.md). Committed animation resources mean Blender is optional.

## Play

| Input | Behavior |
|---|---|
| Hold >3 seconds | Switch theme once, wake and enable automatic expressions |
| Release between 1 and 3 seconds | Toggle sleep |
| Short press | Toggle automatic; when asleep, only wake |
| Wheel | Select an expression; Halloween resumes automatic after 10 seconds |
| Touch | Pet; four orbiting bats in Halloween |
| Three quick touches | Five seconds of Halloween tickles |
| Select HECHIZO, turn 8 further detents, short press | Six-second spell with sparkles and three ghosts |

[Complete controls and USB commands](docs/CONTROLS.md). Nine normal and twelve Halloween expressions. Interaction preferences are not written to flash; reboot starts in normal mode.

## Implementation and licensing

Blender renders 192 × 192 sequences at 20 fps. Block-based JPEG decoding works without PSRAM; lightweight sprites provide the effects. Halloween replaces the second application slot with a resource partition: **OTA is unavailable**. Invalid Halloween resources leave normal mode operational.

[Architecture](docs/ARCHITECTURE.md) · [Assets](docs/ASSETS.md) · [Validation](docs/VALIDATION.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md).

Original code is licensed under [Apache 2.0](LICENSE). See [NOTICE](NOTICE) and [third-party notices](THIRD_PARTY_NOTICES.md). No rights to third-party characters or trademarks are granted. External reference photographs and original SDK avatar files are not distributed.
