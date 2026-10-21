"""Converts Pixelorama .pxo projects to Aseprite .aseprite files, beside the
originals. The .pxo files are only read.

    python pxo_to_aseprite.py art/hero art/enemy
    python pxo_to_aseprite.py art/slime/slime.pxo --out D:/aseprite
    python pxo_to_aseprite.py ... --force

Or double-click pxo_to_aseprite_gui.pyw (or the .exe build.bat makes) and
drop files and folders on it.

Each .pxo becomes <same name>.aseprite in the same folder, or in --out. An
.aseprite saved later than its .pxo (worked on in Aseprite) is left alone
unless --force is given. Kept: every layer
(name, visibility, opacity, bottom to top), every frame and its own duration,
and the tags. Not kept: Pixelorama's clipping masks and layer effects (Aseprite
has neither), reference images and saved palettes.

The .pxo is unpacked to PNGs and a manifest in a temporary folder, and
Aseprite itself writes the .aseprite (aseprite_build.lua, run in Aseprite's
batch mode), so the file is Aseprite's own. Each result is read back
(aseprite_file.py) and checked against the .pxo: every layer of every frame
pixel for pixel, the durations and the tags. A file that does not match is
reported and removed.

ASEPRITE can point at Aseprite.exe; otherwise the usual install folders
(Steam, Program Files) are tried.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aseprite_file  # noqa: E402

# Built into an .exe, the Lua script is unpacked beside the bundled code.
HERE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
INSTALLS = [
    r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe',
    r'C:\Program Files\Steam\steamapps\common\Aseprite\Aseprite.exe',
    r'C:\Program Files\Aseprite\Aseprite.exe',
    r'C:\Program Files (x86)\Aseprite\Aseprite.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\Aseprite\Aseprite.exe'),
]


def find_aseprite():
    """Aseprite.exe from ASEPRITE or the usual install folders, or None."""
    for exe in [os.environ.get('ASEPRITE', '')] + INSTALLS:
        if exe and os.path.isfile(exe):
            return exe
    return None


def aseprite_exe():
    exe = find_aseprite()
    if exe is None:
        raise RuntimeError('Aseprite not found; set ASEPRITE to Aseprite.exe.')
    return exe


def read_pxo(path):
    """(width, height, layers, frames) with layers [{name, visible, opacity}]
    bottom to top and frames [{seconds, cels: {layer index: RGBA bytes}}]."""
    z = zipfile.ZipFile(path)
    data = json.loads(z.read('data.json'))
    w, h = data['size_x'], data['size_y']
    fps = float(data.get('fps') or 6.0)
    layers = [{'name': l['name'], 'visible': bool(l.get('visible', True)),
               'opacity': max(0, min(255, int(round(float(l.get('opacity', 1.0)) * 255))))}
              for l in data['layers']]
    frames = []
    for f, frame in enumerate(data['frames']):
        cels = {}
        for i in range(len(layers)):
            name = 'image_data/frames/%d/layer_%d' % (f + 1, i + 1)
            try:
                raw = z.read(name)
            except KeyError:
                continue
            if len(raw) == w * h * 4 and any(raw[3::4]):
                cels[i] = raw
        seconds = float(frame.get('duration', 1.0)) / fps
        frames.append({'seconds': seconds, 'cels': cels})
    tags = [{'name': t['name'], 'from': int(t['from']), 'to': int(t['to'])} for t in data.get('tags', [])]
    return w, h, layers, frames, tags


def out_path_for(pxo_path, out_dir=None):
    name = os.path.splitext(os.path.basename(pxo_path))[0] + '.aseprite'
    return os.path.join(out_dir or os.path.dirname(pxo_path), name)


def is_newer(out_path, pxo_path):
    return os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(pxo_path)


def convert(pxo_path, out_dir=None):
    """(written path, problems). A file that fails the check is removed."""
    w, h, layers, frames, tags = read_pxo(pxo_path)
    out_path = out_path_for(pxo_path, out_dir)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='pxo2ase_')
    try:
        lines = ['size\t%d\t%d' % (w, h), 'out\t%s' % os.path.abspath(out_path)]
        for l in layers:
            lines.append('layer\t%s\t%d\t%d' % (l['name'], 1 if l['visible'] else 0, l['opacity']))
        for f in frames:
            lines.append('frame\t%.6f' % f['seconds'])
        for fi, f in enumerate(frames, 1):
            for li, raw in f['cels'].items():
                png = os.path.join(tmp, 'f%03d_l%02d.png' % (fi, li + 1))
                Image.frombytes('RGBA', (w, h), raw).save(png)
                lines.append('cel\t%d\t%d\t%s' % (li + 1, fi, png))
        for t in tags:
            lines.append('tag\t%s\t%d\t%d' % (t['name'], t['from'], t['to']))
        manifest = os.path.join(tmp, 'manifest.txt')
        with open(manifest, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        result = subprocess.run([aseprite_exe(), '-b', '--script-param', 'manifest=' + manifest,
                                 '--script', os.path.join(HERE, 'aseprite_build.lua')],
                                capture_output=True, text=True, timeout=300,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if not os.path.exists(out_path):
            raise RuntimeError('Aseprite did not write %s:\n%s%s' % (out_path, result.stdout, result.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    problems = check(out_path, w, h, layers, frames, tags)
    if problems:
        os.remove(out_path)
        return out_path, problems
    return out_path, []


def check(out_path, w, h, layers, frames, tags):
    """Differences between the written .aseprite and the .pxo it came from."""
    ase = aseprite_file.read(out_path)
    problems = []
    if (ase['width'], ase['height']) != (w, h):
        problems.append('size %dx%d, expected %dx%d' % (ase['width'], ase['height'], w, h))
    names = [l['name'] for l in ase['layers']]
    if names != [l['name'] for l in layers]:
        problems.append('layers %s, expected %s' % (names, [l['name'] for l in layers]))
    for a, b in zip(ase['layers'], layers):
        if a['visible'] != b['visible'] or a['opacity'] != b['opacity']:
            problems.append('layer %s visibility or opacity differs' % b['name'])
    if len(ase['frames']) != len(frames):
        problems.append('%d frames, expected %d' % (len(ase['frames']), len(frames)))
    for fi, (af, pf) in enumerate(zip(ase['frames'], frames)):
        if abs(af['ms'] - pf['seconds'] * 1000) > 1.5:
            problems.append('frame %d lasts %d ms, expected %.0f' % (fi + 1, af['ms'], pf['seconds'] * 1000))
        for li in range(len(layers)):
            want = pf['cels'].get(li)
            got = af['images'].get(li)
            if want is None and got is None:
                continue
            if want is not None:
                want = np.frombuffer(want, np.uint8).reshape(h, w, 4).copy()
                want[want[..., 3] == 0] = 0
            if want is None or got is None or not np.array_equal(got, want):
                problems.append('frame %d layer %s pixels differ' % (fi + 1, layers[li]['name']))
    # Aseprite keeps tags in frame order, whatever order they were made in.
    got_tags = sorted((t['from'] + 1, t['to'] + 1, t['name']) for t in ase['tags'])
    want_tags = sorted((t['from'], t['to'], t['name']) for t in tags)
    if got_tags != want_tags:
        problems.append('tags %s, expected %s' % (got_tags, want_tags))
    return problems[:8]


def targets(args, recurse=False):
    """The .pxo files named, and those in any folder named."""
    out = []
    for a in args:
        if os.path.isdir(a):
            if recurse:
                for d, _subdirs, names in os.walk(a):
                    out += sorted(os.path.join(d, f) for f in names if f.lower().endswith('.pxo'))
            else:
                out += sorted(os.path.join(a, f) for f in os.listdir(a) if f.lower().endswith('.pxo'))
        elif a.lower().endswith('.pxo'):
            out.append(a)
    return out


def main(args):
    out_dir, force = None, '--force' in args
    args = [a for a in args if a != '--force']
    if '--out' in args:
        i = args.index('--out')
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    files = targets(args)
    if not files:
        print(__doc__)
        return 2
    bad = kept = 0
    for path in files:
        if not force and is_newer(out_path_for(path, out_dir), path):
            kept += 1
            print('  -- %s kept: its .aseprite is newer (--force to replace)' % path)
            continue
        out, problems = convert(path, out_dir)
        if problems:
            bad += 1
            print('  !! %s did not convert cleanly (removed):' % path)
            for p in problems:
                print('       ' + p)
        else:
            print('  ok %s' % out)
    print('%d converted, %d kept, %d failed' % (len(files) - bad - kept, kept, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
