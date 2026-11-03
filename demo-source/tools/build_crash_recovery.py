"""Guarded crash-only overlay of accepted internal/external ROMs."""
from pathlib import Path
import os,subprocess,re,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/crash-recovery';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6840','--data-loc','0x3fd8','-Wl-b_HOME=0x7ff0',str(R/'src/crash_recovery.c'),'-o',str(W/'crash.ihx')],env=env,check=True)
mp=(W/'crash.map').read_text()
def sym(n):return int(re.search(r'([0-9A-F]{8})\s+_'+n+r'\s',mp)[1],16)
def asm(name,source):
 p=W/(name+'.asm');p.write_text(source)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(p),str(p.with_suffix('.bin'))],check=True)
 return p.with_suffix('.bin').read_bytes()
gates=asm('gates',f'''org 03fa8h
 ld a,188
 ld (06000h),a
 call {sym('crash_pre')}
 or a
 jr nz,back
 ld a,251
 ld (06000h),a
 jp 0324ch
back:
 ld a,251
 ld (06000h),a
 ret
blink:
 ld a,(03fdah)
 or a
 jr z,visible
 ld a,(57950)
 and 4
 ret nz
visible:
 ld c,0
 ld a,8
 jp 02ef9h
''')
assert len(gates)<=48
post=asm('post',f'org 06800h\n call {sym("crash_post")}\n jp 03fbbh\n')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6b10','--data-loc','0x3fd8','-Wl-b_HOME=0x7100',str(R/'src/crash_hud.c'),'-o',str(W/'hud.ihx')],env=env,check=True)
hudmap=(W/'hud.map').read_text();hud=int(re.search(r'([0-9A-F]{8})\s+_crash_hud\s',hudmap)[1],16)
for suffix in ('','-external-88h'):
 src=R/('outputs/truck-clean-side'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes()
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 rom=bytearray(old);allowed=set()
 def put(at,data,expected=None):
  if expected is not None:assert old[at:at+len(data)]==expected,(hex(at),old[at:at+len(data)].hex())
  rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 v=214*16384+8192
 put(v+0x36b2-0x2400,bytes.fromhex('cda83f'),bytes.fromhex('cd4c32'))
 put(v+0x35df-0x2400,bytes.fromhex('3ebc320060c30068'),bytes.fromhex('2a5ee223225ee2c9'))
 # Extend the existing model bootstrap by precisely the 88-byte unused tail.
 pat=bytes.fromhex('11d43d21d47901d401edb0');at=old.find(pat);assert at>=0 and old.find(pat,at+1)<0
 put(at+7,(556).to_bytes(2,'little'),(468).to_bytes(2,'little'))
 put(195*16384+8192+0x1ba8,gates.ljust(48,b'\0')+bytes(40),bytes([255])*88)
 # Retain original colour selector, then optionally blink during immunity.
 put(v+0x2ef5-0x2400,bytes.fromhex('c3f93b00'),bytes.fromhex('cdceca00'))
 put(v+0x3bf9-0x2400,bytes.fromhex('cdcecac3c13f'),bytes([255])*6)
 put(188*16384+8192+0x800,post,bytes([255])*len(post))
 # Chain after the current centered timer without changing its clock logic.
 hb=200*16384+8192;timer=old[hb+0x2cf:hb+0x2d2];assert timer[0]==0xc3
 put(hb+0xb00,b'\xcd'+timer[1:]+b'\xc3'+hud.to_bytes(2,'little'),bytes([255])*6)
 put(hb+0x2cf,bytes.fromhex('c3006b'),timer)
 for line in (W/'hud.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');data=b[4:-1];assert 0x6b10<=a and a+len(data)<0x7200
   put(hb+a-0x6000,data,bytes([255])*len(data))
 for line in (W/'crash.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');data=b[4:-1];assert 0x6840<=a and a+len(data)<=0x8000
   put(188*16384+8192+a-0x6000,data,bytes([255])*len(data))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/crash-recovery'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 report=dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),changed_bytes=sum(a!=b for a,b in zip(old,rom)),pre=sym('crash_pre'),post=sym('crash_post'),state=0x3fd8,scope='Crash recovery only; no timer, rear collision, hull, scenery or audio changes',native_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
