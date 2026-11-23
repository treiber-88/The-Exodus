# The Exodus

A retro journey game for Windows, macOS, and Linux. Lead Israel from Rameses to Mount Nebo: buy supplies, set pace and rations, face grumbling and attacks, and cross the water with Moses.

## Run from source

    pip install -r requirements.txt
    python main.py

## Build

    pip install -r requirements.txt pyinstaller
    python tools/build_release.py

Each operating system must build its own copy. The GitHub Actions workflow in `.github/workflows/build.yml` builds all three when run manually.

## Art

- `python tools/pixelart.py --sheet` compiles the hand-drawn sprites in `art/sprites`.
- `python tools/build_scenes.py` renders landscapes in a running Blender, then converts them to palette pixel art. Add `--skip-render` to convert existing renders only.

## Tests

    python tools/sim_test.py
    python tools/ui_test.py <screenshot folder>
    python tools/save_test.py

## Saved games

Choose **Save game** or press F5 at camp. There are three slots, and **Load saved game** is on the title screen. Saves are stored in a `.the_exodus` folder in your home folder.
