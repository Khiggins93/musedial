# Instalar, respaldar y restaurar

[English](INSTALL.en.md)

Usa exclusivamente el M5Stack Dial original de 8 MiB. El parámetro `--device m5stack-dial` indica que verificaste físicamente el modelo; el programa solo puede comprobar chip, capacidad de flash y configuración de seguridad. Secure Boot o cifrado de flash activados se rechazan.

## Preparación

Instala Python **3.12**, descarga el ZIP de la release, extráelo y abre una terminal **dentro de la carpeta extraída**. No ejecutes desde el ZIP. No necesitas Arduino ni Blender para este camino.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r tools/requirements.txt
.venv/Scripts/python.exe -m serial.tools.list_ports
```

Linux/macOS:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python -m serial.tools.list_ports
```

En los comandos siguientes, `python` representa el ejecutable del entorno anterior. Sustituye `PUERTO` por el puerto encontrado: `COM7`, `/dev/ttyACM0` o `/dev/cu.usbmodem...` son ejemplos, no valores fijos. Cierra monitores seriales antes de continuar.

## Instalar

```sh
python tools/flash.py verify --release .
python tools/flash.py install --release . --port PUERTO --device m5stack-dial
```

Se verifican hashes, offsets, límites, tabla de particiones y CRC de recursos. Antes de escribir se lee toda la flash por sectores y se compara su digest con el del dispositivo; esta lectura puede tardar varios minutos. Se guarda en `backups/FECHA-ID/`: **conserva esta carpeta de forma privada**, puede contener configuraciones y credenciales del firmware anterior. Si falla el respaldo, no se escribe el firmware; reinicia el equipo para volver al programa anterior antes de reintentar.

La instalación escribe bootloader, tabla, inicialización de arranque, aplicación y recursos. Conserva los rangos NVS/SPIFFS, pero sustituye el segundo slot de aplicación: no permite OTA. No se distribuye una imagen completa con datos de otro dispositivo. El modelo empieza en normal; mantén pulsado más de tres segundos para Halloween.

## Restaurar el estado anterior

```sh
python tools/flash.py restore --backup backups/FECHA-ID --port PUERTO
```

Solo restaura un respaldo de 8 MiB con hash correcto y MAC coincidente. Antes hace otro respaldo del estado actual. La restauración completa reemplaza toda la flash, incluida la configuración, por el estado guardado.

Para instalar otra release, usa su paquete y el mismo procedimiento de instalación; no necesita recompilación. No publiques ni adjuntes los respaldos a un issue.

## Si algo falla

- Puerto ausente: prueba un cable de datos y otro puerto USB; identifica el puerto de nuevo después de reiniciar. Si el firmware no arranca, entra al cargador siguiendo las instrucciones de M5Stack para el Dial/Stamp-S3.
- Acceso denegado: cierra el monitor serial y espera a que termine el flasher. En Linux revisa permisos del grupo serial de tu distribución; evita ejecutar todo como root.
- Falta Halloween: consulta `status` con las herramientas del repositorio. `halloween_ready=false` o `asset_error` indican recursos ausentes/corruptos; reinstala el paquete completo.
- Pantalla dormida: toque o pulsación breve para despertar. Pantalla negra persistente: confirma el modelo y restaura tu respaldo.
- Tras flashear espera al arranque antes de abrir diagnóstico. No desconectes durante escritura.

Windows se valida localmente. Linux se valida por CI para compilación/pruebas sin hardware; las instrucciones de macOS no implican una prueba física en ese sistema.
