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
 * \file textureatlas.h
 * \brief Utility functions for loading and accessing a Texture Atlas.
 */

#ifndef TEXTURE_ATLAS_H
#define TEXTURE_ATLAS_H

#pragma pack(1)
typedef struct _texture_atlas_frame_t
{
    unsigned int x;
    unsigned int y;
    unsigned int width;
    unsigned int height;
} texture_atlas_frame_t;
#pragma pack()

typedef struct _texture_atlas_texture_t
{
    const char *name;
    unsigned int num_frames;
    texture_atlas_frame_t *frames;
} texture_atlas_texture_t;

typedef struct _texture_atlas_t
{
    unsigned int width;
    unsigned int height;
    unsigned int num_textures;
    texture_atlas_texture_t *textures;
} texture_atlas_t;

int
texture_atlas_load(
    const char       *path,
    texture_atlas_t **ta);

int
texture_atlas_free(
    texture_atlas_t *ta);

texture_atlas_texture_t *
texture_atlas_lookup(
    texture_atlas_t *ta,
    const char      *name);

#endif /* TEXTURE_ATLAS_H */
