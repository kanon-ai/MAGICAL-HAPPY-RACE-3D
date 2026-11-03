"""Guarded rendering-only trial on the validated alpine baseline."""
from pathlib import Path
import subprocess, sys, os, re, json, hashlib
R=Path(__file__).resolve().parents[1]
# Existing shared assets are preserved.
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 w=R/('work/rock-bore-shadow'+suffix);w.mkdir(exist_ok=True)
 (w/'gate_addresses.h').write_bytes((R/('work/tunnel-depth-fast'+suffix)/'gate_addresses.h').read_bytes())
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f5','-Wl-b_HOME=0x7ee0','-I',str(w),'-DROCK_ARCH','-DARCH_SERIES','-DARCH_LOD',str(R/'src/drive_rock_bore_shadow.c'),'-o',str(w/'gates.ihx')],env=env,check=True)
 mem={}
 for line in (w/'gates.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):
    assert 0x6000<=a+i<0x8000 and a+i not in mem
    mem[a+i]=v
 mapping=(w/'gates.map').read_text()
 def symbol(n):return int(re.search(r'([0-9A-F]{8})\s+_'+n+r'\s',mapping)[1],16)
 src=R/('outputs/six-route-city-tunnel-exit-trim-early-tree'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 donor=next((R/('outputs/six-route-tunnel-depth-fast'+suffix)).glob('*.rom')).read_bytes()
 bank=210*16384+8192;assert len(old)==4194304
 assert old[off(0xb260):off(0xb260)+3]==bytes.fromhex('cda9bb')
 assert old[off(0xca23):off(0xca23)+3]==bytes.fromhex('cd60b2')
 assert old[off(0xa94e)]==0xcd
 rom[bank:bank+8192]=b'\xff'*8192
 for a,v in mem.items():rom[bank+a-0x6000]=v
 rom[off(0xa94f):off(0xa94f)+2]=symbol('draw_drive_gate').to_bytes(2,'little')
 # Keep original object pass, then allow forest20 and city39/40 late drawing.
 stub=bytes.fromhex('cda9bb3a4fe2fe0c2809fe142805d627fe02d0dde5fde53ed2320060cd')+symbol('draw_late_tunnel').to_bytes(2,'little')+bytes.fromhex('3efc320060fde1dde1c9')
 assert len(stub)<=0xb28a-0xb260
 rom[off(0xb260):off(0xb260)+len(stub)]=stub
 changed=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
 assert len(rom)==4194304 and all(bank<=i<bank+8192 or off(0xa94f)<=i<off(0xa94f)+2 or off(0xb260)<=i<off(0xb260)+len(stub) for i in changed)
 out=R/('outputs/six-route-rock-bore-shadow'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),code_bytes=len(mem),changed_bytes=len(changed),native_verified=False,adopted=False,scope='Selector-only intermediate; interior material not embedded. Do not distribute; use shaded builder.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
