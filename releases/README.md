# Windows co-op downloads

[Download all four packages](https://github.com/Linn1024/coop-releases/releases/tag/windows-2026-10-27).

The shared release collects four Windows x64 packages. Aladdin and
Splatterhouse 3 use their existing installer packages. Indiana Jones and Batman
Returns use the shared ZIP setup here.

For emulator use, download **Coop-Cores-Windows-x64.zip** from the same release.
It includes the four custom cores, the Aladdin/Splatterhouse BizHawk adapters,
matching source, licenses, and [emulator instructions](EMULATORS.md).

For ZIP setups, extract everything, open **Install.cmd**, and select your own
original USA ROM. Setup checks the ROM and creates desktop and Start-menu
shortcuts. No compiler, Python, separate emulator or administrator access is
needed. ROMs and player saves are excluded. Compiled cores, launchers, matching
source and component license notices are included.

Reinstalling the shared ZIP setups preserves saves and controls.ini. To remove
one, back up saves, delete its folder under `%LOCALAPPDATA%/Programs`, and delete
its shortcuts. Each package's README describes controls and prototype limits;
packaging does not establish full campaign compatibility.

Build the two shared packages from staged source:

```powershell
python releases/build.py --version 0.1.0 --toolchain C:/path/to/mingw64/bin
python releases/verify.py dist/0.1.0
```

The projects must be sibling folders as described in the main README. Builds
never reuse workstation DLLs or launchers. `dist/0.1.0/VERIFICATION.txt` records
archive checks, wrong-ROM rejection, installation with the supported ROM,
reinstallation preserving saves/settings and launcher boot. GUI ROM picking,
physical controllers and full campaign traversal require separate testing.

Aladdin's builder is `../aladdinGameCoop/installer/build-package.ps1`.
Splatterhouse's builder is `../splatterhouse/installer/build-release.ps1`.
