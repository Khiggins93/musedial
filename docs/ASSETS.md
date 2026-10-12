# Recursos y procedencia / Assets and provenance

The models are procedural fan-art recreations visually inspired by Muse. They are not Meta's original model or animation assets. External reference photographs and the old pixel avatar implementation are excluded.

`assets/render_avatar.py` builds the cream character with nine 40-frame clips. `assets/render_halloween.py` builds the segmented orange hood, curved stem, cream face, violet cape and glowing belly with twelve 40-frame clips. Both generate geometry, materials, lighting and animation in Blender; corresponding `.blend` scenes are included for inspection.

Normal animation JPEGs are in `firmware/MuseDial/avatar_frames.cpp`. `assets/halloween.bin` is a public, generated animation-only resource: it contains no device flash backup, NVS, MAC, credentials or account data. Its SHA-256 is pinned in `dependencies.lock.json`.

The Halloween concept was developed with AI-assisted image ideation and then rebuilt procedurally. The concept/reference photographs are not required to regenerate the scene and are not included. The screenshots in `docs/images/` show the firmware's actual framebuffer.

Project-authored scripts and original contributions are licensed as described in `NOTICE`; no rights to third-party characters or trademarks are granted. Preserve attribution and avoid representing forks as official Muse, Meta or M5Stack products.

Los renders intermedios se generan localmente y no se suben al repositorio. Los scripts reproducen las escenas y poses; la reproducción byte a byte puede variar entre versiones/plataformas de Blender. Los recursos publicados y sus hashes permiten instalar exactamente cada release sin volver a renderizar.
