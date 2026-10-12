# Install, back up and restore

[Español](INSTALL.md)

Use the original 8 MiB M5Stack Dial. `--device m5stack-dial` means you physically identified the model; software can check the chip, flash capacity and security configuration, not the screen/pin wiring. Secure Boot and encrypted flash configurations are rejected.

Install Python **3.12**, download and extract the release ZIP, then open a terminal **inside its extracted directory**. Arduino and Blender are not needed for binary installation.

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

Below, `python` means your environment's executable. Replace `PORT` with the discovered port, such as `COM7`, `/dev/ttyACM0` or `/dev/cu.usbmodem...`. Close serial monitors first.

```sh
python tools/flash.py verify --release .
python tools/flash.py install --release . --port PORT --device m5stack-dial
```

The installer validates hashes, fixed offsets, partition layout, size limits and resource CRC. It reads the complete existing flash in sectors, compares the device digest and saves a verified **private** backup in `backups/DATE-ID/` before writing; allow several minutes for this read. Keep it: it may contain credentials or personal configuration. A failed backup prevents installation; reset the board to boot the previous program before retrying.

Installation writes the bootloader, partition table, boot initialization, application and Halloween resources. NVS/SPIFFS ranges are retained, but the second application slot becomes resource storage: **no OTA**. No full-flash image containing someone else's data is distributed. Boot starts in normal mode; hold the button longer than three seconds for Halloween.

## Restore

```sh
python tools/flash.py restore --backup backups/DATE-ID --port PORT
```

Only a complete 8 MiB backup with matching SHA-256 and device MAC is accepted. The current state is backed up first. Full restoration replaces all flash, including configuration. To install another release, use that release's package and installation command without recompiling. Never attach full backups to public issues.

## Troubleshooting

- Missing port: use a data cable; check the port again after reset. For recovery, follow M5Stack's Dial/Stamp-S3 bootloader instructions.
- Access denied: close serial monitors and wait for flashing to finish. On Linux configure your distribution's serial-device permissions.
- Missing Halloween: `status` reports `halloween_ready` and `asset_error`; reinstall the complete package if resources are absent/corrupt.
- Sleeping display: touch or short press to wake. Persistent black screen: confirm the board model and restore your backup.
- Allow startup after flashing before diagnostics. Do not disconnect while writing.

Windows is locally tested. Linux CI checks build/tests without hardware; macOS commands are documented but not physically tested there.
