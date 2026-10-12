"""Strict resource and partition validation shared by packaging and recovery."""
import hashlib, struct, zlib

def partition_image(halloween=False):
    rows = [('nvs', 1, 2, 36864, 20480), ('otadata', 1, 0, 57344, 8192), ('app0', 0, 16, 65536, 3342336), ('halloween', 1, 64, 3407872, 3342336) if halloween else ('app1', 0, 17, 3407872, 3342336), ('spiffs', 1, 130, 6750208, 1572864), ('coredump', 1, 3, 8323072, 65536)]
    entries = b''.join((struct.pack('<HBBII16sI', 20650, t, s, o, n, name.encode(), 0) for name, t, s, o, n in rows))
    return (entries + b'\xeb\xeb' + b'\xff' * 14 + hashlib.md5(entries).digest()).ljust(3072, b'\xff')

def layout(data):
    if data == partition_image(False):
        return 'legacy'
    if data == partition_image(True):
        return 'halloween'
    raise ValueError('Unknown partition layout; refusing flash')

def validate_assets(data):
    if not len(data) >= 48:
        raise ValueError('Truncated header')
    magic, fmt, clips, frames, w, h, fps, total, jpeg, spans, crc = struct.unpack_from('<8s10I', data)
    if not (magic == b'HWEEN3\x00\x00' and fmt == 1 and (clips == 12) and (frames in (32, 40))):
        raise ValueError('Unsupported header')
    if not ((w, h, fps) == (192, 192, 20) and total == len(data) and (total <= 3 * 1024 * 1024)):
        raise ValueError('Size mismatch')
    n = clips * frames
    if not (spans == 48 + 4 * (n + 1) and jpeg == spans + n * 384 and (jpeg < total)):
        raise ValueError('Invalid ranges')
    if not zlib.crc32(data[48:]) == crc:
        raise ValueError('CRC mismatch')
    offsets = struct.unpack_from('<' + 'I' * (n + 1), data, 48)
    if not (offsets[0] == 0 and offsets[-1] == total - jpeg):
        raise ValueError('Invalid offsets')
    for a, b in zip(offsets, offsets[1:]):
        if not (a + 2 < b <= total - jpeg and data[jpeg + a:jpeg + a + 2] == b'\xff\xd8'):
            raise ValueError('Invalid JPEG entry')
    for a, b in zip(data[spans:jpeg:2], data[spans + 1:jpeg:2]):
        if not (a == 255 and b == 0 or 0 <= a <= b < 192):
            raise ValueError('Invalid silhouette')
    return {'frames': frames, 'clips': clips, 'bytes': total, 'sha256': hashlib.sha256(data).hexdigest()}
