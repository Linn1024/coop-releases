"""Sample actual Aladdin window repaints and resize/fullscreen GDI resource use."""
import ctypes as C
from ctypes import wintypes as W
import subprocess,time,sys
from pathlib import Path
import verify_desktop as ui
u=ui.u
u.SetForegroundWindow.argtypes=[W.HWND]
u.GetGuiResources.argtypes=[W.HANDLE,W.DWORD];u.GetGuiResources.restype=W.DWORD
kernel=C.WinDLL('kernel32');kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];kernel.OpenProcess.restype=W.HANDLE
kernel.CloseHandle.argtypes=[W.HANDLE]

def verify(exe,label):
 settings=ui.ROOT/'dist/aladdin-render-verification'/label
 p=subprocess.Popen([str(exe),'--rom',str(ui.ROOT.parent/'aladdinGameCoop/Aladdin_(U)_[!].bin'),'--settings-dir',str(settings)])
 try:
  hwnd=ui.wait(p,lambda x:x[1]=='AladdinCoop')
  ui.command(hwnd,9012);u.SetForegroundWindow(hwnd);time.sleep(8)
  from PIL import ImageGrab,ImageStat
  point=W.POINT(0,0);u.ClientToScreen.argtypes=[W.HWND,C.POINTER(W.POINT)]
  u.ClientToScreen(hwnd,C.byref(point))
  brightness=[]
  for _ in range(90):
   frame=ImageGrab.grab(bbox=(point.x,point.y,point.x+640,point.y+448))
   brightness.append(sum(ImageStat.Stat(frame.resize((32,24))).mean)/3)
  blank=sum(value<5 for value in brightness)
  process=kernel.OpenProcess(0x400,False,p.pid)
  snapshots=[]
  for batch in range(3):
   for _ in range(12):
    ui.command(hwnd,9011);u.SendMessageW(hwnd,0xF,0,0)
    ui.command(hwnd,9012);u.SendMessageW(hwnd,0xF,0,0)
    ui.command(hwnd,9003);u.SendMessageW(hwnd,0xF,0,0)
    ui.command(hwnd,9003);u.SendMessageW(hwnd,0xF,0,0)
   time.sleep(.1);snapshots.append(u.GetGuiResources(process,0))
  kernel.CloseHandle(process)
  before,after=snapshots[1:]
  assert after<=before+1,snapshots
  assert ui.client(hwnd)==(640,448)
  if label=='fixed':assert u.SendMessageW(hwnd,0x14,0,0)==1,'WM_ERASEBKGND must be handled'
  print(label,'blank frames:',blank,'of',len(brightness),'brightness range:',round(min(brightness),2),round(max(brightness),2),'GDI handles:',before,after,flush=True)
  if label=='fixed':assert blank==0,'Black frames exposed during repaint'
  ui.close(p,hwnd)
 finally:
  if p.poll() is None:p.terminate();p.wait(10)

if __name__=='__main__':
 exe=Path(sys.argv[1]) if len(sys.argv)>1 else ui.ROOT.parent/'aladdinGameCoop/Aladdin-Coop.exe'
 verify(exe,sys.argv[2] if len(sys.argv)>2 else 'fixed')
