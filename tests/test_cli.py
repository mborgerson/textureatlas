import json
import os
import subprocess
import sys
import tempfile
import unittest

from contextlib import contextmanager
from pathlib import Path

import PIL.Image as Image


@contextmanager
def pushd(target):
    original = os.getcwd()
    try:
        os.chdir(target)
        yield
    finally:
        os.chdir(original)


samples_path = Path(__file__).resolve().parent.parent / "samples"


class TestCli(unittest.TestCase):

    def test_simple(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with pushd(temp_dir):
                subprocess.check_call([sys.executable, "-m", "textureatlas", "-mf", "json"] + list(samples_path.glob("*.png")))
                with open("atlas.map", "r", encoding="utf-8") as file:
                    map = json.load(file)
                    assert len(map) == 6

                image = Image.open("atlas.png")
                width, height = image.size
                image.close()

                assert 128 < width <= (128+512)
                assert 128 < height <= (128+512)


if __name__ == '__main__':
    unittest.main()
