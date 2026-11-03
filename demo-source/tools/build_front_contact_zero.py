from pathlib import Path
import os,subprocess,json,hashlib,re
R=Path(__file__).resolve().parents[1];W=R/'work/front-contact-zero';W.mkdir(exist_ok=True)
s=(R/'src/front_forgiving.c').read_text().replace('prior>=24 && prior<=120 && gap<=24 && gap>=0','prior>=0 && prior<=120 && gap<=0 && gap>=-36').replace('(24-gap)','(0-gap)').replace(')[i]-24)',')[i])')
(R/'src/front_contact_zero.c').write_text(s)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6840','--data-loc','0x3fd8','-Wl-b_HOME=0x7ff0',str(R/'src/front_contact_zero.c'),'-o',str(W/'crash.ihx')],env=env,check=True)
mp=(W/'crash.map').read_text();prev=(R/'work/front-forgiving/crash.map').read_text()
for n in ('crash_pre','crash_post'):assert re.search(r'([0-9A-F]{8})\s+_'+n+r'\s',mp)[1]==re.search(r'([0-9A-F]{8})\s+_'+n+r'\s',prev)[1]
def mem(p):
 d={}
 for l in p.read_text().splitlines():
  b=bytes.fromhex(l[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');d.update({a+i:v for i,v in enumerate(b[4:-1])})
 return d
prior=mem(R/'work/front-forgiving/crash.ihx');data=mem(W/'crash.ihx')
for suffix in ('','-external-88h'):
 src=R/('outputs/front-forgiving'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);allowed=set()
 for a,v in data.items():
  assert 0x6840<=a<0x7000;at=188*16384+8192+a-0x6000;assert old[at]==prior.get(a,255);rom[at]=v;allowed.add(at)
 start=206*16384+8192;at=old.index(bytes.fromhex('7dd618'),start,start+0x90)+2;rom[at]=0;allowed.add(at)
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/front-contact-zero'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom);(out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),front_threshold=0,overshoot_limit=36,lateral=28,scope='Forward crossing only, player-favoring contact distance; camera and art unchanged.'),indent=2))
s=(R/'tools/capture_front_forgiving.py').read_text().replace('front-forgiving','front-contact-zero');(R/'tools/capture_front_contact_zero.py').write_text(s)
