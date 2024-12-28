/*
 * Copyright (c) 2014-2024 Matt Borgerson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/*!
 * \file      readmap.c
 * \brief     Reads the contents of a texture atlas .map file.
 */

#include <stdio.h>
#include <stdlib.h>
#include <textureatlas.h>

void print_atlas_info(texture_atlas_t *ta);
void print_texture_info(texture_atlas_texture_t *texture);
void print_texture_frame_info(texture_atlas_texture_t *texture);

int main(
    int argc,
    char *argv[]
    )
{
    int result, i;
    texture_atlas_t *ta;
    texture_atlas_texture_t *texture;

    /* Check command line arguments */
    if (argc < 2 || argc > 3)
    {
        fprintf(stderr, "usage: readmap <map-file> [<texture-name>]\n");
        return 1;
    }

    /* Load the texture atlas */
    result = texture_atlas_load(argv[1], &ta);
    if (result)
    {
        fprintf(stderr, "Error: Failed to load the texture atlas map.\n");
        return 1;
    }

    if (argc == 2)
    {
        /* Print atlas info */
        print_atlas_info(ta);

        /* Print out info about each texture */
        for (i=0; i < ta->num_textures; i++)
        {
            print_texture_info(ta->textures+i);
        }
    }
    else if (argc == 3)
    {
        /* Find the texture in the atlas by name */
        texture = texture_atlas_lookup(ta, argv[2]);

        if (texture == NULL)
        {
            fprintf(stderr, "Error: Texture not found.\n");
            texture_atlas_free(ta);
            return 1;
        }

        /* Print texture frame info */
        print_texture_info(texture);
        print_texture_frame_info(texture);
    }

    /*
     * texture_atlas_map_load malloc'd, so we must free.
     */
    texture_atlas_free(ta);

    return 0;
}

/*!
 * \brief Print information about the texture atlas \a ta to standard-out.
 */
void
print_atlas_info(
    texture_atlas_t *ta /**< [in] Texture Atlas */
    )
{
    printf("Atlas is %dx%d with %d texture(s).\n", ta->width,
                                                   ta->height,
                                                   ta->num_textures);
}

/*!
 * \brief Print information about texture \a texture to standard-out.
 */
void
print_texture_info(
    texture_atlas_texture_t *texture /**< [in] Texture */
    )
{
    printf("Texture \"%s\" has %d frame(s).\n", texture->name,
                                                texture->num_frames);
}

/*!
 * \brief Print the coordinates of each frame of texture \a texture to
 *        standard-out.
 */
void
print_texture_frame_info(
    texture_atlas_texture_t *texture /**< [in] Texture */
    )
{
    unsigned int i;
    texture_atlas_frame_t *frame;

    for (i=0; i < texture->num_frames; i++)
    {
        frame = texture->frames + i;
        printf("Frame %d is %dx%d at %d, %d.\n", i,
                                                 frame->width,
                                                 frame->height,
                                                 frame->x,
                                                 frame->y);
    }
}
