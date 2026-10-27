"""Build matching-source Windows packages for Indiana Jones and Batman Returns.

Run: python releases/build.py --version 0.1.0
Source is staged before compilation; workstation binaries are never reused.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
GAMES = [
    dict(id='IndianaCoop', folder='indianaJonesCoop', title='Indiana Jones Co-op',
         exe='Indiana-Coop.exe', core='engine/fceumm_libretro.dll', license='engine/Copying',
         rom='Young Indiana Jones Chronicles, The (USA).nes',
         sha256='a8cec2954f957a88c1628aa6f6cc929babacc38fafa9a509a1ea0e253131d3f3'),
    dict(id='BatmanReturnsCoop', folder='batmanReturnsCoop', title='Batman Returns Co-op',
         exe='BatmanReturns-Coop.exe', core='engine/snes9x2005_libretro.dll', license='engine/copyright',
         rom='Batman Returns (U) [!].smc',
         sha256='f8d5c51f74df33edc827fbf8df7aab70160770ab0a896db6e59438ad9208cc6e'),
]
FORBIDDEN = {'.nes', '.sfc', '.smc', '.bin', '.gen', '.mdrom', '.smd', '.state',
             '.sav', '.srm', '.ijstate', '.brstate', '.mcstate', '.exe', '.dll', '.o',
             '.a', '.zip', '.pyc', '.lnk', '.png', '.jpg', '.fc0', '.fc1', '.luasav'}


def archive(folder, destination):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                out.write(path, path.relative_to(folder))


def stage_source(root, destination):
    # Engine source plus the frontend/build files suffice to reproduce these packages.
    # Include hidden build files; omit all runtime data and compiled artifacts.
    files = list((root / 'engine').rglob('*'))
    files += [p for p in root.iterdir() if p.is_file() and
              (p.suffix in {'.cpp', '.h', '.md', '.ps1'} or p.name == 'LICENSE')]
    for path in files:
        relative = path.relative_to(root)
        if not path.is_file() or any(p in {'.git', '__pycache__'} for p in relative.parts):
            continue
        if path.suffix.lower() in FORBIDDEN:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def build(game, output, toolchain):
    root = BASE / game['folder']
    work = output / game['id']
    source = work / 'source'
    package = work / (game['id'] + '-Windows-Setup')
    payload = package / 'payload'
    source.mkdir(parents=True)
    payload.mkdir(parents=True)
    stage_source(root, source)
    archive(source, payload / 'source.zip')
    subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                    '-File', str(source / 'build.ps1'), '-ToolchainBin', str(toolchain)], check=True)
    for relative in [game['exe'], game['core'], game['license'], 'README.md', 'THIRD_PARTY_NOTICES.md']:
        target = payload / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    if (source / 'LICENSE').exists():
        shutil.copy2(source / 'LICENSE', payload / 'LICENSE')
    (package / 'installer').mkdir()
    shutil.copy2(HERE / 'install.ps1', package / 'installer/install.ps1')
    (package / 'game.json').write_text(json.dumps(game, indent=2), encoding='utf-8')
    (package / 'Install.cmd').write_text(
        '@echo off\ncd /d "%~dp0"\npowershell.exe -NoProfile -STA -ExecutionPolicy Bypass '
        '-File "%~dp0installer\\install.ps1" %*\nif errorlevel 1 pause\n', encoding='ascii')
    (package / 'START-HERE.txt').write_text(
        f"{game['title']} - Windows x64\n\n"
        '1. Extract the entire ZIP.\n2. Double-click Install.cmd.\n'
        '3. Select your own original USA ROM.\n4. Open the desktop or Start-menu shortcut.\n\n'
        'No compiler, Python, separate emulator, or administrator access is needed.\n'
        'The ROM is not included. Setup accepts any filename and checks its contents.\n'
        f"Supported SHA-256: {game['sha256']}\n\n"
        'Read README.md for controls and current prototype limitations.\n'
        'Re-run setup to update; existing saves and controls.ini are preserved.\n'
        f"Default install folder: %LOCALAPPDATA%\\Programs\\{game['id']}\n"
        'To remove: back up your saves, delete that folder and its two shortcuts.\n'
        'The matching build source and component license notices are in payload/source.zip.\n',
        encoding='utf-8')
    result = output / f"{game['id']}-{output.name}-Windows-Setup.zip"
    archive(package, result)
    print(f'PACKAGE: {result}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--toolchain', type=Path, default=BASE / 'zeroTolerance/bizhawk-integration/mingw64/bin')
    args = parser.parse_args()
    if not args.version or any(c not in '0123456789abcdefghijklmnopqrstuvwxyz.-' for c in args.version):
        parser.error('Version must contain only lowercase letters, digits, dots and hyphens.')
    output = HERE.parent / 'dist' / args.version
    output.mkdir(parents=True, exist_ok=False)
    for game in GAMES:
        build(game, output, args.toolchain)
    hashes = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in sorted(output.glob('*.zip'))]
    (output / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='ascii')


if __name__ == '__main__':
    main()
