# Co-op downloads for Windows

[Watch gameplay and new projects on Linn1024’s YouTube channel](https://www.youtube.com/channel/UCiU71T2o9V1uv62ZgrTRFew)

[Download installers and emulator cores](https://github.com/Linn1024/coop-releases/releases/tag/windows-2026-10-27)

Aladdin, Splatterhouse 3, Indiana Jones and Batman Returns.
For standalone play, download a game installer, extract ZIPs, run setup, and choose your own original USA ROM.

# Using the co-op cores in an emulator

These conversions run inside modified emulator cores. Your original ROM stays
unchanged. Opening it with an ordinary NES, SNES or Genesis core runs the
original single-player game. No ROM patch or Lua script is required.

Download and extract **Coop-Cores-Windows-x64.zip** from
[the Windows release](https://github.com/Linn1024/coop-releases/releases/tag/windows-2026-10-27).
The bundle includes matching source and license notices for each game. You
still need your own supported original USA ROM. These DLLs require Windows x64;
they are not builds for Linux, macOS, Android or consoles.

## BizHawk

Use a separate 64-bit [BizHawk installation](https://github.com/TASEmulators/BizHawk/releases).
Close it before replacing any core files. Keep each game's extracted folder
intact; the two Genesis adapters need their matching engine DLL beside them.

1. Start BizHawk. Choose **File > Open Advanced > Libretro**.
2. Select the core from the table below, then your supported original ROM.
3. Under **Config > Controllers**, bind both P1 and P2 RetroPads. The standalone
   launcher's keyboard settings do not configure your emulator.
4. Start a new game and check both players' controls. Use BizHawk's own save,
   load, fullscreen and emulator hotkeys.

| Game | Select this file in the bundle | Required beside it |
| --- | --- | --- |
| Aladdin | `Aladdin/bizhawk/aladdin_coop_libretro.dll` | `aladdin_engine.dll` |
| Splatterhouse 3 | `Splatterhouse3/bizhawk/splatterhouse_coop_libretro.dll` | `splatterhouse_engine.dll` |
| Indiana Jones | `IndianaJones/engine/fceumm_libretro.dll` | None |
| Batman Returns | `BatmanReturns/engine/snes9x2005_libretro.dll` | None |

For Aladdin, bind RetroPad B = sword, Y = apple, A = jump, L = rejoin, and
Start = pause. For Splatterhouse, B = attack, Y = transform, A = jump, and
Start = start/map. For Indiana Jones and Batman, map both RetroPads and use
the game-specific controls/README in the bundle.

Aladdin's adapter was previously tested with BizHawk 2.4 x64; newer versions
are not established by that test. Splatterhouse's adapter has headless boot
and save/replay coverage, but interactive BizHawk play remains unverified.
Indiana Jones and Batman have previously been exercised in BizHawk. This
bundle preparation checks DLL loading/API availability, not a new campaign
playthrough or compatibility with every BizHawk version.

## RetroArch and other Libretro hosts

The `engine` folders contain standard Libretro DLLs. They can be tried in a
Windows x64 Libretro frontend, but RetroArch compatibility has not been
validated for these co-op builds. The Genesis adapters above are specifically
for BizHawk; use the engine DLLs for a RetroArch experiment.

In RetroArch, use **Load Core > Install or Restore a Core** to install a copy
of a game's `engine/*_libretro.dll`, then **Load Core** and **Load Content** to
open your ROM. Configure both controller ports. See the official
[manual core installation guide](https://docs.libretro.com/guides/download-cores/).
Use a separate RetroArch installation for each game to avoid replacing another
custom or stock core with the same filename. An Online Updater download of a
stock core does not contain these co-op changes.

Standalone saves and emulator save files are not interchangeable. Keep co-op
saves with the matching custom core, and back up saves before changing versions.
Emulator support does not imply that netplay, rewind, run-ahead or achievements
have been tested. See each game's README for prototype gameplay limits.
