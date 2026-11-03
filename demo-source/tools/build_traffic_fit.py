"""Match passenger-car materials to their separate glass, body and wheel faces.
No face-count, camera, collision, AI or physics changes. Both near and far
render tables share the same revised UVs and wheel mounting coordinates.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import re,json,hashlib
R=Path(__file__).resolve().parents[1];A=R/'assets/traffic-fit';A.mkdir(exist_ok=True)
pal=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
oldtex=(R/'assets/modern-traffic/traffic-atlas.bin').read_bytes()
atlas=Image.frombytes('P',(256,44),oldtex);atlas.putpalette(pal);d=ImageDraw.Draw(atlas)
def nearest(rgb):return min(range(1,256),key=lambda i:sum((pal[i*3+j]-rgb[j])**2 for j in range(3)))
lamp=nearest((255,95,70))
# Reconstruct body-only door skins: tires live on independent polygons.
# Explicit pixel clusters avoid gray sheet background or duplicate half wheels.
for v,(base,bright,shade) in enumerate(((51,52,166),(63,55,72),(94,93,98))):
 x=v*64
 d.rectangle((x,0,x+63,19),fill=base)
 d.line((x,1,x+63,1),fill=bright)
 d.rectangle((x,14,x+63,18),fill=shade)
 d.line((x,19,x+63,19),fill=12)
 for door in (21,40):
  d.line((x+door,2,x+door,15),fill=shade)
  d.line((x+door+2,4,x+door+6,4),fill=12)
  d.line((x+door+2,3,x+door+6,3),fill=bright)
 # Wheel centres match model z=38/152 and y=35; black wheel wells only.
 for cx in (13,50):d.ellipse((x+cx-6,4,x+cx+6,24),fill=12)
 d.rectangle((x+1,2,x+3,4),fill=lamp)
 d.rectangle((x+60,2,x+62,4),fill=55)
 # Keep the supplied rear design, clean lamps/plate at native resolution.
 d.rectangle((x+26,33,x+37,35),fill=55)
 d.line((x+26,36,x+37,36),fill=12)
 if v==0:
  for lo,hi in ((3,18),(45,60)):
   d.rectangle((x+lo,22,x+hi,25),fill=48)
   d.line((x+lo+1,23,x+hi-1,23),fill=lamp)
 d.rectangle((x+3,38,x+60,39),fill=12)
# Neutral front grille, separate from each vehicle's painted bonnet.
d.rectangle((192,32,223,43),fill=12)
d.rectangle((193,33,200,36),fill=55);d.rectangle((215,33,222,36),fill=55)
for y in (35,38,41):d.line((202,y,213,y),fill=72)
# Remove gray reference-sheet corners from the wheel material.
wheel=atlas.crop((224,0,256,32));mask=Image.new('1',(32,32));ImageDraw.Draw(mask).ellipse((1,1,30,30),fill=1)
clean=Image.new('P',(32,32),12);clean.putpalette(pal);clean.paste(wheel,(0,0),mask);atlas.paste(clean,(224,0))
tex=atlas.tobytes();(A/'traffic-atlas.bin').write_bytes(tex);atlas.resize((1024,176),Image.Resampling.NEAREST).save(A/'traffic-atlas-preview.png')
before=(R/'assets/traffic-packets.bin').read_bytes();packet=bytearray(before)
for v in range(3):
 for near in (0,1):
  block=v*2048+near*1024;n=packet[block]
  for f in range(n):
   # Rasterized edge fallback is a visible palette entry, not a flag alone.
   if packet[block+11+f*11]>=128:packet[block+11+f*11]=242
  for f in range(0,n,2):
   ids=list(packet[block+1+f*11:block+5+f*11]);uv=None
   if ids==[19,20,26,25]:uv=[210,31,210,16,223,16,223,31]
   if ids==[13,14,20,19]:uv=[192,31,192,16,210,16,210,31]
   if uv:
    at=block+1+n*11+f*8;packet[at:at+8]=bytes(uv)
    pairs=[uv[j:j+2] for j in range(0,8,2)];packet[at+8:at+16]=bytes(sum(pairs[::-1],[]))
  # Painter order: far wheels must not overwrite the nearer rear fascia.
  # Insert each axle after its side skin but before the body sections in front.
  groups=[]
  for f in range(0,n,2):
   fp=bytes(packet[block+1+f*11:block+1+(f+2)*11])
   uv=bytes(packet[block+1+n*11+f*8:block+1+n*11+(f+2)*8])
   groups.append((fp,uv))
  rear=[g for g in groups if 36<=min(g[0][:4])<44]
  front=[g for g in groups if min(g[0][:4])>=44]
  order=[]
  for g in groups:
   if min(g[0][:4])>=36:continue
   order.append(g)
   if list(g[0][:4])==[18,19,25,24]:order.extend(front)
   if list(g[0][:4])==[6,7,13,12]:order.extend(rear)
  assert len(order)==len(groups)
  packet[block+1:block+1+n*11]=b''.join(g[0] for g in order)
  packet[block+1+n*11:block+1+n*19]=b''.join(g[1] for g in order)
 for chase in (0,1):
  at=6144+chase*468+v*156;scale=.75 if chase else 1
  # A small lower-body bevel; tires mount outside the side skin, not inside it.
  for vertex,value in ((0,-86),(1,-90),(2,-85),(3,85),(4,90),(5,86)):
   packet[at+vertex*3]=round(value*scale)&255
  for vertex in range(36,52):packet[at+vertex*3]=round(-97*scale)&255
(A/'traffic-packets.bin').write_bytes(packet)
def faces(b,v):
 block=v*2048+1024;n=b[block]
 return b''.join(b[block+1+f*11:block+5+f*11]+b[block+1+n*11+f*8:block+1+n*11+(f+1)*8]+b[block+11+f*11:block+12+f*11] for f in range(0,n,2))
for suffix in ('','-external-88h'):
 src=R/('outputs/pixel-coast'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);allowed=set()
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 def put(at,data):rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 at=195*16384+8192;assert old[at:at+len(before)]==before;put(at,packet)
 start=206*16384+8192;end=start+8192
 for v in range(3):
  for prior,new in ((faces(before,v),faces(packet,v)),(before[6144+v*156:6300+v*156],packet[6144+v*156:6300+v*156])):
   at=old.find(prior,start,end);assert at>=0 and old.find(prior,at+1,end)<0
   put(at,new)
 # Truck uses the same visible fallback convention; preserve its geometry/UVs.
 truck_at=251*16384+8192;truck_before=old[truck_at:truck_at+2360];truck=bytearray(truck_before)
 for block in (0,1024):
  for f in range(truck[block]):
   if truck[block+11+f*11]>=128:truck[block+11+f*11]=242
 prior=faces(truck_before,0);new=faces(truck,0)
 at=old.find(prior,start,end);assert at>=0 and old.find(prior,at+1,end)<0
 put(at,new);put(truck_at,truck)
 for y in range(44):
  offset=y*256;at=(12+offset//8192)*16384+8192+offset%8192
  assert old[at:at+256]==oldtex[offset:offset+256];put(at,tex[offset:offset+256])
 assert len(rom)==len(old)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 O=R/('outputs/pixel-coast-traffic-fit'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),scope='Stage1 art plus passenger car UV/materials and small rear-body/wheel-position corrections. Runtime code, topology, physics, player and truck unchanged.',native_verified=False),indent=2))
 print(O)
