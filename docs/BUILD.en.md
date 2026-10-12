# Build and regenerate assets

[Español](BUILD.md)

Install Git, Python 3.12 and [Arduino CLI 1.5.1](https://github.com/arduino/arduino-cli/releases/tag/v1.5.1) on PATH. Clone the repository and create the Python environment described in [installation](INSTALL.en.md). `python` below means that environment's executable.

```sh
git clone https://github.com/Khiggins93/musedial.git
cd musedial
python -m pip install -r tools/requirements.txt
python tools/bootstrap.py
python -m unittest discover -s tests -v
python tools/build.py
```

Bootstrap installs Arduino-ESP32 3.3.2 and fetches exact M5Dial 1.0.3, M5Unified 0.2.25 and M5GFX 0.2.32 commits. Its only source patch disables JPEG Bayer dithering. `dependencies.lock.json` records versions, FQBN and the Halloween resource hash. Do not copy dependencies from a private workspace.

Build creates `dist/musedial-3.3.0-life/` and a ZIP with fixed flash segments, manifest, SHA256SUMS, installer and notices. It checks size and layout. The full `merged.bin` is not packaged; only its 8192-byte boot initialization segment is extracted.

```sh
python tools/flash.py verify --release dist/musedial-3.3.0-life
python tools/flash.py install --release dist/musedial-3.3.0-life --port PORT --device m5stack-dial
```

## Optional animation regeneration

Use Blender **5.2.1**, CPU rendering; allow several minutes. Replace `blender` with its full executable path if needed.

```sh
blender -b -t 8 -P assets/render_avatar.py -- --force
python assets/pack_frames.py
blender -b -t 8 -P assets/render_halloween.py -- --force
python assets/pack_halloween.py
```

The first pair updates normal firmware assets. The second creates `build/Halloween/halloween.bin`. Review `build/previews/halloween/`, copy the result to `assets/halloween.bin`, explicitly update `assets_sha256` in the lock file, run tests and rebuild.

Generators also save the `.blend` scenes; intermediate PNGs are ignored. `-- --preview --force` renders one pose per expression. Scene and poses are reproducible; Blender/platform differences can alter rendered bytes. Committed resources and their checksums define each binary release.

In PowerShell use `& 'path with spaces/blender.exe'`. Linux/macOS use the same Python scripts. Linux CI builds and tests without Blender.

### Normal companion gestures (3.2)

I added a separate scene that reuses the original character:

```sh
blender -b -t 8 -P assets/render_companion.py -- --force
python assets/pack_companion.py
```

This produces nine gaze directions and four gestures (145 frames total). Review `build/previews/companion/companion.gif`, update `companion_sha256` in the lock file from `assets.json`, then rebuild. The generated scene is `assets/companion.blend`. The packer enforces a 1 MB budget; the build checks the whole application size.
