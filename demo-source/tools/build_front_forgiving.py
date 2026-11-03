from pathlib import Path
import os,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/front-forgiving';W.mkdir(exist_ok=True)
s=(R/'src/shared_contact.c').read_text().replace('prior>=40 && prior<=120 && gap<=40','prior>=24 && prior<=120 && gap<=24').replace('(40-gap)','(24-gap)').replace(')[i]-40)',')[i]-24)')
assert s!=(R/'src/shared_contact.c').read_text();(R/'src/front_forgiving.c').write_text(s)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6840','--data-loc','0x3fd8','-Wl-b_HOME=0x7ff0',str(R/'src/front_forgiving.c'),'-o',str(W/'crash.ihx')],env=env,check=True)
def load(p):
 d={}
 for l in p.read_text().splitlines():
  b=bytes.fromhex(l[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');d.update({a+i:v for i,v in enumerate(b[4:-1])})
 return d
before=load(R/'work/shared-contact/crash.ihx');after=load(W/'crash.ihx');assert before.keys()==after.keys()
delta={a:(before[a],after[a]) for a in before if before[a]!=after[a]};print(delta);assert len(delta)<=6
for suffix in ('','-external-88h'):
 src=R/('outputs/truck-wheel-order'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256'];rom=bytearray(old);changes=[]
 for a,(v,w) in delta.items():
  at=188*16384+8192+a-0x6000;assert old[at]==v;rom[at]=w;changes.append(at)
 start=206*16384+8192;pattern=bytes.fromhex('7dd628');at=old.index(pattern,start,start+0x90)+2;assert old.count(pattern,start,start+0x90)==1;rom[at]=24;changes.append(at)
 assert all(i in changes for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/front-forgiving'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),front_threshold_before=40,front_threshold_after=24,lateral_threshold=28,changed_offsets=changes,scope='Front contact threshold and held minimum gap only. Camera, lateral hull, crash/recovery, radio and art unchanged.'),indent=2))
s=(R/'tools/capture_camera_restored.py').read_text().replace('outputs/camera-restored-driving-','outputs/front-forgiving-driving-').replace('outputs/camera-restored','outputs/front-forgiving').replace('key 0 16','key 1 1');(R/'tools/capture_front_forgiving.py').write_text(s)
s=(R/'tools/verify_shared_contact_native.py').read_text().replace('outputs/shared-native','outputs/front-forgiving-native').replace('outputs/shared-contact','outputs/front-forgiving').replace('((60,41),(60,40),(60,39),(60,24),(60,4),(35,20),(16380,0))','((60,41),(60,40),(60,25),(60,24),(60,23),(35,20),(16380,0))').replace('hit=40<=prior<=120 and 0<=gap<=40','hit=24<=prior<=120 and 0<=gap<=24').replace('5000+gap-40','5000+gap-24').replace('for ext in (False,True):','for ext in (False,):');(R/'tools/verify_front_forgiving.py').write_text(s)
