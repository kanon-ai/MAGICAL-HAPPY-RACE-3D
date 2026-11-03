from pathlib import Path
import math,subprocess,os,json,hashlib,sys
from PIL import Image
R=Path(__file__).resolve().parents[1];W=R/'work/polygon-trees';W.mkdir(exist_ok=True)
def model(palm):
 v=[(-3,0,-3),(3,0,-3),(3,0,3),(-3,0,3), (6,100 if palm else 62,-2),(10,100 if palm else 62,-2),(10,100 if palm else 62,2),(6,100 if palm else 62,2)]
 faces=[([0,1,5,4],75),([1,2,6,5],106),([2,3,7,6],117),([3,0,4,7],75)]
 if palm:
  for j in (3,4,5,2,6,1,7,0):
   angle=j*math.pi/4;dx=math.cos(angle);dz=math.sin(angle);base=len(v)
   v.extend([(8,104,0),(round(8+dx*24-dz*5),116,round(dz*24+dx*5)),(round(8+dx*49),81+(j%3)*3,round(dz*49)),(round(8+dx*24+dz*5),116,round(dz*24-dx*5))])
   faces.append(([base,base+1,base+2,base+3],242))
 else:
  for j in range(12):
   angle=j*math.pi/6;v.append((round(55*math.cos(angle)),round(86+39*math.sin(angle)),0))
  v.extend([(0,87,24),(0,87,-24)])
  for center in (20,21):
   for j in range(12):faces.append(([center,8+j,8+(j+1)%12,center],242))
 headers=[];uvs=[]
 for ids,c in faces:
  uv=[0,0,15,0,15,15,0,15] if palm or c<128 else [8,8,round((v[ids[1]][0]+55)*15/110),round((125-v[ids[1]][1])*15/78),round((v[ids[2]][0]+55)*15/110),round((125-v[ids[2]][1])*15/78),8,8]
  for rev in (False,True):
   headers.extend([i+192 for i in (ids[::-1] if rev else ids)]+[0]*6+[c]);pairs=[uv[k:k+2] for k in range(0,8,2)];uvs.extend(sum(pairs[::-1] if rev else pairs,[]))
 return bytes([len(v),len(faces)*2])+bytes(c&255 for p in v for c in p)+bytes(headers+uvs)
models={'round':model(False),'palm':model(True)}
assert models['round'][1]==56 and models['palm'][1]==24
(W/'tree_models.h').write_text('\n'.join('static const uint8_t '+k+'_model[]={'+','.join(map(str,b))+'};' for k,b in models.items()))
# Calm native leaf clusters; existing RGB555 palette, no transparent-edge noise.
atlas=bytearray((R/'assets/pixel-coast/coast-atlas.bin').read_bytes())
for y in range(16):
 for x in range(16):
  c=45 if x+y<17 else 43
  if (x//4+y//3)%5==0:c=44
  if abs(x-7)<=0 and y>3:c=47
  atlas[(224+y)*256+80+x]=c
sys.path.insert(0,str(R.parents[3]/'public-road-cockpit/tools'))
from graphics_codec import compress
packed=bytearray(40960)
for page,start in enumerate((0,3*8192+632)):
 pos=start
 for i in range(32):
  chunk=bytes([1])+compress(bytes(atlas[page*32768+i*1024:page*32768+(i+1)*1024]))
  if pos//8192!=(pos+len(chunk)-1)//8192:pos=(pos//8192+1)*8192
  assert pos+len(chunk)<=(3*8192+632 if page==0 else 40960)
  packed[pos:pos+len(chunk)]=chunk;pos+=len(chunk)
(W/'atlas.bin').write_bytes(atlas)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
S=json.loads((R/'outputs/symbols.json').read_text());entry=S['_gfx_scaled']
def resident(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 O=R/('outputs/polygon-trees'+suffix);O.mkdir(exist_ok=True)
 cmd=[str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6900','--data-loc','0xf6f6','-I',str(W),'-I',str(R/'src')]
 if suffix:cmd+=['-DEXTERNAL_V9968']
 subprocess.run(cmd+[str(R/'src/polygon_trees.c'),'-o',str(O/'trees.ihx')],env=env,check=True)
 mem={}
 for line in (O/'trees.ihx').read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big')
   for i,v in enumerate(b[4:-1]):assert 0x6900<=a+i<0x8000;mem[a+i]=v
 import re
 mul=int(re.search(r'([0-9A-F]{8})\s+__mulint\s',(O/'trees.map').read_text())[1],16)
 for i,v in enumerate(bytes.fromhex('424bedc3ebc9')):mem[mul+i]=v
 fn=int(re.search(r'([0-9A-F]{8})\s+_polygon_tree\s',(O/'trees.map').read_text())[1],16)
 src=R/('outputs/coast-scale'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 stolen=old[resident(entry):resident(entry)+22];assert stolen==bytes.fromhex('dde5dd210000dd3921efff39f9dd77fbdd73f9dd72fa')
 # Shared seven-byte RAM return gateway occupies only the prior hook's NOPs.
 at=214*16384+8192+5342;assert old[at:at+17]==bytes.fromhex('3ed3320060cd007c000000000000000000')
 rom[at+8:at+17]=bytes.fromhex('18073ecf320060c900');back=0x38e8
 gate=f'''org 06800h
 pop af
 push af
 push de
 ld a,(57935)
 cp 8
 jr nc,fallback
 ld a,d
 cp 3
 jr nz,fallback
 ld a,e
 cp 128
 jr nz,fallback
 ld a,(60649)
 or a
 jr z,eligible
 ld hl,(60650)
 ld de,225
 or a
 sbc hl,de
 jr nc,fallback
eligible:
 pop de
 pop af
 ld hl,2
 add hl,sp
 call {fn}
 pop hl
 ld de,14
 ex de,hl
 add hl,sp
 ld sp,hl
 push de
 jp {back}
fallback:
 pop de
 pop af
 db {','.join(str(x) for x in stolen)}
 ld hl,{entry+22}
 push hl
 jp {back}
'''
 (O/'gate.asm').write_text(gate);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'gate.asm'),str(O/'gate.bin')],check=True)
 code=(O/'gate.bin').read_bytes();assert len(code)<256
 # Wait in resident code before mapping ROM, preserving both ABI inputs.
 stub=bytes.fromhex('f5d5cd')+S['_gfx_wait'].to_bytes(2,'little')+bytes.fromhex('d13ebc320060c30068')
 rom[resident(entry):resident(entry)+22]=stub+bytes(22-len(stub))
 for a,v in mem.items():assert old[188*16384+8192+a-0x6000]==255;rom[188*16384+8192+a-0x6000]=v
 at=188*16384+8192+2048;assert old[at:at+len(code)]==bytes([255])*len(code);rom[at:at+len(code)]=code
 for i in range(5):at=(16+i)*16384+8192;rom[at:at+8192]=packed[i*8192:(i+1)*8192]
 assert len(rom)==4194304
 (O/p.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),renderer_bytes=len(mem)+len(code),scope='Stage1 polygon palms/canopies only; sprite fallback during scene atlas replacement and on all other stages.',native_verified=False),indent=2))
 print(O,len(mem),hex(fn))
