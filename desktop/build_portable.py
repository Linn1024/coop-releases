"""Build the four portable standalone downloads from matching source snapshots."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
OUT=ROOT/'dist/portable-2026-10-27'
TOOLCHAIN=BASE/'zeroTolerance/bizhawk-integration/mingw64/bin'
GAMES=[
 dict(folder='aladdinGameCoop',id='AladdinCoop',name='Aladdin',exe='Aladdin-Coop.exe',core='genesis_plus_gx_libretro.dll',license='engine/LICENSE.txt'),
 dict(folder='splatterhouse',id='Splatterhouse3Coop',name='Splatterhouse3',exe='Splatterhouse3-Coop.exe',core='genesis_plus_gx_libretro.dll',license='engine/LICENSE.txt'),
 dict(folder='indianaJonesCoop',id='IndianaCoop',name='IndianaJones',exe='Indiana-Coop.exe',core='fceumm_libretro.dll',license='engine/Copying'),
 dict(folder='batmanReturnsCoop',id='BatmanReturnsCoop',name='BatmanReturns',exe='BatmanReturns-Coop.exe',core='snes9x2005_libretro.dll',license='engine/copyright'),
]
FORBIDDEN={'.nes','.smc','.sfc','.bin','.gen','.mdrom','.smd','.rom','.state','.sav','.srm','.brstate','.ijstate','.dll','.exe','.o','.a','.zip','.pyc','.lnk'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(root,*args):
    return subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'-C',str(root),*args])
def zip_tree(folder,path):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(folder.rglob('*')):
            if file.is_file():z.write(file,file.relative_to(folder))

def stage(game):
    root=BASE/game['folder'];work=OUT/game['name'];source=work/'source';payload=work/'payload'
    source.mkdir(parents=True,exist_ok=False);payload.mkdir()
    files=set(git(root,'ls-files','-z').decode().split('\0'))-set([''])
    files.add('coop_desktop.h')
    manifest={}
    for name in sorted(files):
        file=root/name
        if not file.is_file() or file.suffix.lower() in FORBIDDEN:continue
        if name.startswith(('diagnostics/','dist/','saves/')):continue
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
        # Ship the committed emulator defaults, not a developer's live BizHawk settings.
        if name=='bizhawk/indiana.ini':target.write_bytes(git(root,'show','HEAD:'+name))
        manifest[name]=sha(target)
    zip_tree(source,payload/'source.zip')
    assert manifest['coop_desktop.h']==sha(ROOT/'desktop/coop_desktop.h')
    (work/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return source,payload,manifest

def finish(game,source,payload,manifest):
    for name in [game['exe'],'engine/'+game['core'],game['license'],'README.md','THIRD_PARTY_NOTICES.md','LICENSE']:
        path=source/name
        if path.exists():
            target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    (payload/'START-HERE.txt').write_text(
        game['name']+' co-op - portable Windows x64\n\n'
        '1. Extract the entire ZIP. Keep engine beside the EXE.\n'
        '2. Open '+game['exe']+'.\n'
        '3. Choose your own original USA ROM. Its location is remembered.\n'
        '4. Next time, just open the EXE. The ROM is not copied.\n\n'
        'Settings > Choose ROM: select a different ROM location.\n'
        'Settings > Screen size: 1x/2x/3x/4x or fullscreen.\n'
        'Settings > Controls (F2): keyboard and Xbox-compatible gamepad bindings for P1 and P2.\n'
        'F11 / Alt+Enter: toggle fullscreen. Manual window resizing is remembered.\n'
        'Settings > Open saves and settings folder: find your saved settings and standalone saves.\n\n'
        'User files: %LOCALAPPDATA%\\Linn1024Coop\\'+game['id']+'\n'
        'No installer, compiler, Python, administrator access or separate emulator is needed to play.\n'
        'ROMs are not included. Extract compressed ROMs before selecting them.\n'
        'source.zip contains the matching source and build instructions.\n',encoding='utf-8')
    info=dict(game=game['name'],date='2026-10-27',source_base_commit=git(BASE/game['folder'],'rev-parse','HEAD').decode().strip(),
              source_archive_sha256=sha(payload/'source.zip'),exe_sha256=sha(payload/game['exe']),
              core_sha256=sha(payload/'engine'/game['core']),source_files=manifest)
    (payload/'BUILD-INFO.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    result=OUT/(game['name']+'-Coop-Portable-Windows-x64.zip')
    zip_tree(payload,result)
    with zipfile.ZipFile(result) as z:
        assert z.testzip() is None
        assert not any(Path(n).suffix.lower() in FORBIDDEN-{'.exe','.dll','.zip'} for n in z.namelist())
    print('PORTABLE:',result,flush=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for game in GAMES:
        source,payload,manifest=stage(game)
        command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(source/'build.ps1'),'-ToolchainBin',str(TOOLCHAIN)]
        log=open(source.parent/'build.log','w',encoding='utf-8')
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        jobs.append((game,source,payload,manifest,process,log))
    for game,source,payload,manifest,process,log in jobs:
        code=process.wait();log.close()
        if code:raise RuntimeError('Build failed: '+game['name']+'; see '+str(source.parent/'build.log'))
        finish(game,source,payload,manifest)
    (OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(OUT.glob('*.zip'))),encoding='ascii')

if __name__=='__main__':main()
