import hashlib
import io
import json
import re
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

class CompanionAssets(unittest.TestCase):
    def test_all_frames_are_valid_and_within_flash_budget(self):
        source=(ROOT/'firmware/MuseDial/companion_frames.cpp').read_text()
        offsets=list(map(int,re.search(r'companion_offsets\[146\]=\{([^}]+)',source)[1].split(',')))
        jpeg=bytes(map(int,re.search(r'companion_jpeg\[\]=\{([^}]+)',source)[1].strip().rstrip(',').split(',')))
        self.assertEqual(len(offsets),146)
        self.assertEqual(offsets[0],0)
        self.assertEqual(offsets[-1],len(jpeg))
        self.assertLessEqual(len(jpeg),1000000)
        self.assertEqual(hashlib.sha256(jpeg).hexdigest(),json.loads((ROOT/'dependencies.lock.json').read_text())['companion_sha256'])
        for a,b in zip(offsets,offsets[1:]):
            self.assertLess(a,b)
            with Image.open(io.BytesIO(jpeg[a:b])) as image:
                self.assertEqual(image.size,(192,192))
                image.load()
