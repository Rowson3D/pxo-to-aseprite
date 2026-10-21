# pxo to Aseprite

Converts Pixelorama `.pxo` projects to Aseprite `.aseprite` files.

Kept: every layer (name, visibility, opacity, order), every frame and its duration, and the tags.
Not kept: clipping masks, layer effects, reference images and saved palettes.

Aseprite writes each file itself, in batch mode. The result is then read back and checked against the `.pxo`: every layer of every frame, pixel for pixel, plus the durations and the tags. A file that doesn't match is removed and reported.

## Use

Double-click `pxo_to_aseprite_gui.pyw`, or the `.exe` that `build.bat` makes. Then drop `.pxo` files or folders on the window.

- **Save to**: the output folder. Leave it empty to save each file beside its `.pxo`.
- An `.aseprite` saved later than its `.pxo` is left alone, unless you tick the replace box.

From a command prompt:

```
python pxo_to_aseprite.py art/hero art/enemy.pxo --out D:/aseprite
python pxo_to_aseprite.py art/hero --force
```

## Needs

- Aseprite. The Steam install is found on its own; set `ASEPRITE` to `Aseprite.exe` for any other install.
- Python 3 with Pillow and NumPy, plus tkinterdnd2 for drag and drop:
  `py -m pip install --user pillow numpy tkinterdnd2`

## Build the exe

Run `build.bat`. It installs what it needs and writes `dist/pxo_to_aseprite.exe`. The exe needs no Python, but it still needs Aseprite.

## Files

- `pxo_to_aseprite.py`: reads the `.pxo`, runs Aseprite, checks the result
- `aseprite_build.lua`: the Aseprite script that builds the file
- `aseprite_file.py`: reads `.aseprite` files (RGBA) into layers, frames and tags
- `pxo_to_aseprite_gui.pyw`: the drop-on window
