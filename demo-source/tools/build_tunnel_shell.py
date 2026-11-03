"""Isolated tunnel renderer experiment; no asset or gameplay mutations."""
from pathlib import Path
import subprocess,os,re,json,hashlib
R=Path(__file__).resolve().parents[1]
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 work=R/('work/tunnel-shell'+suffix);work.mkdir(exist_ok=True)
 hdr=R/('work/arch-series-lod'+suffix)/'gate_addresses.h'
 assert hdr.exists(),hdr
 (work/'gate_addresses.h').write_bytes(hdr.read_bytes())
 env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f5','-Wl-b_HOME=0x7800','-I',str(work),'-DROCK_ARCH','-DARCH_SERIES','-DARCH_LOD',str(R/'src/drive_tunnel_trial.c'),'-o',str(work/'gates.ihx')],env=env,check=True)
 mem={}
 for line in (work/'gates.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   at=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):assert 0x6000<=at+i<0x8000;mem[at+i]=v
 entry=int(re.search(r'([0-9A-F]{8})\s+_draw_drive_gate\s',(work/'gates.map').read_text())[1],16)
 src=R/('outputs/six-route-passing-props-shared'+suffix);path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 bank=210*16384+8192
 rom[bank:bank+8192]=bytes([255])*8192
 for a,v in mem.items():rom[bank+a-0x6000]=v
 ptr=off(0xa94f);assert old[ptr-1]==0xcd
 rom[ptr:ptr+2]=entry.to_bytes(2,'little')
 changed=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
 assert all(bank<=i<bank+8192 or ptr<=i<ptr+2 for i in changed)
 assert len(rom)==4194304
 out=R/('outputs/six-route-tunnel-shell'+suffix);out.mkdir(exist_ok=True)
 (out/path.name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 report=dict(bytes=len(rom),code_bytes=len(mem),entry=entry,sha256=hashlib.sha256(rom).hexdigest(),runtime_verified=False,adopted=False,scope='Forest short tunnel geometry only; texture and native passage review pending.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
