"""Drive real portable EXEs: ROM picker, remembered paths, controls and display."""
import configparser
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'dist/desktop-verification'
GAMES=[
 ('batmanReturnsCoop','BatmanReturns-Coop.exe','snes9x2005_libretro.dll','Batman Returns (U) [!].smc','BatmanReturnsCoop',4,0),
 ('indianaJonesCoop','Indiana-Coop.exe','fceumm_libretro.dll','Young Indiana Jones Chronicles, The (USA).nes','IndianaCoop',4,8),
 ('aladdinGameCoop','Aladdin-Coop.exe','genesis_plus_gx_libretro.dll','Aladdin_(U)_[!].bin','AladdinCoop',6,8),
 ('splatterhouse','Splatterhouse3-Coop.exe','genesis_plus_gx_libretro.dll','Splatterhouse 3 (USA).md','Splatterhouse3Coop',6,8),
]
u=C.WinDLL('user32',use_last_error=True)
u.SetProcessDPIAware()
u.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
u.SendMessageW.restype=W.LPARAM
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
u.GetDlgItem.argtypes=[W.HWND,C.c_int];u.GetDlgItem.restype=W.HWND
u.SetDlgItemTextW.argtypes=[W.HWND,C.c_int,W.LPCWSTR]
u.SetWindowTextW.argtypes=[W.HWND,W.LPCWSTR]
u.GetDlgCtrlID.argtypes=[W.HWND]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
u.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
u.GetWindowLongW.argtypes=[W.HWND,C.c_int]
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]

def windows(pid):
    result=[]
    @CB
    def visit(hwnd,_):
        owner=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(owner))
        if owner.value==pid:
            name=C.create_unicode_buffer(512);cls=C.create_unicode_buffer(128)
            u.GetWindowTextW(hwnd,name,512);u.GetClassNameW(hwnd,cls,128)
            result.append((hwnd,cls.value,name.value))
        return True
    u.EnumWindows(visit,0)
    return result

def wait(process,predicate,timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        for item in windows(process.pid):
            if predicate(item):return item[0]
        if process.poll() is not None:raise AssertionError(('EXE exited',process.returncode))
        time.sleep(.05)
    raise AssertionError(('Window timeout',windows(process.pid)))

def command(hwnd,id):u.SendMessageW(hwnd,0x111,id,0)
def close(process,hwnd):u.PostMessageW(hwnd,0x10,0,0);assert process.wait(10)==0
def client(hwnd):
    r=W.RECT();assert u.GetClientRect(hwnd,C.byref(r));return r.right,r.bottom
def config(path):
    b=path.read_bytes();p=configparser.ConfigParser();p.read_string(b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8-sig'));return p
def pick(dialog,path):
    time.sleep(.3)
    edits=[]
    @CB
    def child(hwnd,_):
        cls=C.create_unicode_buffer(128);u.GetClassNameW(hwnd,cls,128)
        if cls.value=='Edit' and u.GetDlgCtrlID(hwnd)==1148:edits.append(hwnd)
        return True
    u.EnumChildWindows.argtypes=[W.HWND,CB,W.LPARAM]
    u.EnumChildWindows(dialog,child,0)
    assert edits, 'No file-name edit in ROM picker'
    # Explorer's file-name model needs edit notifications from typing;
    # WM_SETTEXT changes only the edit's visible text, not the selection.
    u.SendMessageW(edits[0],0xB1,0,-1)  # replace any remembered filename
    for char in str(path):u.SendMessageW(edits[0],0x102,ord(char),1)
    u.PostMessageW(dialog,0x111,1,int(u.GetDlgItem(dialog,1)))

def verify(game,source=None):
    folder,exe,dll,rom_name,main_class,jump_row,jump_bit=game
    source=Path(source) if source else ROOT.parent/folder
    stage=WORK/folder/'app';settings=WORK/folder/'settings'
    stage.mkdir(parents=True,exist_ok=True);(stage/'engine').mkdir(exist_ok=True)
    if (settings/'launcher.ini').exists():(settings/'launcher.ini').unlink()
    shutil.copy2(source/exe,stage/exe);shutil.copy2(source/'engine'/dll,stage/'engine'/dll)
    external=WORK/folder/'external';external.mkdir(exist_ok=True)
    rom=external/('ROM \u0411\u044d\u0442\u043c\u0435\u043d [USA]'+Path(rom_name).suffix)
    if not rom.exists():rom.hardlink_to(ROOT.parent/folder/rom_name)
    bad=external/'wrong.rom';bad.write_bytes(b'not the original game')
    # Native hash checks must reject an invalid choice and never save that path.
    rejected=subprocess.run([str(stage/exe),'--test','2','--rom',str(bad),
                             '--settings-dir',str(settings)],cwd=stage,timeout=15)
    assert rejected.returncode!=0
    assert not config(settings/'launcher.ini').has_option('Game','ROM')
    # Actual first run with no ROM supplied: drive the common file dialog.
    process=subprocess.Popen([str(stage/exe),'--settings-dir',str(settings)],cwd=stage)
    try:
        dialog=wait(process,lambda x:x[1]=='#32770' and x[2].startswith('Choose your original'))
        pick(dialog,rom)
        main=wait(process,lambda x:x[1]==main_class)
        assert config(settings/'launcher.ini')['Game']['ROM']==str(rom)
        assert not (stage/rom_name).exists(), 'Launcher copied ROM into the download'
        command(main,9012);time.sleep(.15);size=client(main)
        assert min(size)>200
        command(main,9003);assert u.GetWindowLongW(main,-16)&0x80000000
        command(main,9003);assert client(main)==size
        command(main,9002)
        cls='IndianaControls' if folder=='indianaJonesCoop' else 'CoopDesktopControls'
        controls=wait(process,lambda x:x[1]==cls)
        command(controls,200+jump_row)
        u.SendMessageW(controls,0x100,ord('Z'),0)
        path=settings/('controls.ini' if folder=='indianaJonesCoop' else 'launcher.ini')
        saved=config(path)
        if folder=='indianaJonesCoop':assert saved['Player2']['jump']=='90'
        else:assert saved['P2Keyboard'][str(jump_bit)]=='90'
        u.SendMessageW(controls,0x10,0,0)
        close(process,main)
        process=subprocess.Popen([str(stage/exe),'--settings-dir',str(settings)],cwd=stage)
        main=wait(process,lambda x:x[1]==main_class and client(x[0])==size)
        assert client(main)==size, ('Size not remembered',folder,client(main),size)
        assert not any(x[1]=='#32770' for x in windows(process.pid))
        # Fullscreen survives closing/reopening, and normal window size is retained.
        command(main,9003)
        close(process,main)
        process=subprocess.Popen([str(stage/exe),'--settings-dir',str(settings)],cwd=stage)
        main=wait(process,lambda x:x[1]==main_class and u.GetWindowLongW(x[0],-16)&0x80000000)
        command(main,9003)
        assert client(main)==size
        # A moved ROM can be located again; the new location replaces the old one.
        moved=rom.with_name('Moved '+rom.name)
        if not moved.exists():moved.hardlink_to(rom)
        u.PostMessageW(main,0x111,9001,0)
        dialog=wait(process,lambda x:x[1]=='#32770' and x[2].startswith('Choose your original'))
        pick(dialog,moved)
        end=time.monotonic()+5
        while config(settings/'launcher.ini')['Game']['ROM']!=str(moved) and time.monotonic()<end:time.sleep(.05)
        assert config(settings/'launcher.ini')['Game']['ROM']==str(moved)
        close(process,main)
        moved.unlink() # only the isolated test hardlink; user's original is untouched
        process=subprocess.Popen([str(stage/exe),'--settings-dir',str(settings)],cwd=stage)
        notice=wait(process,lambda x:x[1]=='#32770' and x[2] and not x[2].startswith('Choose your original'))
        time.sleep(.15)
        u.PostMessageW(notice,0x10,0,0)
        dialog=wait(process,lambda x:x[1]=='#32770' and x[2].startswith('Choose your original'))
        pick(dialog,rom)
        main=wait(process,lambda x:x[1]==main_class and client(x[0])==size)
        close(process,main)
        assert config(settings/'launcher.ini')['Game']['ROM']==str(rom)
        print('PASS',folder,'real ROM picker, Unicode/external ROM remembered, no ROM copy, size/fullscreen, keyboard binding, relaunch, fullscreen persistence, changing/missing ROM recovery',flush=True)
    finally:
        if process.poll() is None:process.terminate();process.wait(10)
    # Cancelling first-run ROM selection exits normally.
    cancel_settings=WORK/folder/'cancel-settings'
    process=subprocess.Popen([str(stage/exe),'--settings-dir',str(cancel_settings)],cwd=stage)
    try:
        dialog=wait(process,lambda x:x[1]=='#32770' and x[2].startswith('Choose your original'))
        u.PostMessageW(dialog,0x10,0,0);assert process.wait(10)==0
    finally:
        if process.poll() is None:process.terminate();process.wait(10)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packaged',type=Path,help='Portable build output folder containing the four payload folders')
    args=parser.parse_args()
    names={'batmanReturnsCoop':'BatmanReturns','indianaJonesCoop':'IndianaJones','aladdinGameCoop':'Aladdin','splatterhouse':'Splatterhouse3'}
    if args.packaged:WORK=ROOT/'dist/desktop-verification-packaged'
    for game in GAMES:verify(game,args.packaged/names[game[0]]/'payload' if args.packaged else None)


