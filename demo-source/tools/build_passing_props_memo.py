from pathlib import Path
import os,re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/passing-props-memo';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6800','--data-loc','0xf6f6','-Wl-b_HOME=0x7d00',str(R/'src/passing_props_memo.c'),'-o',str(W/'props.ihx')],env=env,check=True)
mem={}
for line in (W/'props.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  a=int.from_bytes(b[1:3],'big')
  for i,v in enumerate(b[4:-1]):assert 0x6000<=a+i<0x8000;mem[a+i]=v
entry=int(re.search(r'([0-9A-F]{8})\s+_shift_passing_props\s',(W/'props.map').read_text())[1],16)
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-forest-grove-art'+suffix);o=R/('outputs/six-route-passing-props-memo'+suffix);o.mkdir(exist_ok=True);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);bank=211*16384+8192
 for a,v in mem.items():
  assert 0x6800<=a<0x8000 and old[bank+a-0x6000]==255,(a,old[bank+a-0x6000])
  rom[bank+a-0x6000]=v
 assert old[bank+0xeb:bank+0xee]==bytes.fromhex('cdee61')
 rom[bank+0xeb:bank+0xee]=b'\xc3'+entry.to_bytes(2,'little')
 (o/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(o/f.name).write_bytes(f.read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),entry=entry,helper_bytes=len(mem),native_validation=False),indent=2));print(o.name,len(mem),entry)
