"""HUD-only overlay; countdown state/update code remains byte-identical."""
from pathlib import Path
import json,os,subprocess,re,hashlib
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];W=R/'work/center-timer';W.mkdir(exist_ok=True)
S=json.loads((R/'outputs/symbols.json').read_text())
patterns=['01110/11011/11011/11011/11011/11011/01110','00110/01110/00110/00110/00110/00110/01111','01110/11011/00011/00110/01100/11000/11111','11110/00011/00011/01110/00011/00011/11110','00011/00111/01111/11011/11111/00011/00011','11111/11000/11000/11110/00011/00011/11110','01110/11000/11000/11110/11011/11011/01110','11111/00011/00110/00110/01100/01100/01100','01110/11011/11011/01110/11011/11011/01110','01110/11011/11011/01111/00011/00011/01110']
data=[]
for pat in patterns:
 mask=Image.new('L',(12,16));d=ImageDraw.Draw(mask)
 for y,row in enumerate(pat.split('/')):
  for x,v in enumerate(row):
   if v=='1':d.rectangle((1+x*2,1+y*2,2+x*2,2+y*2),fill=255)
 outline=mask.filter(ImageFilter.MaxFilter(3));data.extend(15 if a else 12 if b else 0 for a,b in zip(mask.getdata(),outline.getdata()))
data.extend([0]*192)
for suffix,sha in [('', 'b899757c95247ae212b3ccfbf916b370c03f0243b374963f993e702d43684a8d'),('-external-88h','7774a5d93e946b09d359f6283c5e901cb5505bd2700dc0b0dc84762cd6bd33d9')]:
 O=R/('outputs/center-timer'+suffix);O.mkdir(exist_ok=True)
 port=0x88 if suffix else 0x98
 source=f'''#include <stdint.h>
#define MODE (*(volatile uint8_t *){S['_mode']})
#define PAGE (*(volatile uint8_t *){S['_draw_page']})
#define SECONDS (*(volatile uint16_t *){S['_remaining_seconds']})
#define CACHED (*(volatile uint16_t *)0xf6ea)
#define NOTICE (*(volatile uint16_t *)0xf6e8)
#define WAIT ((void (*)(void)){S['_gfx_wait']})
#define POLL ((void (*)(void)){S['_bgm_poll']})
#define BLIT ((void (*)(uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,uint8_t)){S['_gfx_blit']})
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
#define TEXT ((void (*)(int16_t,int16_t,const char *))0x888d)
__sfr __at({port}) vr;
__sfr __at({port+1}) ctl;
static const uint8_t digits[2112]={{{','.join(map(str,data))}}};
void centered_timer(void) {{
 uint16_t value=SECONDS,a,b,c,y;
 uint8_t row,x;
 if(MODE!=1&&MODE!=2)return;
 if(value>999)value=999;
 if(CACHED!=SECONDS) {{
  a=value>=100?value/100:10;b=value>=10?(value/10)%10:10;c=value%10;
  a*=192;b*=192;c*=192;
  WAIT();
  /* x88..123,y658..673: between mirror and speed; no scenery overlap. */
  for(row=0;row<16;++row) {{
   y=658+row;ctl=y>>6;ctl=0x8e;ctl=88;ctl=0x40|(y&63);
   for(x=0;x<12;++x)vr=digits[a+x];
   for(x=0;x<12;++x)vr=digits[b+x];
   for(x=0;x<12;++x)vr=digits[c+x];
   a+=12;b+=12;c+=12;POLL();
  }}
  CACHED=SECONDS;
 }}
 BLIT(88,658,value>=100?110:value>=10?104:98,((uint16_t)PAGE<<8)+6,36,16,1);
 if(NOTICE) {{RECT(4,22,122,12,12);TEXT(10,24,"CHECKPOINT +140");}}
}}
'''
 (O/'centered_timer.c').write_text(source)
 sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x7200','--data-loc','0xf6f5','-Wl-b_HOME=0x7ff0',str(O/'centered_timer.c'),'-o',str(O/'timer.ihx')],env=env,check=True)
 src=next((R/('outputs/modern-player'+suffix)).glob('*.rom'));old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==sha
 rom=bytearray(old);allowed=set();base=200*16384+8192
 for line in (O/'timer.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):
    assert 0x7200<=a+i<0x8000
    at=base+a+i-0x6000;assert old[at]==255;rom[at]=v;allowed.add(at)
 entry=int(re.search(r'([0-9A-F]{8})\s+_centered_timer\s',(O/'timer.map').read_text())[1],16)
 at=base+0x2cf
 rom[at:at+3]=b'\xc3'+entry.to_bytes(2,'little');allowed.update(range(at,at+3))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/src.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=sha,sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),scope='Timer display only; countdown calculation/checkpoint logic unchanged',glyph_size=[12,16],transparent_background=True,screen_center=128,cache=[88,658,36,16],native_verified=False),indent=2))
 print(O,entry,len(allowed))
