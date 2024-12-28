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
 * \file textureatlas.c
 * \brief Utility functions for loading and accessing a Texture Atlas.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <textureatlas.h>

#define TEXTURE_ATLAS_MAP_FILE_MAGIC 0x41584554

#pragma pack(1)
typedef struct _texture_atlas_map_file_header_t {
    unsigned int magic;
    unsigned int width;
    unsigned int height;
    unsigned int num_textures;
    unsigned int tex_section_offset;
    unsigned int tex_section_len;
    unsigned int str_section_offset;
    unsigned int str_section_len;
    unsigned int frm_section_offset;
    unsigned int frm_section_len;
} texture_atlas_map_file_header_t;
#pragma pack()

#pragma pack(1)
typedef struct _texture_atlas_map_file_texture_t
{
    unsigned int name;
    unsigned int num_frames;
    unsigned int frames;
} texture_atlas_map_file_texture_t;
#pragma pack()

/*!
 * \brief Loads the binary texture atlas .map file at \a path.
 *
 * Note: Memory is allocated by this call. \c texture_atlas_free should be
 *       called when the texture atlas is no longer needed.
 */
int
texture_atlas_load(
    const char       *path, /**< [in] The path to the .map file. */
    texture_atlas_t **ta /**< [out] Texture Atlas. */
    )
{
    FILE *fd;
    unsigned int i;
    char *strings;
    texture_atlas_map_file_header_t header;
    texture_atlas_map_file_texture_t texture;
    texture_atlas_frame_t *frames;

    fd = fopen(path, "rb");
    if (fd == NULL)
    {
        fprintf(stderr, "Error: Failed to open %s for reading.\n", path);
        return 1;
    }

    /* Read header */
    if (!fread(&header, sizeof(header), 1, fd))
    {
        fprintf(stderr, "Error: Failed to read header.\n");
        fclose(fd);
        return 1;
    }

    /* Check header magic */
    if (header.magic != TEXTURE_ATLAS_MAP_FILE_MAGIC)
    {
        fprintf(stderr, "Error: Invalid header magic.\n");
        fclose(fd);
        return 1;
    }

    /* Allocate memory */
    *ta = malloc(sizeof(texture_atlas_t) +
                 sizeof(texture_atlas_texture_t) * header.num_textures +
                 header.str_section_len +
                 header.frm_section_len);

    if (*ta == NULL)
    {
        fprintf(stderr, "Error: Failed to allocate memory for atlas.\n");
        fclose(fd);
        return 1;
    }

    (*ta)->width        = header.width;
    (*ta)->height       = header.height;
    (*ta)->num_textures = header.num_textures;

    /* Place textures after the atlas root */
    (*ta)->textures = (void *)(*ta) + sizeof(texture_atlas_t);

    /* Place strings after textures */
    strings = (void *)((*ta)->textures) +
              (*ta)->num_textures * sizeof(texture_atlas_texture_t);

    /* Place frames after strings */
    frames = (void *)strings + header.str_section_len;

    /* Read texture info into memory */
    fseek(fd, header.tex_section_offset, SEEK_SET);
    for (i=0; i < header.num_textures; i++)
    {
        if (!fread(&texture, sizeof(texture_atlas_map_file_texture_t), 1, fd))
        {
            fprintf(stderr, "Error: Failed to read texture data.\n");
            fclose(fd);
            free(*ta);
            return 1;
        }

        (*ta)->textures[i].name       = strings + texture.name;
        (*ta)->textures[i].num_frames = texture.num_frames;
        (*ta)->textures[i].frames     = (void *)frames + texture.frames;
    }

    /* Read strings into memory */
    fseek(fd, header.str_section_offset, SEEK_SET);
    if (!fread(strings, header.str_section_len, 1, fd))
    {
        fprintf(stderr, "Error: Failed to read texture strings.\n");
        fclose(fd);
        free(*ta);
        return 1;
    }

    /* Read frames */
    fseek(fd, header.frm_section_offset, SEEK_SET);
    if (!fread(frames, header.frm_section_len, 1, fd))
    {
        fprintf(stderr, "Error: Failed to read texture frames.\n");
        fclose(fd);
        free(*ta);
        return 1;
    }

    fclose(fd);
    return 0;
}

/*!
 * \brief Frees the resources allocated by this texture atlas.
 */
int
texture_atlas_free(
    texture_atlas_t *ta)
{
    free(ta);
    return 0;
}

/*!
 * \brief Finds a texture in a texture atlas by name.
 */
texture_atlas_texture_t *
texture_atlas_lookup(
    texture_atlas_t *ta,  /**< [in] Texture Atlas to reference. */
    const char      *name /**< [in] Name of texture to find. */
    )
{
    unsigned int i;

    for (i=0; i < ta->num_textures; i++)
    {
        if (strcmp(name, ta->textures[i].name) == 0)
            return ta->textures+i;
    }

    return NULL;
}