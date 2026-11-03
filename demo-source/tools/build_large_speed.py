"""Larger cockpit speed digits using three opaque, cached-state VRAM blits."""
from pathlib import Path
import json,os,subprocess,re,hashlib
from structure_vram_layout import validate as validate_structure_vram
validate_structure_vram()
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
W=R/'work/large-speed';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
source=f'''#include <stdint.h>
#define SPEED (*(volatile uint16_t *){S['_speed']})
#define PAGE (*(volatile uint8_t *){S['_draw_page']})
#define BLIT ((void (*)(uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,uint8_t)){S['_gfx_blit']})
static void digit(uint8_t d,uint16_t x,uint16_t y) {{
 uint16_t sx=d<6?88+d*12:192+(d-6)*12;
 BLIT(sx,d<6?680:738,x,y,12,16,0);
}}
void draw_large_speed(void) {{
 uint16_t value=(SPEED*15)>>3, y=((uint16_t)PAGE<<8)+184;
 uint8_t hundreds=value/100, tens=(value%100)/10, units=value%10;
 digit(hundreds,32,y);
 digit(tens,44,y);
 digit(units,56,y);
}}
'''
(W/'large_speed.c').write_text(source)
env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f5','-Wl-b_HOME=0x7000',str(W/'large_speed.c'),'-o',str(W/'large_speed.ihx')],env=env,check=True)
mem={}
for line in (W/'large_speed.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  at=int.from_bytes(b[1:3],'big')
  for i,v in enumerate(b[4:-1]):assert 0x6000<=at+i<0x8000;mem[at+i]=v
maptext=(W/'large_speed.map').read_text()
entry=int(re.search(r'([0-9A-F]{8})\s+_draw_large_speed\s',maptext)[1],16)
atlas=Image.new('P',(120,16),12)
# Beveled seven-segment forms at 10x14, with spacing inside each 12x16 cell.
segments=[[(2,1),(8,1),(9,2),(8,3),(2,3),(1,2)],[(8,2),(10,3),(10,6),(9,7),(8,6)],[(9,8),(10,9),(10,12),(8,14),(8,9)],[(2,12),(8,12),(9,13),(8,14),(2,14),(1,13)],[(1,8),(3,9),(3,12),(1,14),(1,9)],[(1,2),(3,3),(3,6),(2,7),(1,6)],[(3,6),(8,6),(9,7),(8,8),(3,8),(2,7)]]
digit_segments=('abcdef','bc','abdeg','abcdg','bcfg','acdfg','acdefg','abc','abcdefg','abcdfg')
d=ImageDraw.Draw(atlas)
for n,letters in enumerate(digit_segments):
 for c in letters:d.polygon([(x+n*12,y) for x,y in segments[ord(c)-97]],fill=15)
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-instrument-art-carfix'+suffix);out=R/('outputs/six-route-large-speed-carfix'+suffix);out.mkdir(exist_ok=True)
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old);allowed=set()
 def patch(at,data):rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 bank=209*16384+8192;assert old[bank:bank+8192]==bytes([255])*8192
 for address,value in mem.items():patch(bank+address-0x6000,bytes([value]))
 start,end=0xc64a,0xc681
 assert old[off(start):off(start)+5]==bytes.fromhex('c5d5cd1a86')
 # Preserve both live callers' values (remaining in BC, shown_speed in DE).
 code=bytes.fromhex('c5d5fde5')+bytes.fromhex('3ed1320060cd')+entry.to_bytes(2,'little')+bytes.fromhex('3efc320060fde1d1c1c381c6')
 assert len(code)<=end-start
 patch(off(start),code+bytes(end-start-len(code)))
 dash=Image.open(src/'dashboard.png').copy();draw=ImageDraw.Draw(dash)
 draw.rectangle((30,16,93,35),fill=12)
 # Move the existing font-shaped KMH to the right of the large readout.
 original=Image.open(src/'dashboard.png');dash.paste(original.crop((39,29,57,36)),(72,24))
 for y in range(44):
  offset=(44+y)*256;at=(12+offset//8192)*16384+8192+offset%8192
  patch(at,dash.tobytes()[y*256:(y+1)*256])
 # VRAM212..255 is the traffic-car atlas, never dashboard scratch.
 for digit in range(10):
  sx=88+digit*12 if digit<6 else 192+(digit-6)*12
  sy=680 if digit<6 else 738
  for y in range(16):
   offset=(sy+y-512)*256+sx;at=(4+offset//8192)*16384+8192+offset%8192
   patch(at,atlas.tobytes()[y*120+digit*12:y*120+digit*12+12])
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (out/path.name).write_bytes(rom);dash.save(out/'dashboard.png');atlas.putpalette(dash.getpalette());atlas.save(out/'digits.png')
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_entry=entry,helper_bytes=len(mem),digit_source=[[88,680,72,16],[192,738,48,16]],destination=[32,184,36,16],scope='Cockpit speed drawing only, original per-page change cache retained. Font and dash from separate instrument-art trial.',adopted=False),indent=2))
 print(out.name,len(mem),flush=True)
