"""Assemble emulator cores from the exact installer releases, with matching source."""
import ctypes
import io
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist/0.1.0'
STAGE = OUT / 'emulator-bundle'
STAGE.mkdir(exist_ok=False)


def extract_payload(zip_path, destination):
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.startswith('payload/') and not name.endswith('/'):
                target = destination / name[len('payload/'):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))


aladdin = STAGE / 'Aladdin'
extract_payload(OUT / 'Aladdin-Coop-Windows-Setup.zip', aladdin)
adapter_source = OUT / 'aladdin-adapter-source'
with zipfile.ZipFile(aladdin / 'source.zip') as archive:
    archive.extractall(adapter_source)
toolchain = ROOT.parent / 'zeroTolerance/bizhawk-integration/mingw64/bin'
adapter = aladdin / 'bizhawk'
adapter.mkdir()
subprocess.run([str(toolchain / 'g++.exe'), str(adapter_source / 'bizhawk/aladdin_libretro.cpp'),
                '-o', str(adapter / 'aladdin_coop_libretro.dll'), '-O2', '-std=c++17',
                '-static', '-shared', '-lbcrypt', '-lgdi32'], check=True,
               env={**os.environ, 'PATH': str(toolchain) + os.pathsep + os.environ['PATH']})
shutil.copy2(aladdin / 'engine/genesis_plus_gx_libretro.dll', adapter / 'aladdin_engine.dll')
# The prebuilt Splatterhouse payload was created by its existing release builder.
splatter = STAGE / 'Splatterhouse3'
shutil.copytree(ROOT.parent / 'splatterhouse/dist/0.1.0/payload', splatter)
for filename, folder in [('IndianaCoop', 'IndianaJones'), ('BatmanReturnsCoop', 'BatmanReturns')]:
    extract_payload(OUT / (filename + '-0.1.0-Windows-Setup.zip'), STAGE / folder)
# Emulator downloads do not need standalone executables; retain cores, docs and source.
for exe in STAGE.rglob('*.exe'):
    exe.unlink()
shutil.copy2(ROOT / 'releases/EMULATORS.md', STAGE / 'EMULATORS.md')
checks = []
for dll in sorted(STAGE.rglob('*.dll')):
    library = ctypes.CDLL(str(dll))
    assert library.retro_api_version() == 1, dll
    checks.append('PASS DLL load / Libretro API 1: ' + str(dll.relative_to(STAGE)))
(STAGE / 'BUNDLE-VERIFICATION.txt').write_text('\n'.join(checks) + '\n'
    'Adapters and engines are selected from matching release source/binaries.\n'
    'No new emulator gameplay or RetroArch compatibility check was performed.\n', encoding='utf-8')
with zipfile.ZipFile(OUT / 'Coop-Cores-Windows-x64.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(STAGE.rglob('*')):
        if path.is_file():
            assert path.suffix.lower() not in {'.nes', '.smc', '.sfc', '.bin', '.gen', '.state', '.sav', '.srm'}
            archive.write(path, path.relative_to(STAGE))
print('\n'.join(checks))
print('Core bundle ready: ' + str(OUT / 'Coop-Cores-Windows-x64.zip'))
