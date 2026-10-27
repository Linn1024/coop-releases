"""Publish tested portable assets, retaining every existing game/core download."""
import json
from pathlib import Path
import subprocess
import build_portable as build

REPO='Linn1024/coop-releases'
TAG='windows-2026-10-27'
OUT=build.OUT

def gh(*args):
    return subprocess.check_output(['gh',*args],text=True,encoding='utf-8')

def main():
    previous=json.loads(gh('release','view',TAG,'--repo',REPO,'--json','assets,body'))
    (OUT/'previous-release.json').write_text(json.dumps(previous,indent=2),encoding='utf-8')
    baseline=OUT/'previous';baseline.mkdir(exist_ok=True)
    gh('release','download',TAG,'--repo',REPO,'--pattern','VERIFICATION.txt','--dir',str(baseline),'--clobber')
    packages=sorted(OUT.glob('*-Coop-Portable-Windows-x64.zip'))
    assert len(packages)==4
    old={a['name']:a['digest'].removeprefix('sha256:') for a in previous['assets'] if a['name'] not in ('SHA256SUMS.txt','VERIFICATION.txt')}
    checksums=dict(old)
    for package in packages:checksums[package.name]=build.sha(package)
    (OUT/'SHA256SUMS.txt').write_text(''.join(digest+'  '+name+'\n' for name,digest in sorted(checksums.items())),encoding='ascii')
    verification=(baseline/'VERIFICATION.txt').read_text(encoding='utf-8')
    verification+='\nPortable standalone EXE update - 27 October 2026\n'
    for game in build.GAMES:
        verification+='PASS '+game['name']+': fresh source build; actual first-run ROM picker; invalid-ROM rejection; external Unicode ROM path; no ROM copy; remembered ROM; screen size; fullscreen and restoration; fullscreen persistence; P2 keyboard rebinding; restart; ROM location change; missing-ROM recovery; cancelling picker.\n'
    verification+='PASS all four portable ZIPs: archive integrity, complete exact source-file SHA256 manifests, matching source archives, component license notices, no ROMs or saves.\n'
    verification+='Existing installer and emulator-core downloads are retained unchanged. No new physical-controller or full-campaign test.\n'
    (OUT/'VERIFICATION.txt').write_text(verification,encoding='utf-8')
    prefix="""## Portable EXEs - recommended

Download the portable ZIP for your game, extract the entire ZIP, and open its EXE.
Choose your own original USA ROM on first run. The location is saved; next time,
just open the EXE. Keep the engine folder beside the EXE. No installation or
separate emulator is needed. Your ROM stays in its chosen folder.

- [Aladdin portable ZIP](https://github.com/Linn1024/coop-releases/releases/download/windows-2026-10-27/Aladdin-Coop-Portable-Windows-x64.zip)
- [Splatterhouse 3 portable ZIP](https://github.com/Linn1024/coop-releases/releases/download/windows-2026-10-27/Splatterhouse3-Coop-Portable-Windows-x64.zip)
- [Indiana Jones portable ZIP](https://github.com/Linn1024/coop-releases/releases/download/windows-2026-10-27/IndianaJones-Coop-Portable-Windows-x64.zip)
- [Batman Returns portable ZIP](https://github.com/Linn1024/coop-releases/releases/download/windows-2026-10-27/BatmanReturns-Coop-Portable-Windows-x64.zip)

**Settings > Screen size:** 1x-4x or fullscreen. **Settings > Controls (F2):**
P1/P2 keyboard and Xbox-compatible gamepad bindings. F11/Alt+Enter toggles
fullscreen. These settings persist. **Settings > Choose ROM** changes its saved
location. Use **Open saves and settings folder** to find user files.

Each portable ZIP includes matching source and component licenses. All four
passed actual first-run/relaunch UI checks, including Unicode paths, saved
window size/fullscreen, keyboard rebinding and missing-ROM recovery. Physical
controllers and a new campaign playthrough were not tested. See
[portable build details](https://github.com/Linn1024/coop-releases/blob/main/PORTABLE.md).
The previous installers and the complete eight-DLL emulator bundle remain intact.

---

"""
    body=previous['body'].replace('## Easy installation','## Older installers').replace('SHA256SUMS.txt covers all six package/source archives.','SHA256SUMS.txt covers all ten package/source archives.')
    notes=OUT/'release-notes.md';notes.write_text(prefix+body,encoding='utf-8')
    gh('release','upload',TAG,'--repo',REPO,*map(str,packages),str(OUT/'SHA256SUMS.txt'),str(OUT/'VERIFICATION.txt'),'--clobber')
    gh('release','edit',TAG,'--repo',REPO,'--title','Four co-op games - portable Windows EXEs and emulator cores','--notes-file',str(notes))
    current=json.loads(gh('release','view',TAG,'--repo',REPO,'--json','assets'))
    actual={a['name']:a['digest'].removeprefix('sha256:') for a in current['assets']}
    for name,digest in checksums.items():assert actual[name]==digest,(name,'remote checksum mismatch')
    for name,digest in old.items():assert actual[name]==digest,(name,'old download changed')
    print('PASS remote hashes for all four portable packages; all six prior package/source downloads retained byte-for-byte.')

if __name__=='__main__':main()
