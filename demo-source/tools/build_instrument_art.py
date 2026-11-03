"""Code-native 256-colour instrument and 6x8 typography art, no game-rule edits."""
from pathlib import Path
import re,json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
palette=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
# Hand-hinted 5x7 forms; the sixth column and eighth row remain spacing.
patterns={
'0':'01110/11011/11011/11011/11011/11011/01110',
'1':'00110/01110/00110/00110/00110/00110/01111',
'2':'01110/11011/00011/00110/01100/11000/11111',
'3':'11110/00011/00011/01110/00011/00011/11110',
'4':'00011/00111/01111/11011/11111/00011/00011',
'5':'11111/11000/11000/11110/00011/00011/11110',
'6':'01110/11000/11000/11110/11011/11011/01110',
'7':'11111/00011/00110/00110/01100/01100/01100',
'8':'01110/11011/11011/01110/11011/11011/01110',
'9':'01110/11011/11011/01111/00011/00011/01110',
'A':'01110/11011/11011/11111/11011/11011/11011',
'B':'11110/11011/11011/11110/11011/11011/11110',
'C':'01111/11000/11000/11000/11000/11000/01111',
'D':'11110/11011/11011/11011/11011/11011/11110',
'E':'11111/11000/11000/11110/11000/11000/11111',
'F':'11111/11000/11000/11110/11000/11000/11000',
'G':'01111/11000/11000/11011/11011/11011/01111',
'H':'11011/11011/11011/11111/11011/11011/11011',
'I':'01110/00100/00100/00100/00100/00100/01110',
'J':'00111/00011/00011/00011/00011/11011/01110',
'K':'11011/11011/11110/11100/11110/11011/11011',
'L':'11000/11000/11000/11000/11000/11000/11111',
'M':'10001/11011/11111/10101/10001/10001/10001',
'N':'10011/11011/11011/11111/11111/11011/11001',
'O':'01110/11011/11011/11011/11011/11011/01110',
'P':'11110/11011/11011/11110/11000/11000/11000',
'Q':'01110/11011/11011/11011/11111/01110/00011',
'R':'11110/11011/11011/11110/11100/11011/11011',
'S':'01111/11000/11000/01110/00011/00011/11110',
'T':'11111/00100/00100/00100/00100/00100/00100',
'U':'11011/11011/11011/11011/11011/11011/01110',
'V':'11011/11011/11011/11011/11011/01110/00100',
'W':'10001/10001/10001/10101/11111/11011/10001',
'X':'11011/11011/01110/00100/01110/11011/11011',
'Y':'11011/11011/11011/01110/00100/00100/00100',
'Z':'11111/00011/00110/00100/01100/11000/11111',
}
def label(im,x,y,text,color):
 for c in text:
  if c in patterns:
   for yy,row in enumerate(patterns[c].split('/')):
    for xx,p in enumerate(row):
     if p=='1':im.putpixel((x+xx,y+yy),color)
  x+=6
dash=Image.new('P',(256,44),12);dash.putpalette(palette);d=ImageDraw.Draw(dash)
# Low, continuous top lip, matte panels and a restrained cyan accent.
for y,color in enumerate([14,7,3,1,12]):d.line((0,y,255,y),fill=color)
d.polygon([(4,10),(15,6),(92,6),(101,14),(101,39),(4,39)],fill=7)
d.polygon([(6,11),(16,8),(91,8),(98,15),(98,37),(6,37)],fill=12)
d.polygon([(163,14),(171,6),(249,6),(253,10),(253,39),(163,39)],fill=7)
d.polygon([(166,15),(172,8),(247,8),(250,11),(250,37),(166,37)],fill=12)
d.line((18,7,84,7),fill=32);d.line((177,10,240,10),fill=32)
label(dash,33,9,'SPEED',14)
label(dash,39,29,'KMH',14)
# Existing live speed at (42,18) and distance at (176,26) stay clear.
d.rectangle((40,18,62,25),fill=12)
d.rectangle((174,26,195,33),fill=12)
label(dash,201,26,'M',14)
label(dash,205,18,'X100',14)
for y in (17,21,25,29):d.line((110,y,148,y),fill=7);d.line((110,y+1,148,y+1),fill=0)
label(dash,119,7,'MHR',14)
d.line((107,37,151,37),fill=3)
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-road-uv-preserved'+suffix);out=R/('outputs/six-route-instrument-art-carfix'+suffix);out.mkdir(exist_ok=True)
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old);allowed=set()
 def put(at,value):rom[at]=value;allowed.add(at)
 def vram_at(x,y):
  offset=(y-512)*256+x
  return (4+offset//8192)*16384+8192+offset%8192
 for c,rows in patterns.items():
  n=ord(c)-32;x=(n&31)*6;y=696+(n>>5)*8
  for yy in range(8):
   for xx in range(6):put(vram_at(x+xx,y+yy),15 if yy<7 and xx<5 and rows.split('/')[yy][xx]=='1' else 0)
 for copy in (1,):
  for y in range(44):
   for x in range(256):
    offset=(copy*44+y)*256+x;at=(12+offset//8192)*16384+8192+offset%8192
    put(at,dash.getpixel((x,y)))
 tile=Image.new('P',(30,8),0);label(tile,0,0,'ROAD',14)
 for y in range(8):
  for x in range(30):put(vram_at(192+x,704+y),tile.getpixel((x,y)))
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom);dash.save(out/'dashboard.png')
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),scope='Static instrument art and uppercase/digit 6x8 glyphs only. No code, counters, timers or simulation changes.',adopted=False),indent=2))
 print(out.name,flush=True)
