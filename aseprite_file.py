"""Reads Aseprite .aseprite files (RGBA sprites) into plain layers and frames,
for the converter's check, and so the sprite tools in tools/sprite_layers
can take .aseprite sources as well as .pxo.

    read(path) -> {width, height, layers, frames, tags}
        layers: [{name, visible, opacity 0-255, group}] bottom to top
        frames: [{ms, images: {layer index: np.uint8 (h, w, 4)}}]
        tags:   [{name, from, to}] with 0-based frames

Each image is the full canvas with the cel placed and its opacity applied.
Fully transparent pixels are stored as 0,0,0,0. Linked cels share their
image. Only RGBA sprites are read; tilemap layers are skipped.

Format: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md
"""
import os
import struct
import zlib

import numpy as np

HEADER_MAGIC = 0xA5E0
FRAME_MAGIC = 0xF1FA
LAYER_CHUNK = 0x2004
CEL_CHUNK = 0x2005
TAGS_CHUNK = 0x2018


def _string(data, at):
    n = struct.unpack_from('<H', data, at)[0]
    return data[at + 2:at + 2 + n].decode('utf-8'), at + 2 + n


def read(path):
    data = open(path, 'rb').read()
    _size, magic, frame_count, w, h, depth, flags = struct.unpack_from('<IHHHHHI', data, 0)
    if magic != HEADER_MAGIC:
        raise ValueError('%s is not an .aseprite file' % path)
    if depth != 32:
        raise ValueError('%s is not RGBA (colour depth %d)' % (path, depth))
    opacity_valid = bool(flags & 1)
    layers, frames, tags = [], [], []
    at = 128
    for f in range(frame_count):
        frame_bytes, fmagic, old_chunks, ms = struct.unpack_from('<IHHH', data, at)
        if fmagic != FRAME_MAGIC:
            raise ValueError('%s: bad frame %d' % (path, f))
        new_chunks = struct.unpack_from('<I', data, at + 12)[0]
        chunks = new_chunks or old_chunks
        frame = {'ms': ms, 'images': {}}
        frames.append(frame)
        c = at + 16
        for _ in range(chunks):
            size, kind = struct.unpack_from('<IH', data, c)
            body = c + 6
            if kind == LAYER_CHUNK:
                lflags, ltype, child = struct.unpack_from('<HHH', data, body)
                opacity = data[body + 12] if opacity_valid else 255
                name, _ = _string(data, body + 16)
                layers.append({'name': name, 'visible': bool(lflags & 1), 'opacity': opacity,
                               'group': ltype == 1, 'tilemap': ltype == 2, 'child': child})
            elif kind == CEL_CHUNK:
                li, x, y, opacity, ctype = struct.unpack_from('<HhhBH', data, body)
                p = body + 16
                if ctype == 1:
                    linked = struct.unpack_from('<H', data, p)[0]
                    image = frames[linked]['images'].get(li)
                    if image is not None:
                        frame['images'][li] = image
                elif ctype in (0, 2):
                    cw, ch = struct.unpack_from('<HH', data, p)
                    raw = data[p + 4:c + size]
                    if ctype == 2:
                        raw = zlib.decompress(raw)
                    cel = np.frombuffer(raw[:cw * ch * 4], np.uint8).reshape(ch, cw, 4).copy()
                    if opacity != 255:
                        cel[..., 3] = (cel[..., 3].astype(np.uint16) * opacity // 255).astype(np.uint8)
                    image = np.zeros((h, w, 4), np.uint8)
                    x0, y0 = max(0, x), max(0, y)
                    x1, y1 = min(w, x + cw), min(h, y + ch)
                    if x1 > x0 and y1 > y0:
                        image[y0:y1, x0:x1] = cel[y0 - y:y1 - y, x0 - x:x1 - x]
                    image[image[..., 3] == 0] = 0
                    frame['images'][li] = image
            elif kind == TAGS_CHUNK:
                n = struct.unpack_from('<H', data, body)[0]
                p = body + 10
                for _ in range(n):
                    t_from, t_to = struct.unpack_from('<HH', data, p)
                    name, p = _string(data, p + 17)
                    tags.append({'name': name, 'from': t_from, 'to': t_to})
            c += size
        at += frame_bytes
    return {'width': w, 'height': h, 'layers': layers, 'frames': frames, 'tags': tags}


def newest(path):
    """The .aseprite beside a .pxo when there is one and it was saved later,
    so a file moved to Aseprite is read without changing the configs."""
    side = os.path.splitext(path)[0] + '.aseprite'
    if path.lower().endswith('.pxo') and os.path.exists(side) and (
            not os.path.exists(path) or os.path.getmtime(side) > os.path.getmtime(path)):
        return side
    return path


def is_aseprite(path):
    return path.lower().endswith(('.aseprite', '.ase'))
