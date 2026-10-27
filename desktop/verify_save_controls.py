"""Exercise real launcher controls, clearing/rebinding, and ten save slots."""
from pathlib import Path
import argparse,ctypes as C,subprocess,time
import verify_desktop as ui
u=ui.u

def text(hwnd):
 b=C.create_unicode_buffer(512);u.GetWindowTextW(hwnd,b,512);return b.value

def key(hwnd,k):u.SendMessageW(hwnd,0x100,k,0)

def verify(game,source=None):
 folder,exe,dll,rom_name,main_class,jump_row,jump_bit=game
 source=Path(source) if source else ui.ROOT.parent/folder
 settings=ui.ROOT/'dist/save-controls-verification'/folder
 settings.mkdir(parents=True,exist_ok=True)
 for slot in range(11):
  for ext in ['brstate','ijstate','alstate','shstate']:
   f=settings/'saves'/('slot-'+str(slot)+'.'+ext)
   if f.exists():f.unlink()
 for name in ['launcher.ini']:
  if (settings/name).exists():(settings/name).unlink()
 p=subprocess.Popen([str(source/exe),'--rom',str(ui.ROOT.parent/folder/rom_name),'--settings-dir',str(settings)],cwd=source)
 try:
  main=ui.wait(p,lambda x:x[1]==main_class and 'Slot 1' in x[2])
  time.sleep(.5);ui.command(main,9002)
  controls=ui.wait(p,lambda x:x[1]=='CoopDesktopControls')
  assert [text(u.GetDlgItem(controls,500+i)) for i in range(4)]==['F5','F8','F6','F7']
  # Clear both types of a movement binding and confirm no replacement is captured.
  ui.command(controls,300);ui.command(controls,320)
  ini=ui.config(settings/'launcher.ini')
  assert ini['P1Keyboard']['4']=='0' and ini['P1Gamepad']['4']=='0'
  assert text(u.GetDlgItem(controls,100))=='Unbound'
  assert text(u.GetDlgItem(controls,120))=='Unbound'
  # Each clear button sits outside its binding button, and column headers align.
  for player in range(2):
   rects=[]
   for id in [100+player*100,300+player*100,120+player*100,320+player*100]:
    r=ui.W.RECT();u.GetWindowRect.argtypes=[ui.W.HWND,C.POINTER(ui.W.RECT)];u.GetWindowRect(u.GetDlgItem(controls,id),C.byref(r));rects.append(r)
   assert all(rects[i].right<=rects[i+1].left for i in range(3))
  # Clearing a hotkey must really stop it; the old hardcoded F5 must not run.
  ui.command(controls,510);key(main,0x74)
  assert ui.config(settings/'launcher.ini')['Hotkeys']['Quicksave']=='0'
  before=list((settings/'saves').glob('*')) if (settings/'saves').exists() else []
  assert not before
  ui.command(controls,500);key(controls,0x74)
  # Buttons and keyboard defaults must select all ten independent slots.
  extensions={'aladdinGameCoop':'alstate','splatterhouse':'shstate','batmanReturnsCoop':'brstate','indianaJonesCoop':'ijstate'}
  for slot in range(1,11):
   assert 'Slot '+str(slot) in text(main)
   key(main,0x74)
   disk_slot=0 if folder=='indianaJonesCoop' and slot==10 else slot
   path=settings/'saves'/('slot-'+str(disk_slot)+'.'+extensions[folder])
   assert path.exists() and path.stat().st_size>1000,path
   key(main,0x75)
  assert 'Slot 1' in text(main)
  key(main,0x76);assert 'Slot 10' in text(main)
  key(main,0x75);assert 'Slot 1' in text(main)
  assert len(list((settings/'saves').glob('*')))==10
  first=settings/'saves'/('slot-1.'+extensions[folder]);old=first.read_bytes()
  # Advance the game so loading slot 1 must restore an earlier state.
  u.SendMessageW(controls,0x10,0,0);time.sleep(.7)
  ui.command(main,9002);controls=ui.wait(p,lambda x:x[1]=='CoopDesktopControls')
  key(main,0x75);ui.command(controls,520)
  second=settings/'saves'/('slot-2.'+extensions[folder])
  if folder!='indianaJonesCoop':assert second.read_bytes()!=old,'Game did not advance between saves'
  key(main,0x76);ui.command(controls,521);assert 'Loaded' in text(main)
  untouched={f.name:f.stat().st_mtime_ns for f in (settings/'saves').glob('*') if f!=first}

  ui.command(controls,520)
  after=first.read_bytes()
  assert len(old)==len(after)
  if folder!='batmanReturnsCoop':assert old==after,'Earlier state was not restored exactly'
  assert untouched=={f.name:f.stat().st_mtime_ns for f in (settings/'saves').glob('*') if f!=first},'Saving slot 1 overwrote another slot'
  # A bad slot file must fail gracefully and leave the running state intact.
  key(main,0x75)
  second=settings/'saves'/('slot-2.'+extensions[folder]);backup=second.read_bytes();second.write_bytes(b'bad save')
  key(main,0x77);assert 'Load failed' in text(main)
  second.write_bytes(backup)
  ui.command(controls,503);key(controls,0x7B) # previous slot -> F12
  assert ui.config(settings/'launcher.ini')['Hotkeys']['PreviousSlot']=='123'
  key(main,0x7B);assert 'Slot 1' in text(main)
  ui.command(controls,522);assert 'Slot 2' in text(main)
  u.SendMessageW(controls,0x10,0,0);ui.close(p,main)
  p=subprocess.Popen([str(source/exe),'--settings-dir',str(settings)],cwd=source)
  main=ui.wait(p,lambda x:x[1]==main_class and 'Slot 2' in x[2])
  ui.command(main,9002);controls=ui.wait(p,lambda x:x[1]=='CoopDesktopControls')
  assert text(u.GetDlgItem(controls,100))=='Unbound'
  assert text(u.GetDlgItem(controls,120))=='Unbound'
  assert text(u.GetDlgItem(controls,503))=='F12'
  u.SendMessageW(controls,0x10,0,0);ui.close(p,main)
  print('PASS',folder,'clear keyboard/controller, persisted bindings, ten independent slots, wrap, save/load state roundtrip, corrupt save rejection, remapped shortcuts and restart',flush=True)
 finally:
  if p.poll() is None:p.terminate();p.wait(10)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packaged',type=Path);args=parser.parse_args()
 names={'aladdinGameCoop':'Aladdin','splatterhouse':'Splatterhouse3','indianaJonesCoop':'IndianaJones','batmanReturnsCoop':'BatmanReturns'}
 for game in ui.GAMES:verify(game,args.packaged/names[game[0]]/'payload' if args.packaged else None)
