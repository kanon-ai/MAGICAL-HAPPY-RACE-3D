"""Isolated title splash and transparent result lettering; gameplay bytes preserved."""
from pathlib import Path
import json,re,hashlib,subprocess,os
from PIL import Image,ImageDraw,ImageFont
from pack_atlas import encode
R=Path(__file__).resolve().parents[1];W=R/'work/title-art';A=R/'assets/title-art'
S=json.loads((R/'outputs/symbols.json').read_text())
pal=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
p=Image.new('P',(1,1));p.putpalette(pal)
font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',9)
patterns={
'A':'01110/10001/10001/11111/10001/10001/10001','B':'11110/10001/10001/11110/10001/10001/11110','C':'01111/10000/10000/10000/10000/10000/01111','D':'11110/10001/10001/10001/10001/10001/11110','E':'11111/10000/10000/11110/10000/10000/11111','F':'11111/10000/10000/11110/10000/10000/10000','G':'01111/10000/10000/10111/10001/10001/01111','H':'10001/10001/10001/11111/10001/10001/10001','I':'11111/00100/00100/00100/00100/00100/11111','J':'00111/00010/00010/00010/10010/10010/01100','K':'10001/10010/10100/11000/10100/10010/10001','L':'10000/10000/10000/10000/10000/10000/11111','M':'10001/11011/10101/10101/10001/10001/10001','N':'10001/11001/10101/10011/10001/10001/10001','O':'01110/10001/10001/10001/10001/10001/01110','P':'11110/10001/10001/11110/10000/10000/10000','Q':'01110/10001/10001/10001/10101/10010/01101','R':'11110/10001/10001/11110/10100/10010/10001','S':'01111/10000/10000/01110/00001/00001/11110','T':'11111/00100/00100/00100/00100/00100/00100','U':'10001/10001/10001/10001/10001/10001/01110','V':'10001/10001/10001/10001/10001/01010/00100','W':'10001/10001/10001/10101/10101/11011/10001','X':'10001/10001/01010/00100/01010/10001/10001','Y':'10001/10001/01010/00100/00100/00100/00100','Z':'11111/00001/00010/00100/01000/10000/11111',
'0':'01110/10001/10011/10101/11001/10001/01110','1':'00100/01100/00100/00100/00100/00100/01110','2':'01110/10001/00001/00010/00100/01000/11111','3':'11110/00001/00001/01110/00001/00001/11110','4':'00010/00110/01010/10010/11111/00010/00010','5':'11111/10000/10000/11110/00001/00001/11110','6':'01110/10000/10000/11110/10001/10001/01110','7':'11111/00001/00010/00100/01000/01000/01000','8':'01110/10001/10001/01110/10001/10001/01110','9':'01110/10001/10001/01111/00001/00001/01110',
'>':'00000/01000/00100/00010/00100/01000/00000','/':'00001/00001/00010/00100/01000/10000/10000',':':'00000/00100/00100/00000/00100/00100/00000',' ':'00000/00000/00000/00000/00000/00000/00000'}
glyphs=[]
for ch in range(32,96):
 rows=patterns.get(chr(ch),patterns[' ']).split('/')+['00000']
 glyphs.extend(sum(1<<(x+1) for x,v in enumerate(row) if v=='1') for row in rows)
assets={}
for name,size in [('title',(256,212)),('goal',(240,64)),('over',(224,42))]:
 im=Image.open(A/f'{name}-source.png').convert('RGBA')
 if name!='title':
  assert im.getextrema()[3][0]==0,'True alpha required'
  im=im.crop(im.getchannel('A').getbbox())
 im=im.resize(size,Image.Resampling.LANCZOS)
 q=im.convert('RGB').quantize(palette=p,dither=Image.Dither.NONE)
 data=bytearray(q.tobytes())
 # Index zero is transparent in the renderer, never use it for opaque pixels.
 for i,(v,a) in enumerate(zip(data,im.getchannel('A').tobytes())):
  if name!='title' and a<128:data[i]=0
  elif v==0:data[i]=12
 q=Image.frombytes('P',size,bytes(data));q.putpalette(pal);q.save(A/f'{name}-native.png',transparency=0 if name!='title' else None)
 assets[name]=(size,bytes(data))
slots=[(186,0x7000,0x8000),(188,0x7400,0x8000),(194,0x6b00,0x8000),(195,0x7c00,0x8000),(205,0x7300,0x8000),(248,0x6e00,0x8000),(249,0x7800,0x8000),(250,0x7400,0x8000),(254,0x6e00,0x8000),(255,0x6c00,0x8000),(214,0x7800,0x8000),(199,0x7800,0x8000),(211,0x7e00,0x8000),(215,0x7d00,0x8000)]
payload=[];tables={};slot=0;at=slots[0][1]
for name,((width,height),data) in assets.items():
 rows=[]
 for y in range(height):
  enc=encode(data[y*width:(y+1)*width])
  while at+len(enc)>slots[slot][2]:slot+=1;at=slots[slot][1]
  bank=slots[slot][0];rows.append((bank,at,len(enc)));payload.append((bank*16384+at-0x4000,bytes(enc)));at+=len(enc)
 tables[name]=rows
def phys(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
for suffix,port in [('',0x98),('-external-88h',0x88)]:
 O=R/('outputs/title-art'+suffix);O.mkdir(exist_ok=True)
 c='''#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define WAIT ((void(*)(void))51970)
#define POLL ((void(*)(void))0xd600)
#define INPUT ((uint8_t(*)(void))53447)
#define FLIP ((void(*)(uint8_t))53149)
#define TEXT ((void(*)(int16_t,int16_t,const char *))0x888d)
typedef struct {uint8_t bank;uint16_t address,length;} Row;
typedef void (*Reader)(uint8_t,uint16_t,uint8_t*,uint16_t) __sdcccall(0);
#define READ ((Reader)0xb174)
'''+f'__sfr __at({port}) vr;\n__sfr __at({port+1}) ctl;\n'
 for name,rows in tables.items():c+=f'static const Row {name}_rows[]={{'+','.join('{%d,%d,%d}'%r for r in rows)+'};\n'
 c+='static const uint8_t glyphs[]={'+','.join(map(str,glyphs))+'};\n'
 c+='''
static void label(uint8_t x,uint8_t y,const char *text){
 uint8_t c,row,col,m,above,below,v,bit,outline,run;uint16_t py;const uint8_t *g;
 WAIT();
 while((c=*text++)){
  if(c<32||c>95)c=32;g=glyphs+(uint16_t)(c-32)*8;
  for(row=0;row<10;++row){
   m=row>0&&row<9?g[row-1]:0;above=row>1?g[row-2]:0;below=row<8?g[row]:0;
   py=((uint16_t)U8(57953)<<8)+y+row;
   outline=m|(m<<1)|(m>>1)|above|below;bit=1;run=0;
   for(col=0;col<8;++col){v=(m&bit)?15:(outline&bit)?12:0;
    if(v){if(!run){ctl=py>>6;ctl=0x8e;ctl=x+col;ctl=0x40|(py&63);}vr=v;run=1;}else run=0;bit<<=1;
   }
  }x+=7;POLL();
 }
}
static void draw(const Row *rows,uint8_t height,uint16_t y,uint8_t x,uint8_t transparent){
 uint8_t *buf=(uint8_t*)58271;uint8_t token,value,n;uint16_t i,px;uint8_t h;
 WAIT();
 for(h=0;h<height;++h,++rows,++y){
  READ(rows->bank,rows->address,buf,rows->length);i=0;px=x;
  while(i<rows->length){
   token=buf[i++];n=(token&127)+1;
   if(token&128){value=buf[i++];if(!transparent||value){ctl=y>>6;ctl=0x8e;ctl=(uint8_t)px;ctl=0x40|(y&63);{uint8_t j=n;do{vr=value;}while(--j);}}px+=n;}
   else {while(n--){value=buf[i++];if(!transparent||value){ctl=y>>6;ctl=0x8e;ctl=(uint8_t)px;ctl=0x40|(y&63);vr=value;}++px;}}
  }
  POLL();
 }
}
void splash(void){
 uint8_t page=U8(57953);draw(title_rows,212,(uint16_t)page<<8,0,0);
 label(89,194,"PRESS SPACE");WAIT();FLIP(page);
 while(INPUT()&16)POLL();while(!(INPUT()&16))POLL();while(INPUT()&16)POLL();
}
void result(void){
 uint16_t y=(uint16_t)U8(57953)<<8;
 uint8_t color=U8(51961)&3,song=U8(0xdff0);
 if(U8(57921)==0){
  label(54,43,"MAGICAL HAPPY RACE 3D");
  label(54,66,"RADIO  1 / 2 / 3");
  label(54,81,song==0?"> BGM1   BGM2   BGM3":song==1?"  BGM1 > BGM2   BGM3":"  BGM1   BGM2 > BGM3");
  label(54,105,"COLOR  5 / 6 / 7 / 8");
  label(54,120,color==0?"> BLACK":color==1?"> RED":color==2?"> BLUE":"> YELLOW");
  label(82,145,"SPACE: START");return;
 }
 if(U8(60185))draw(over_rows,42,y+46,16,1);else draw(goal_rows,64,y+30,8,1);
 label(79,101,U8(60185)?"TIME EXPIRED":"DRIVE COMPLETE");
 label(68,117,"SPACE: DRIVE AGAIN");label(75,130,"ESC: MODE SELECT");
}
'''
 (O/'title_art.c').write_text(c)
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6200','--data-loc','0xdff5','-Wl-b_HOME=0x7ff0',str(O/'title_art.c'),'-o',str(O/'art.ihx')],env=env,check=True)
 mp=(O/'art.map').read_text();symbol=lambda n:int(re.search(r'([0-9A-F]{8})\s+_'+n+r'\s',mp)[1],16)
 source=next((R/('outputs/race-title'+suffix)).glob('*.rom'));old=source.read_bytes();rom=bytearray(old);allowed=set()
 def put(a,data,expect=None):
  if expect is not None:assert old[a:a+len(data)]==expect,(hex(a),old[a:a+len(data)].hex(),expect.hex())
  rom[a:a+len(data)]=data;allowed.update(range(a,a+len(data)))
 for a,data in payload:put(a,data,b'\xff'*len(data))
 for line in (O/'art.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');data=b[4:-1];assert 0x6200<=a and a+len(data)<0x8000;put(187*16384+a-0x4000,data,b'\xff'*len(data))
 original=old[phys(0xc3a7):phys(0xc3a7)+3];assert original[0]==0xcd
 asm=f'''org 0b174h
reader:
 push ix
 ld ix,0
 add ix,sp
 ld a,(ix+4)
 ld l,(ix+5)
 ld h,(ix+6)
 ld e,(ix+7)
 ld d,(ix+8)
 ld c,(ix+9)
 ld b,(ix+10)
 ld (06000h),a
 ldir
 ld a,187
 ld (06000h),a
 pop ix
 ret
input_hook:
 ld a,(0dff1h)
 or a
 jr nz,input_ready
 inc a
 ld (0dff1h),a
 push bc
 push de
 push hl
 push ix
 push iy
 ld a,187
 ld (06000h),a
 call {symbol('splash')}
 call 0c18ah
 ld a,252
 ld (06000h),a
 pop iy
 pop ix
 pop hl
 pop de
 pop bc
input_ready:
 jp 0de80h
panel_hook:
 ld a,(57921)
 or a
 jr z,result_panel
 cp 3
 jr z,result_panel
 cp 4
 jr z,result_panel
 db {','.join(map(str,original))}
 jp 0c3aah
result_panel:
 ld a,187
 ld (06000h),a
 call {symbol('result')}
 ld a,252
 ld (06000h),a
 ret
'''
 (O/'hooks.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'hooks.asm'),str(O/'hooks.bin'),str(O/'hooks.sym')],check=True)
 hook=(O/'hooks.bin').read_bytes();assert len(hook)<=140;put(phys(0xb174),hook,b'\xff'*len(hook))
 sym=(O/'hooks.sym').read_text();hs=lambda n:int(re.search(n+r'\s+EQU\s+0([0-9A-F]+)H',sym)[1],16)
 put(0xe9a7,b'\xcd'+hs('input_hook').to_bytes(2,'little'),bytes.fromhex('cd80de'))
 put(phys(0xc3a7),b'\xc3'+hs('panel_hook').to_bytes(2,'little'),original)
 put(phys(0xdff1),b'\0',b'\xff')
 # Remove only the legacy contact banner, leaving particles and penalties intact.
 pattern=bytes.fromhex('3a')+S['_notice_timer'].to_bytes(2,'little')+bytes.fromhex('b728')
 start=old.find(pattern,phys(0xc500),phys(0xc800));assert start>=0
 put(start+4,b'\x18',b'\x28')
 for text in (b'SCRAPE\0',b'IMPACT\0'):
  start=old.find(text,200*16384+8192,201*16384);assert start>=0;put(start,b'\0',text[:1])
 # Low-speed period 720 -> 1440 (~one octave lower); tone volumes +1.
 start=phys(0xd170);block=old[start:start+190]
 pos=block.index(bytes.fromhex('21d002'));put(start+pos,bytes.fromhex('21a005'),bytes.fromhex('21d002'))
 for pattern,replacement in [(bytes.fromhex('2e08c53e08'),bytes.fromhex('2e09c53e08')),(bytes.fromhex('2e05c53e09'),bytes.fromhex('2e06c53e09'))]:
  pos=block.index(pattern);put(start+pos,replacement,pattern)
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/source.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),art_bytes=sum(len(d) for _,d in payload),entry={n:symbol(n) for n in ['splash','result']},scope='Generated title splash; transparent result overlays. All non-UI game logic preserved.',verified=False),indent=2))
 print(O,'art bytes',sum(len(d) for _,d in payload))
