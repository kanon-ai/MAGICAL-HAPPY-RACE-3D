from pathlib import Path
import re,json,hashlib,subprocess,os
R=Path(__file__).resolve().parents[1];W=R/'work/bonnet-wide-test';W.mkdir(exist_ok=True)
pal=[int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])];pal=list(zip(*[iter(pal)]*3))
def nearest(rgb):return min(range(256),key=lambda i:sum((pal[i][j]-rgb[j])**2 for j in range(3)))
ram=json.loads((R/'outputs/symbols.json').read_text())['_bgm_poll']+46
base=[nearest(x) for x in [(5,6,7),(21,2,3),(2,8,22),(26,18,3)]]
shine=[nearest(x) for x in [(10,11,12),(29,8,7),(5,14,28),(31,25,10)]]
code='''#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
static const uint8_t paints[4]={BASE};
static const uint8_t highlights[4]={SHINE};
void bonnet(void) {
 uint8_t p,h,c;
 if(U8(57921)!=1 || U8(60246))return;
 c=U8(STATE)&3;p=paints[c];h=highlights[c];
 /* Bonnet remains entirely above dashboard row168. */
 RECT(32,159,192,1,h);
 RECT(16,160,224,2,p);
 RECT(0,162,256,5,p);
 RECT(32,161,2,4,h);
 RECT(222,161,2,4,h);
 RECT(0,167,256,1,12);
}
'''.replace('BASE',','.join(map(str,base))).replace('SHINE',','.join(map(str,shine))).replace('STATE',str(ram))
(R/'src/bonnet_wide_test.c').write_text(code)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6410','--data-loc','0x3fd8','-Wl-b_HOME=0x6af0',str(R/'src/bonnet_wide_test.c'),'-o',str(W/'hood.ihx')],check=True,env=env)
m=(W/'hood.map').read_text();entry=int(re.search(r'([0-9A-F]{8})\s+_bonnet\s',m)[1],16)
for suffix in ('','-external-88h'):
 d=R/('outputs/camera-restored'+suffix);src=next(d.glob('*.rom'));old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((d/'manifest.json').read_text())['sha256'];rom=bytearray(old);allowed=set();hb=200*16384+8192
 def put(at,data,expected):
  assert old[at:at+len(data)]==expected,hex(at)
  rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 target=old[hb+0xb04:hb+0xb06];assert old[hb+0xb03]==0xc3
 put(hb+0xb04,bytes.fromhex('0064'),target)
 wrapper=b'\xcd'+entry.to_bytes(2,'little')+b'\xc3'+target
 put(hb+0x400,wrapper,bytes([255])*len(wrapper))
 for l in (W/'hood.ihx').read_text().splitlines():
  b=bytes.fromhex(l[1:]);assert sum(b)%256==0
  if b[3]==0:
   at=int.from_bytes(b[1:3],'big');data=b[4:-1];assert 0x6410<=at and at+len(data)<0x6b00
   put(hb+at-0x6000,data,bytes([255])*len(data))
 assert len(rom)==len(old)==4194304
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/bonnet-wide-test'+suffix);out.mkdir(exist_ok=True);(out/src.name).write_bytes(rom)
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),changed_bytes=sum(a!=b for a,b in zip(old,rom)),scope='Cockpit bonnet only; camera, chase view, physics, assets unchanged.',palette=base,highlights=shine),indent=2))
 print(out)
