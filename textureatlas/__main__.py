import argparse
import os.path
import re
import shlex
import textwrap

from textureatlas import (
    BinaryTextureAtlasMap,
    JsonTextureAtlasMap,
    Frame,
    Texture,
    TextureAtlas,
    )


def main():
    desc = """
        Packs many smaller images into one larger image, a Texture Atlas. A
        companion file (.map), is created that defines where each texture is
        mapped in the atlas.
        """

    # Parse arguments
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent(desc),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    arg_parser.add_argument(
        "-o",
        "--output-image-filename",
        metavar="output-image-filename",
        type=str,
        default="atlas.png",
        help="output image filename (atlas.png)",
    )
    arg_parser.add_argument(
        "-m",
        "--output-map-filename",
        metavar="output-map-filename",
        type=str,
        default="",
        help="output map filename (atlas.map)",
    )
    arg_parser.add_argument(
        "-mf",
        "--map-format",
        choices={"json", "binary"},
        default="json",
        help="format of map output",
    )
    arg_parser.add_argument(
        "-im",
        "--image-mode",
        metavar="mode",
        type=str,
        default="RGBA",
        help="output file mode (RGBA)",
    )
    arg_parser.add_argument(
        "textures", metavar="texture", type=str, nargs="+", help="filename of texture"
    )

    args = arg_parser.parse_args()
    filename, ext = os.path.splitext(args.output_image_filename)

    if ext == "":
        print(
            "Error: Specify an image extension for output_image_filename (e.g. atlas.png)."
        )
        exit(1)

    # Parse texture names
    textures = []
    for texture in args.textures:
        # Look for a texture name
        matches = re.match(r"^((\w+)=)?(.+)", texture)
        assert matches

        name, frames = matches.group(2), shlex.split(matches.group(3))

        # If no name was specified, use the first frame's filename
        name = name or os.path.splitext(os.path.basename(frames[0]))[0]

        # Add frames to texture object list
        textures.append(Texture(name, [Frame(f) for f in frames]))

    # Sort textures by perimeter size in non-increasing order
    textures = sorted(textures, key=lambda t: t.frames[0].perimeter, reverse=True)
    finished = False
    largest_frame = textures[0].frames[0]
    width, height = largest_frame.width, largest_frame.height
    atlas = TextureAtlas(width, height)

    while not finished:
        finished = True
        for texture in textures:
            if atlas.pack_texture(texture):
                continue

            # Failed to pack the texture. Make the atlas larger...
            finished = False
            biggest_free_space = max(
                atlas.get_free_regions(), key=lambda r: r.perimeter
            )
            if biggest_free_space.width < texture.frames[0].width:
                width += texture.frames[0].width
            else:
                height += texture.frames[0].height
            atlas = TextureAtlas(width, height)
            break

    atlas.write(args.output_image_filename, args.image_mode)
    map_path = args.output_map_filename or (filename + ".map")

    match args.map_format:
        case "json":
            with open(map_path, "w", encoding="utf-8") as file:
                JsonTextureAtlasMap(atlas).write(file)
        case "binary":
            with open(map_path, "wb") as file:
                BinaryTextureAtlasMap(atlas).write(file)


if __name__ == "__main__":
    main()
