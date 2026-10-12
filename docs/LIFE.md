# Vida propia — 3.3.0-life

[English](LIFE.en.md) · [Controles](CONTROLS.md) · [Restauración](INSTALL.md)

Quise que Muse se comportara como un compañero tranquilo. Reutilicé las animaciones
existentes: esta versión no añade modelos, imágenes, red ni almacenamiento persistente.

| Momento en automático | Comportamiento que implementé |
|---|---|
| Arranque, cambio de tema o activar automático | Despierto, tranquilo, contador de inactividad a cero |
| Cada 20–35 s mientras está despierto | Un gesto de 2 s, sin repetir el anterior, y regreso a tranquilo |
| 3 min sin interacción | Tranquilo, sin gestos espontáneos |
| 5 min sin interacción | Bostezo de 2 s y Dormilón con respiración y Z |
| Toque mientras duerme por inactividad | Saludo de 2 s; consumo el contacto completo, incluida su liberación |
| Pulsación breve mientras duerme por inactividad | Saludo, conservando automático |
| Rueda mientras duerme | Despertar y seleccionar inmediatamente la expresión |

En normal alterno curioso, pensando, feliz y saludo; en Halloween, curioso,
travieso, risita y saludo. Conservo el brillo durante el sueño visible. El reposo
del botón de 1–3 segundos sigue apagando la pantalla; mantener más de tres cambia
el tema una sola vez. Una pulsación breve con pantalla apagada solo la enciende.

La rueda conserva la selección manual indefinida en normal. En Halloween mantengo
la selección durante diez segundos y después vuelvo a automático despierto y
tranquilo. Las reacciones en curso retrasan ese retorno y las rutinas: una caricia,
un abrazo, las cosquillas o un hechizo terminan antes de iniciar otro gesto.
Elegir una expresión o cambiar el tema conserva la cancelación explícita de efectos.

Reinicio la inactividad con las interacciones, nunca con `status`, capturas ni
cambios internos de animación. El contacto sostenido impide iniciar el sueño;
al soltar reinicio el contador. `touch X Y` y `release` funcionan en ambos temas;
en normal también permiten probar la mirada. `pet` es un contacto instantáneo.
Las expresiones de sueño seleccionadas manualmente siguen siendo manuales.

## Diagnóstico y pruebas

En `status` expongo `life_state`, `idle_ms` y `spontaneous_active`. Distingo
`manual`, `awake`, `relaxed`, `yawning`, `asleep`, `greeting` y `screen_off`.

```sh
python -m unittest discover -s tests -v
python tools/diagnose.py --port PORT "selftest life"
python tools/life_test.py --port PORT --output local/life-test.json
```

El último comando tarda algo más de treinta minutos: primero comprueba controles,
después mide quince minutos continuos por tema sin capturas. Durante esa medición
no toques el Dial; el programa verifica los contadores de entradas físicas. Guarda
un registro incremental y un informe final en `local/`, excluidos de Git.
Compruebo por separado los controles físicos. Publico los resultados concretos,
sin confundir simulaciones USB con confirmaciones físicas, en [Validación](VALIDATION.md).

Pruebo los límites exactos y el desbordamiento del reloj en una máquina de estados
con tiempo y azar controlados. `selftest life` ejecuta esos casos sin alterar el
reloj real ni las rutinas activas. No añadí comandos para acelerar el dispositivo.

## Instalación y regreso a 3.2.1

Conservé el esquema de particiones, los índices `mode` y los recursos gráficos.
El instalador verifica hashes y crea un respaldo completo privado antes de escribir.
Para volver exactamente a tu estado anterior uso:

```sh
python tools/flash.py restore --backup RUTA_DEL_RESPALDO --port PORT
```

El restaurador comprueba identidad y hashes y también respalda el estado que va a
sustituir. No publiques esos respaldos. También mantengo la
[release 3.2.1](https://github.com/Khiggins93/musedial/releases/tag/v3.2.1-dreams)
con sus binarios e instrucciones. No requiere recompilar.
