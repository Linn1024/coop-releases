# Portable Windows launchers

All four standalone games now choose the original ROM through a Windows file
picker, validate its contents, and remember its absolute location. ROM files can
have any name and stay in the user's chosen folder. Missing or moved ROMs prompt
for a replacement. Cancelling the first-run picker exits normally.

The Settings menu provides ROM selection, 1x-4x window sizes, fullscreen,
keyboard/gamepad bindings for both players, and access to the user files folder.
F2 opens controls; F11/Alt+Enter toggles fullscreen. Manual window sizes,
fullscreen, bindings and ROM location persist under
`%LOCALAPPDATA%\Linn1024Coop\<game>`. Existing standalone saves/controls beside an
upgraded EXE migrate without overwriting existing user files.

## Build and matching source

`desktop/coop_desktop.h` is shared by the four projects. Each project carries a
copy so it builds independently. Run `python desktop/build_portable.py` from
this checkout with sibling game repositories and the configured MinGW toolchain.
The script snapshots the source, builds all four EXEs and engines, and emits
portable ZIPs under `dist/portable-2026-10-27`. Choose a fresh output directory
when repeating a build. No game ROMs, personal saves or generated diagnostics
are packaged. Each download contains the matching `source.zip`, component
licenses, build instructions and `BUILD-INFO.json` with exact file hashes.
The build uses committed default BizHawk settings rather than live local edits.

## Verification

All four packaged builds passed actual Win32 UI checks using isolated settings:
first-run file picker, original-ROM hash validation, invalid-ROM rejection,
external Unicode ROM paths, no ROM copying, remembered path, 2x window sizing,
fullscreen/restoration, persisted fullscreen, P2 keyboard rebinding, relaunch,
changing ROM location, recovery after moving a ROM, and picker cancellation.

Run `python desktop/verify_desktop.py --packaged dist/portable-2026-10-27` to
repeat these checks. It needs the user's supported original ROMs in the sibling
project folders. Test ROM paths use hardlinks to those originals and isolated
settings under `dist/desktop-verification-packaged`; originals are not changed.
Source archives, package integrity and SHA256 hashes were also checked.
This launcher work does not establish a new campaign playthrough or physical
controller test. The older installers and emulator-core bundle remain available.


## Aladdin repaint update (2026-10-28)

Aladdin now composes frames in a reusable offscreen bitmap and presents each
complete frame in one blit. This removes the visible black clear between
frames. The original launcher exposed 2 black frames in 90 actual-window
captures; the corrected launcher exposed 0 in 90. Repeated window resizing and
fullscreen transitions kept GDI resource counts stable.
`python desktop/verify_aladdin_render.py` repeats this rendering check (requires
Pillow and the supported original ROM). The Aladdin portable ZIP was refreshed
with matching source; the engine and all other game/core assets are unchanged.
