"""Isolated native gate renderer on the verified instrument trial."""
from pathlib import Path
import subprocess,os,json,re,hashlib,sys
ARCH="--rock-arch" in sys.argv
SERIES="--arch-series" in sys.argv
LOD="--arch-lod" in sys.argv
assert not LOD or SERIES
assert not SERIES or ARCH
TRIAL="drive-structures-carfix2" if ARCH else "drive-gates-carfix2"
if SERIES:TRIAL="arch-series"
if LOD:TRIAL="arch-series-lod"
from structure_vram_layout import validate as validate_structure_vram
validate_structure_vram()
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-large-speed-carfix'+suffix);out=R/('outputs/six-route-'+TRIAL+suffix);out.mkdir(exist_ok=True)
 work=R/('work/'+TRIAL+suffix);work.mkdir(exist_ok=True)
 index=0x8d if suffix else 0x9d
 hdr=f'#define GEO_INDEX {index}\n#define GEO_DATA {index+2}\n'
 for macro,key,typ in [('MODE','mode','uint8_t'),('PIECE','route_piece','uint8_t'),('DISTANCE','distance','uint16_t'),('CAMERA','camera_mode','uint8_t'),('BOTTOM','view_bottom','uint8_t'),('PAGE','draw_page','uint8_t')]:hdr+=f'#define {macro} (*(volatile {typ} *){S["_"+key]})\n'
 hdr+=f'#define PROFILE ((uint8_t *){S["_profile"]})\n#define TRAFFIC_LUT ((uint8_t *){S["_traffic_scale_lut"]})\n'
 for macro,addr,typ,args in [('LERP',0x867c,'int16_t','int16_t,uint8_t,uint8_t'),('VIEW_X',S['_view_x'],'int16_t','int16_t,uint8_t'),('VIEW_Y',S['_view_y'],'int16_t','int16_t,uint8_t'),('VIEW_W',S['_view_width'],'uint8_t','uint8_t'),('CAMERA_SHIFT',S['_camera_shift'],'int16_t','uint8_t'),('TEX_WINDOW',S['_gfx_texture_window'],'void','uint16_t,uint16_t,uint16_t,uint16_t'),('WORD',S['_road_word'],'void','uint8_t,int16_t'),('POLL',S['_bgm_poll'],'void','void')]:hdr+=f'#define {macro} (({typ} (*)({args})){addr})\n'
 (work/'gate_addresses.h').write_text(hdr)
 env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6f5','-Wl-b_HOME=0x7800','-I',str(work),*(['-DROCK_ARCH'] if ARCH else []),*(['-DARCH_SERIES'] if SERIES else []),*(['-DARCH_LOD'] if LOD else []),str(R/'src/drive_gates.c'),'-o',str(work/'gates.ihx')],env=env,check=True)
 mem={}
 for line in (work/'gates.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   at=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):assert 0x6000<=at+i<0x8000;mem[at+i]=v
 entry=int(re.search(r'([0-9A-F]{8})\s+_draw_drive_gate\s',(work/'gates.map').read_text())[1],16)
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old);allowed=set()
 def patch(at,data):rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 bank=210*16384+8192;assert old[bank:bank+8192]==bytes([255])*8192
 for address,value in mem.items():patch(bank+address-0x6000,bytes([value]))
 assert old[off(0xca1d):off(0xca1d)+3]==bytes.fromhex('cdb3d3')
 assert old[off(0xa935):off(0xa935)+16]==bytes.fromhex('3ecf320060cd00603efc320060c351b3')
 stub=bytes.fromhex('dde5fde53ed2320060cd')+entry.to_bytes(2,'little')+bytes.fromhex('3efc320060fde1dde1c3b3d3')
 assert 0xa945+len(stub)<0xa9f7
 patch(off(0xa945),stub);patch(off(0xca1d),bytes.fromhex('cd45a9'))
 font=b''.join(old[k*16384+8192:(k+1)*16384] for k in range(4,12))
 # Separate compact banners from all resident car and UI textures.
 for n,label in enumerate(('CHECKPOINT','GOAL')):
  banner=Image.new('P',(64,8),3);d=ImageDraw.Draw(banner)
  x=(64-len(label)*6)//2
  for ch in label:
   i=ord(ch)-32;sx=(i&31)*6;sy=696+(i>>5)*8-512
   for yy in range(8):
    for xx in range(6):
     if font[(sy+yy)*256+sx+xx]:banner.putpixel((x+xx,yy),15)
   x+=6
  sx,sy=(64,650) if n else (0,650)
  for y in range(8):
   offset=(sy+y-512)*256+sx;at=(4+offset//8192)*16384+8192+offset%8192
   patch(at,banner.tobytes()[y*64:(y+1)*64])
 # Regression guard: all 44 resident traffic-atlas rows must stay original.
 baseline=next((R/('outputs/six-route-road-uv-preserved'+suffix)).glob('*.rom')).read_bytes()
 for row in range(44):
  offset=row*256;at=(12+offset//8192)*16384+8192+offset%8192
  assert rom[at:at+256]==baseline[at:at+256],('traffic texture overwritten',row)
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (out/path.name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),entry=entry,code_bytes=len(mem),scope='Checkpoint/goal gates and optional canyon rock arch. Native projection/culling and timing validation pending.',rock_arch=ARCH,adopted=False),indent=2));print(out.name,len(mem),hex(entry),flush=True)
