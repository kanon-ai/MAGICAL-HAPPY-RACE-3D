"""Isolated tunnel renderer experiment; no asset or gameplay mutations."""
from pathlib import Path
import subprocess,os,re,json,hashlib
R=Path(__file__).resolve().parents[1]
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 work=R/('work/tunnel-segmented'+suffix);work.mkdir(exist_ok=True)
 hdr=R/('work/arch-series-lod'+suffix)/'gate_addresses.h'
 assert hdr.exists(),hdr
 (work/'gate_addresses.h').write_bytes(hdr.read_bytes())
 env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f5','-Wl-b_HOME=0x7800','-I',str(work),'-DROCK_ARCH','-DARCH_SERIES','-DARCH_LOD',str(R/'src/drive_tunnel_segmented.c'),'-o',str(work/'gates.ihx')],env=env,check=True)
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
 late=int(re.search(r'([0-9A-F]{8})\s+_draw_late_tunnel\s',(work/'gates.map').read_text())[1],16)
 # B260 lies after the 304-byte B130 beacon helper in the retired mirror body.
 assert old[off(0xb02c):off(0xb02c)+3]==bytes.fromhex('c335a9')
 assert old[off(0xb260):off(0xb260)+17]==bytes.fromhex('66fc23dd75f7dd74f8dd7ef0dd77fbdd36')
 assert old[off(0xca23):off(0xca23)+3]==bytes.fromhex('cda9bb')
 stub=bytes.fromhex('cda9bb3a4fe2fe14c0dde5fde53ed2320060cd')+late.to_bytes(2,'little')+bytes.fromhex('3efc320060fde1dde1c9')
 assert 0xb260+len(stub)<0xb351
 rom[off(0xb260):off(0xb260)+len(stub)]=stub
 rom[off(0xca23):off(0xca23)+3]=bytes.fromhex('cd60b2')
 from structure_vram_layout import validate,ART
 validate(dict(ART, tunnel_concrete=(192,754,64,14)))
 material=(R/'assets/tunnel-material-v1/concrete-64x14.bin').read_bytes();assert len(material)==896
 texture_offsets=set()
 for y in range(14):
  v=(754+y-512)*256+192;at=(4+v//8192)*16384+8192+v%8192
  rom[at:at+64]=material[y*64:(y+1)*64];texture_offsets.update(range(at,at+64))
 changed=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
 assert all(bank<=i<bank+8192 or ptr<=i<ptr+2 or off(0xb260)<=i<off(0xb260)+len(stub) or off(0xca23)<=i<off(0xca23)+3 or i in texture_offsets for i in changed)
 assert len(rom)==4194304
 out=R/('outputs/six-route-tunnel-segmented'+suffix);out.mkdir(exist_ok=True)
 (out/path.name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 report=dict(bytes=len(rom),code_bytes=len(mem),entry=entry,sha256=hashlib.sha256(rom).hexdigest(),runtime_verified=False,adopted=False,scope='Forest short tunnel geometry only; texture and native passage review pending.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
