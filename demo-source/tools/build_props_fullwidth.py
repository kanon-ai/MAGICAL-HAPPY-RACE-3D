from pathlib import Path
import os,re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];w=R/'work/props-fullwidth';w.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6800','--data-loc','0xf6f6','-Wl-b_HOME=0x7d00',str(R/'src/passing_props_fullwidth.c'),'-o',str(w/'props.ihx')],env=env,check=True)
def load(p):
 mem={}
 for line in p.read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):assert 0x6800<=a+i<0x8000;mem[a+i]=v
 return mem
oldmem=load(R/'work/passing-props-memo/props.ihx');newmem=load(w/'props.ihx')
entry=int(re.search(r'([0-9A-F]{8})\s+_shift_passing_props\s',(w/'props.map').read_text())[1],16)
oldentry=int(re.search(r'([0-9A-F]{8})\s+_shift_passing_props\s',(R/'work/passing-props-memo/props.map').read_text())[1],16)
for suffix,sha in [('', '9faf12daa2de2ceaf6f0f98e84b548abe470aa0139e73e001cc07fd52e8457a4'),('-external-88h','ebed012879d13cf08c9a82e087e7c358dab77fbec5b4d595124bb8dd5a85ddea')]:
 src=R/('outputs/six-route-city-tunnel-exit-trim-early-tree'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();assert hashlib.sha256(old).hexdigest()==sha
 rom=bytearray(old);bank=211*16384+8192
 for a in oldmem.keys()|newmem.keys():
  at=bank+a-0x6000;assert old[at]==oldmem.get(a,255),(hex(a),old[at],oldmem.get(a,255))
  rom[at]=newmem.get(a,255)
 assert old[bank+0xeb:bank+0xee]==b'\xc3'+oldentry.to_bytes(2,'little')
 rom[bank+0xeb:bank+0xee]=b'\xc3'+entry.to_bytes(2,'little')
 assert len(rom)==4194304
 out=R/('outputs/six-route-props-fullwidth'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps({'source_sha256':sha,'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'code_bytes':len(newmem),'native_verified':False},indent=2))
print('Both isolated full-width trials built',len(newmem))
