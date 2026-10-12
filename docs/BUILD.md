# Compilar y regenerar

[English](BUILD.en.md)

Instala Git, Python 3.12 y [Arduino CLI 1.5.1](https://github.com/arduino/arduino-cli/releases/tag/v1.5.1), disponibles en PATH. Clona el repositorio y crea el entorno Python como en [instalación](INSTALL.md). En los comandos, `python` es el ejecutable de ese entorno.

```sh
git clone https://github.com/Khiggins93/musedial.git
cd musedial
python -m pip install -r tools/requirements.txt
python tools/bootstrap.py
python -m unittest discover -s tests -v
python tools/build.py
```

`bootstrap.py` instala Arduino-ESP32 3.3.2 y obtiene M5Dial 1.0.3, M5Unified 0.2.25 y M5GFX 0.2.32 por sus commits exactos. Desactiva únicamente el patrón Bayer de JPEG. `dependencies.lock.json` fija las versiones, FQBN y hash del recurso Halloween. No copies bibliotecas desde otro proyecto.

`build.py` genera `dist/musedial-3.3.0-life/` y su ZIP, valida la tabla y tamaños y añade manifiesto, SHA256SUMS, instalador y avisos. No empaqueta la imagen `merged.bin`: esta se usa solo para extraer los 8192 bytes de inicialización `boot_app0.bin`.

```sh
python tools/flash.py verify --release dist/musedial-3.3.0-life
python tools/flash.py install --release dist/musedial-3.3.0-life --port PUERTO --device m5stack-dial
```

## Regenerar animaciones (opcional)

Instala Blender **5.2.1**. El render se hace por CPU; puede tardar varios minutos. `blender` representa su ejecutable completo si no está en PATH.

```sh
blender -b -t 8 -P assets/render_avatar.py -- --force
python assets/pack_frames.py
blender -b -t 8 -P assets/render_halloween.py -- --force
python assets/pack_halloween.py
```

El primer par actualiza los recursos normales incorporados al firmware. El segundo produce `build/Halloween/halloween.bin`: revisa sus previsualizaciones en `build/previews/halloween/`, cópialo a `assets/halloween.bin` y actualiza explícitamente `assets_sha256` del archivo de dependencias con el SHA-256 nuevo. Después ejecuta las pruebas y recompila.

Los generadores crean las escenas `.blend`; los PNG intermedios se ignoran. Usa `-- --preview --force` para renderizar solo una pose de cada expresión. Los scripts reproducen escena y poses; Blender/plataforma pueden cambiar algunos bytes del render. El recurso comprometido en Git y su hash son la referencia binaria de la release.

En Windows PowerShell un ejecutable de Blender con espacios se invoca con `& 'ruta/al/blender.exe'`. En Linux/macOS los mismos scripts usan rutas relativas a su ubicación. CI compila en Linux y ejecuta las pruebas sin necesidad de Blender.

### Gestos del Muse normal (3.2)

Añadí una escena independiente que reutiliza el personaje original:

```sh
blender -b -t 8 -P assets/render_companion.py -- --force
python assets/pack_companion.py
```

Genera nueve miradas y cuatro gestos (145 cuadros en total). Revisa el GIF de `build/previews/companion/`, actualiza `companion_sha256` en el archivo de dependencias con el hash de `assets.json` y recompila. La escena queda en `assets/companion.blend`. El empaquetador impone un presupuesto de 1 MB; la compilación comprueba además el tamaño total de la aplicación.
