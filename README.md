# pxo to Aseprite

Moving from Pixelorama to Aseprite? This little tool brings your work with you.

Pixelorama saves projects as `.pxo` files, and Aseprite can't open them. You could export every animation as PNG strips and rebuild your layers and tags by hand, but that gets old fast once you have more than a couple of sprites. Drop your `.pxo` files on this window instead and you get real `.aseprite` projects back, with layers, frames, timing and tags all in place, ready to keep working on.

Your original `.pxo` files are only ever read, never changed. So you can try Aseprite, keep using Pixelorama, or go back and forth while you decide.

## What comes across

- **Layers:** names, order, visibility and opacity
- **Frames:** every frame, each with its own duration
- **Tags:** your animation ranges, by name

Some things don't make the trip, because Aseprite has no direct match for them: clipping masks, layer effects, reference images and saved palettes. Everything you actually drew comes across exactly.

## Is it exact?

Yes, and it checks. Aseprite itself writes each file, so it's a proper Aseprite project rather than an imitation. The tool then reads the new file back and compares it to your `.pxo`, pixel for pixel on every layer of every frame, along with the timings and tags. If anything doesn't match, the file is deleted and the window tells you what went wrong. That way you never end up with a quietly broken copy.

## Getting started

1. Download `pxo_to_aseprite.exe` from the [Releases](../../releases) page. No install is needed.
2. Run it. Windows may warn that the app is from an unknown publisher, because it isn't code-signed. Click **More info**, then **Run anyway**.
3. Drop `.pxo` files, or whole folders, onto the window. Folders are searched all the way down.

You'll need Aseprite installed, since it does the writing. The tool looks for it in the usual places (Steam, Program Files). If it can't find it, it asks you once and remembers.

### Where the files go

Fill in **Save to** to collect everything in one folder. Leave it empty and each `.aseprite` is saved right next to its `.pxo`.

### Converting again later

Say you've already converted a sprite and started editing the `.aseprite`. If you drop the `.pxo` again, your Aseprite version won't be overwritten: any `.aseprite` saved more recently than its `.pxo` is left alone. Tick **Replace .aseprite files saved later than their .pxo** if you really do want a fresh copy.

## Running from source

If you'd rather run the Python directly:

```
py -m pip install --user pillow numpy tkinterdnd2
```

Then double-click `pxo_to_aseprite_gui.pyw` for the window, or use the command line:

```
python pxo_to_aseprite.py my_art_folder
python pxo_to_aseprite.py hero.pxo enemy.pxo --out D:/aseprite
python pxo_to_aseprite.py my_art_folder --force
```

`--force` replaces `.aseprite` files even if they're newer. To point at an Aseprite install the tool can't find, set the `ASEPRITE` environment variable to the full path of `Aseprite.exe`.

## Building the exe yourself

Run `build.bat`. It installs what it needs and leaves `pxo_to_aseprite.exe` in the `dist` folder.

## What's inside

- `pxo_to_aseprite_gui.pyw`: the drag-and-drop window
- `pxo_to_aseprite.py`: reads the `.pxo`, hands it to Aseprite and checks the result
- `aseprite_build.lua`: the script Aseprite runs to build each file
- `aseprite_file.py`: reads `.aseprite` files, used for the check
- `build.bat`: builds the standalone exe
