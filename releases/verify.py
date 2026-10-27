"""Check built archives, ROM validation, reinstall preservation and launcher boot."""
import argparse
import hashlib
import io
from pathlib import Path
import subprocess
import zipfile

from build import BASE, GAMES, FORBIDDEN


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    args = parser.parse_args()
    release = args.release.resolve()
    checks = []
    for game in GAMES:
        zip_path = next(release.glob(game['id'] + '-*-Windows-Setup.zip'))
        extracted = release / 'verification' / game['id'] / 'setup'
        with zipfile.ZipFile(zip_path) as package:
            assert not any(Path(n).suffix.lower() in FORBIDDEN - {'.exe', '.dll', '.zip'} for n in package.namelist())
            source = package.read('payload/source.zip')
            with zipfile.ZipFile(io.BytesIO(source)) as archive:
                assert not any(Path(n).suffix.lower() in FORBIDDEN for n in archive.namelist())
                assert 'launcher.cpp' in archive.namelist()
                assert 'build.ps1' in archive.namelist()
                assert game['license'] in archive.namelist()
            package.extractall(extracted)
        installed = extracted.parent / 'installed'
        bad_rom = extracted.parent / 'invalid.rom'
        bad_rom.write_bytes(b'not a ROM')

        def install(rom):
            return subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                   '-File', str(extracted / 'installer/install.ps1'),
                                   '-NonInteractive', '-NoShortcuts', '-RomPath', str(rom),
                                   '-InstallDirectory', str(installed)], capture_output=True, text=True)

        rejected = install(bad_rom)
        assert rejected.returncode != 0 and not installed.exists(), rejected.stdout + rejected.stderr
        rom = BASE / game['folder'] / game['rom']
        accepted = install(rom)
        assert accepted.returncode == 0, accepted.stdout + accepted.stderr
        assert hashlib.sha256((installed / game['rom']).read_bytes()).hexdigest() == game['sha256']
        (installed / 'saves').mkdir()
        sentinel = installed / 'saves/preserve-test.txt'
        sentinel.write_text('keep this save', encoding='utf-8')
        controls = installed / 'controls.ini'
        controls.write_text('; preserve settings\n', encoding='ascii')
        accepted = install(rom)
        assert accepted.returncode == 0, accepted.stdout + accepted.stderr
        assert sentinel.read_text() == 'keep this save'
        assert controls.read_text() == '; preserve settings\n'
        # WaitForInputIdle verifies the GUI reaches its message loop; DLL loading,
        # ROM checking and core initialization all precede that in these launchers.
        boot = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                              "$ErrorActionPreference='Stop'; "
                              f"$p=Start-Process -FilePath '{installed / game['exe']}' "
                              f"-WorkingDirectory '{installed}' -WindowStyle Hidden -PassThru; "
                              "try { if (-not $p.WaitForInputIdle(15000)) { throw 'GUI boot timed out' }; "
                              "Start-Sleep -Seconds 2; $p.Refresh(); "
                              "if ($p.HasExited) { throw 'Launcher exited during boot' }; "
                              "if ($p.MainWindowTitle -match 'error|missing|failed') { throw $p.MainWindowTitle }; "
                              "Write-Output $p.MainWindowTitle "
                              "} finally { if (-not $p.HasExited) { Stop-Process -Id $p.Id } }"],
                              capture_output=True, text=True)
        assert boot.returncode == 0, boot.stdout + boot.stderr
        checks.append(f"PASS {game['title']}: archive contents, matching build source, wrong-ROM rejection, "
                      'valid-ROM installation, reinstall preserving saves/settings, launcher boot. ' + boot.stdout.strip())
    (release / 'VERIFICATION.txt').write_text('\n'.join(checks) + '\n'
        'No campaign traversal, physical controller testing or interactive installer UI validation performed.\n', encoding='utf-8')
    print('\n'.join(checks))


if __name__ == '__main__':
    main()
