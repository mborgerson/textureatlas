#!/usr/bin/env python
#
# Copyright (c) 2014-2025 Matt Borgerson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import json
import os.path
import re
import shlex
import struct

from dataclasses import dataclass
from typing import TextIO, BinaryIO

import PIL.Image as Image


@dataclass
class Rect:
    """A two-dimensional object."""

    x: int
    y: int
    width: int
    height: int

    @property
    def perimeter(self) -> None:
        return 2 * (self.width + self.height)


class PackRegion(Rect):
    """A region that Rect objects can be packed into."""

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.subregion_1: PackRegion | None = None
        self.subregion_2: PackRegion | None = None
        self.packable: Rect | None = None

    def pack(self, packable: Rect) -> bool:
        """Pack 2D packable into this region."""
        if self.packable is None:
            # Is there room to pack this?
            if (packable.width > self.width) or (packable.height > self.height):
                return False

            # Pack
            packable.x, packable.y = self.x, self.y
            self.packable = packable

            # Create sub-regions
            self.subregion_1 = PackRegion(
                self.x,
                self.y + self.packable.height,
                self.packable.width,
                self.height - self.packable.height,
            )
            self.subregion_2 = PackRegion(
                self.x + self.packable.width,
                self.y,
                self.width - self.packable.width,
                self.height,
            )
            return True

        # Pack into sub-region
        if self.subregion_1.perimeter > self.subregion_2.perimeter:
            return self.subregion_1.pack(packable) or self.subregion_2.pack(packable)
        return self.subregion_2.pack(packable) or self.subregion_1.pack(packable)



class Frame(Rect):
    """An image file that can be packed into a PackRegion."""

    def __init__(self, filename: str):
        self.filename = filename

        # Determine frame dimensions
        image = Image.open(filename)
        width, height = image.size
        del image

        super().__init__(0, 0, width, height)

    def draw(self, image) -> None:
        """Draw this frame into another Image."""
        i = Image.open(self.filename)
        image.paste(i, (self.x, self.y))
        del i


@dataclass
class Texture:
    """A collection of one or more frames."""

    name: str
    frames: list[Frame]


class TextureAtlas(PackRegion):
    """Texture Atlas generator."""

    def __init__(self, width: int, height: int):
        super().__init__(0, 0, width, height)
        self.textures: list[Texture] = []

    def pack(self, texture: Texture) -> None:
        """Pack a Texture into this atlas."""
        self.textures.append(texture)
        for frame in texture.frames:
            if not super().pack(frame):
                raise Exception("Failed to pack frame %s" % frame.filename)

    def write(self, filename: str, mode: str) -> None:
        """Generates the final texture atlas."""
        out = Image.new(mode, (self.width, self.height))
        for texture in self.textures:
            for frame in texture.frames:
                frame.draw(out)
        out.save(filename)


class BinaryTextureAtlasMap:
    """Binary Texture Atlas Map file generator.

    The binary atlas map is composed of four sections. The first section is the
    header. The second section contains the details of each texture (name,
    number of frames, etc.). The third section contains all null-terminated
    strings referenced by other sections. The fourth section contains the
    coordinates and dimensions of all texture frames.

    HEADER FORMAT

    Offset Size Description
    ------ ---- -----------
    0      4    Magic ('TEXA' = 0x41584554)
    4      4    Texture Atlas Width
    8      4    Texture Atlas Height
    12     4    Number of Textures
    16     4    Texture Section Offset
    20     4    Texture Section Size
    24     4    String Section Offset
    28     4    String Section Size
    32     4    Frame Section Offset
    36     4    Frame Section Size

    TEXTURE FORMAT

    Offset Size Description
    ------ ---- -----------
    0      4    Offset to Texture Name in String Section
    4      4    Number of Frames
    8      4    Offset to first Frame

    FRAME FORMAT

    Offset Size Description
    ------ ---- -----------
    0      4    X-Coordinate of Frame
    4      4    Y-Coordinate of Frame
    8      4    Frame Width
    12     4    Frame Height
    """

    def __init__(self, atlas: TextureAtlas):
        self.atlas = atlas

    def write(self, file: BinaryIO):
        """Writes the binary texture atlas map file into file object."""
        # Calculate offset and size of each section
        hdr_fmt = "IIIIIIIII"
        hdr_fmt_len = struct.calcsize(hdr_fmt)
        hdr_section_len = hdr_fmt_len + 4  # Header + Magic

        tex_fmt = "III"
        tex_fmt_len = struct.calcsize(tex_fmt)
        tex_section_off = hdr_section_len
        tex_section_len = len(self.atlas.textures) * tex_fmt_len

        str_section_off = tex_section_off + tex_section_len
        str_section_len = sum(map(lambda t: len(t.name) + 1, self.atlas.textures))

        frm_fmt = "IIII"
        frm_fmt_len = struct.calcsize(frm_fmt)
        frm_section_off = str_section_off + str_section_len
        frm_section_len = sum(map(lambda t: len(t.frames), self.atlas.textures))
        frm_section_len *= frm_fmt_len

        # Write Header
        file.write(b"TEXA")
        file.write(
            struct.pack(
                hdr_fmt,
                self.atlas.width,
                self.atlas.height,
                len(self.atlas.textures),
                tex_section_off,
                tex_section_len,
                str_section_off,
                str_section_len,
                frm_section_off,
                frm_section_len,
            )
        )

        # Write Texture Section
        str_offset = 0
        frm_offset = 0
        for t in self.atlas.textures:
            file.write(struct.pack(tex_fmt, str_offset, len(t.frames), frm_offset))
            str_offset += len(t.name) + 1  # +1 for sentinel byte
            frm_offset += len(t.frames) * frm_fmt_len

        # Write String Section
        for t in self.atlas.textures:
            file.write(t.name.encode("utf-8") + b"\x00")

        # Write Frame Section
        for t in self.atlas.textures:
            for f in t.frames:
                file.write(struct.pack(frm_fmt, f.x, f.y, f.width, f.height))


class JsonTextureAtlasMap:
    """A JSON encoding of the atlas map."""

    def __init__(self, atlas: TextureAtlas):
        self.atlas = atlas

    def write(self, file: TextIO) -> None:
        """Writes the JSON texture atlas map."""
        json.dump(
            {
                texture.name: [
                    (
                        frame.x,
                        (self.atlas.height - 1) - frame.y - (frame.height - 1),
                        frame.width,
                        frame.height,
                    )
                    for frame in texture.frames
                ]
                for texture in self.atlas.textures
            },
            file,
            indent=2,
        )


def main():
    desc = """Packs many smaller images into one larger image, a Texture
    Atlas. A companion file (.map), is created that defines where each texture is
    mapped in the atlas."""

    # Parse arguments
    arg_parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    arg_parser.add_argument(
        "-o",
        dest="outfile",
        metavar="output-file",
        type=str,
        default="atlas.png",
        help="output filename (atlas.png)",
    )
    arg_parser.add_argument("--map-output")
    arg_parser.add_argument("--map-format", choices={"json", "binary"}, default="json")
    arg_parser.add_argument(
        "-m",
        "--mode",
        metavar="mode",
        type=str,
        default="RGBA",
        help="output file mode (RGBA)",
    )
    arg_parser.add_argument(
        "-s",
        "--size",
        metavar="size",
        type=int,
        default=512,
        help="size of atlas (n x n)",
    )
    arg_parser.add_argument(
        "textures", metavar="texture", type=str, nargs="+", help="filename of texture"
    )

    args = arg_parser.parse_args()
    filename, ext = os.path.splitext(args.outfile)

    if ext == "":
        print("Error: Specify an image extension for outfile (e.g. atlas.png).")
        exit(1)

    # Parse texture names
    textures = []
    for texture in args.textures:
        # Look for a texture name
        matches = re.match(r"^((\w+)=)?(.+)", texture)
        name, frames = matches.group(2), shlex.split(matches.group(3))

        # If no name was specified, use the first frame's filename
        name = name or os.path.splitext(os.path.basename(frames[0]))[0]

        # Add frames to texture object list
        textures.append(Texture(name, [Frame(f) for f in frames]))

    # Sort textures by perimeter size in non-increasing order
    textures = sorted(textures, key=lambda i: i.frames[0].perimeter, reverse=True)

    # Create the atlas and pack textures in
    atlas = TextureAtlas(args.size, args.size)

    for texture in textures:
        atlas.pack(texture)

    atlas.write(args.outfile, args.mode)
    map_path = args.map_output or filename + ".map"

    match args.map_format:
        case "json":
            with open(map_path, "w", encoding="utf-8") as file:
                JsonTextureAtlasMap(atlas).write(file)
        case "binary":
            with open(map_path, "wb") as file:
                BinaryTextureAtlasMap(atlas).write(file)


if __name__ == "__main__":
    main()
