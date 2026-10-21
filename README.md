# pxo to Aseprite

Converts Pixelorama `.pxo` files to Aseprite `.aseprite` files. The `.pxo` files are read only.

## Converted

- Layers: name, order, visibility, opacity
- Frames, with per-frame duration
- Tags: name and frame range

Not converted: clipping masks, layer effects, reference images, palettes.

## Method

1. The `.pxo` is unpacked to one PNG per layer per frame, plus a manifest.
2. Aseprite runs `aseprite_build.lua` in batch mode to build and save the `.aseprite`.
3. The output is read back with `aseprite_file.py` and compared to the `.pxo`: pixels on every layer of every frame, frame durations, and tags. If any of them differ, the output file is deleted and the differences are listed.

## Requirements

- Windows
- Aseprite. Searched for in the Steam and Program Files folders. If it isn't found, the window asks for `Aseprite.exe` and saves the path. You can also set the `ASEPRITE` environment variable to its path.

## Exe

Download `pxo_to_aseprite.exe` from Releases. It isn't code-signed, so SmartScreen may block it: choose More info, then Run anyway.

Drop `.pxo` files or folders on the window. Folders are searched recursively.

- **Save to**: the output folder. If empty, each output is written beside its `.pxo`.
- An `.aseprite` with a newer modified time than its `.pxo` is skipped. Tick the replace box to overwrite it.

Settings are stored in `%USERPROFILE%\.pxo_to_aseprite.json`.

## Source

```
py -m pip install --user pillow numpy tkinterdnd2
```

Window: `pxo_to_aseprite_gui.pyw`

Command line:

```
python pxo_to_aseprite.py <files or folders> [--out <folder>] [--force]
```

`--force` overwrites newer `.aseprite` files. Folders are not searched recursively on the command line.

## Build

`build.bat` installs Pillow, NumPy, tkinterdnd2 and PyInstaller if they're missing, then writes `dist\pxo_to_aseprite.exe`.

## Files

| File | Purpose |
| --- | --- |
| `pxo_to_aseprite.py` | `.pxo` reader, Aseprite call, output check, command line |
| `aseprite_build.lua` | Builds the sprite from the manifest |
| `aseprite_file.py` | `.aseprite` reader (RGBA) |
| `pxo_to_aseprite_gui.pyw` | Drop window |
| `build.bat` | PyInstaller build |
