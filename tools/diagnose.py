"""Inspect the running MuseDial firmware and capture its real framebuffer."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import serial
from PIL import Image


def port_open(port_name):
    port = serial.Serial()
    port.port, port.baudrate, port.timeout = port_name, 115200, 2
    port.dtr, port.rts = False, False
    port.open()
    return port


def request(port, command, timeout=5):
    port.reset_input_buffer()
    port.write((command + "\n").encode())
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        line = port.readline().decode(errors="replace").strip()
        if line.startswith('{"firmware"'):
            if command == "status":
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    port.write(b"status\n")
                    continue
        elif line.startswith(("OK ", "ERROR ")):
            return line
    raise TimeoutError(command)


def capture(port, output):
    port.reset_input_buffer()
    port.write(b"snapshot\n")
    until = time.monotonic() + 6
    while time.monotonic() < until:
        if port.readline().startswith(b"FRAME 240 240 RGB565LE 115200"):
            break
    else:
        raise TimeoutError("No frame header")
    data = bytearray()
    until = time.monotonic() + 20
    while len(data) < 115200 and time.monotonic() < until:
        data.extend(port.read(min(4096, 115200 - len(data))))
    if len(data) != 115200:
        raise RuntimeError(f"Incomplete capture: {len(data)} bytes")
    end = port.read_until(b"FRAME_END\r\n")
    if b"FRAME_END" not in end:
        raise RuntimeError("Missing capture trailer")
    pixels = bytearray()
    for i in range(0, len(data), 2):
        c = data[i] | data[i + 1] << 8
        r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
        pixels.extend(((r * 255 + 15) // 31, (g * 255 + 31) // 63, (b * 255 + 15) // 31))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.frombytes("RGB", (240, 240), bytes(pixels)).save(output)
    return {"file": str(output), "bytes": len(data), "sha256_rgb565": hashlib.sha256(data).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="status")
    parser.add_argument("--capture")
    parser.add_argument("--port", required=True)
    args = parser.parse_args()
    with port_open(args.port) as port:
        print(json.dumps(capture(port, args.capture) if args.capture else request(port, args.command), ensure_ascii=False))
