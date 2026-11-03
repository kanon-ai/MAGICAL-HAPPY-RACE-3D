from pathlib import Path
import os,re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/passing-props';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f6','-Wl-b_HOME=0x7800',str(R/'src/passing_props.c'),'-o',str(W/'props.ihx')],env=env,check=True)
mem={}
for line in (W/'props.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  a=int.from_bytes(b[1:3],'big')
  for i,v in enumerate(b[4:-1]):assert 0x6000<=a+i<0x8000;mem[a+i]=v
entry=int(re.search(r'([0-9A-F]{8})\s+_shift_passing_props\s',(W/'props.map').read_text())[1],16)
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-bounds'+suffix);o=R/('outputs/six-route-passing-props'+suffix);o.mkdir(exist_ok=True);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);bank=211*16384+8192;assert old[bank:bank+8192]==b'\xff'*8192
 for a,v in mem.items():rom[bank+a-0x6000]=v
 assert old[off(0x85e6):off(0x85e6)+3]==bytes.fromhex('c3ec36')
 stub=bytes.fromhex('cdec36dde5fde53ed3320060cd')+entry.to_bytes(2,'little')+bytes.fromhex('3efc320060fde1dde1c9');assert len(stub)<=0x27
 rom[off(0xa9d0):off(0xa9d0)+len(stub)]=stub;rom[off(0x85e6):off(0x85e6)+3]=bytes.fromhex('c3d0a9')
 (o/p.name).write_bytes(rom)
 for f in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(o/f).write_bytes((src/f).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),entry=entry,helper_bytes=len(mem),playable_adoption=False,native_validation=False),indent=2));print(o.name,len(mem),entry)
