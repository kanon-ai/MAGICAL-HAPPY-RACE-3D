"""Isolated player-only assets. Reference-sheet crops -> existing 256-colour palette.
Preserves vertex count, face topology, yaw poses, wheel contact and camera.
"""
from pathlib import Path
import json,struct,math,re
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'assets/modern-player'
im=Image.open(O/'orthographic-master.png').convert('RGB')
pal=np.array([round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])],dtype=np.int32).reshape(256,3)
# These are UV surface crops, not whole-car sprites: glass/wheels must not be
# baked into the fascia, and no reference background can reach a body face.
boxes={'rear':(93,204,631,351),'bumper':(93,351,631,430),
       'side':(217,778,484,895),'glass':(1013,907,1151,967),
       'rim':(91,817,227,950),'deck':(1009,986,1156,1013),
       'highlight':(1001,581,1024,674),'paint':(1060,580,1100,675)}
sizes={'rear':(48,16),'bumper':(48,16),'side':(48,16),'glass':(48,16),
       'rim':(16,16),'deck':(48,16),'highlight':(8,16),'paint':(8,16)}
tiles={k:np.array(im.crop(box).resize(sizes[k],Image.Resampling.LANCZOS)) for k,box in boxes.items()}
positions={'rear':(0,0),'bumper':(0,16),'side':(0,32),'glass':(0,48),'rim':(16,64),'highlight':(32,64),'paint':(40,64),'deck':(0,80)}
for color in ('black','red','blue'):
 atlas=Image.new('P',(48,96),12);atlas.putpalette(pal.astype('uint8').ravel().tolist())
 for name,source in tiles.items():
  a=source.astype(np.float32);r,g,b=a[:,:,0].copy(),a[:,:,1].copy(),a[:,:,2].copy()
  mask=(r>g*1.35)&(r>b*1.35)&(r>40)
  # Keep rear lamps red for every body colour, including their bright cores.
  if name=='rear':
   mask[1:5,4:15]=False;mask[1:5,33:44]=False
  if name=='bumper':
   mask[:2,6:14]=False;mask[:2,34:42]=False
  if color=='black':
   v=r*.32+g*.18; a[mask]=np.stack((v*.91,v*.96,v),axis=2)[mask]
  elif color=='blue':a[mask]=np.stack((r*.14+g*.3,r*.30+g*.25,r*.91),axis=2)[mask]
  # Nearest palette, no error diffusion: stable clean pixel clusters in motion.
  diff=a.reshape(-1,1,3)-pal[None,:,:]
  idx=(diff[:,:,0]**2*.9+diff[:,:,1]**2*1.2+diff[:,:,2]**2).argmin(axis=1).astype('uint8')
  tile=Image.frombytes('P',sizes[name],idx.tobytes());tile.putpalette(atlas.getpalette());atlas.paste(tile,positions[name])
 atlas.save(O/f'{color}-materials.png');(O/f'{color}-materials.bin').write_bytes(atlas.tobytes())
board=Image.new('RGB',(48*3,96))
for i,c in enumerate(('black','red','blue')):board.paste(Image.open(O/f'{c}-materials.png').convert('RGB'),(48*i,0))
board.resize((576,384),Image.Resampling.NEAREST).save(O/'materials-preview.png')
# Rebuild the five poses from a subtly revised coupe shell. Track and wheelbase
# remain exact. Do not change the camera, projected scale or driving physics.
old=(R/'assets/player-model.bin').read_bytes();base=[]
for i in range(92):
 x=int.from_bytes(old[i*3:i*3+1],'little',signed=True)*4;y=old[i*3+1]*4;z=old[i*3+2]*10
 if i<60:
  sec,j=divmod(i,10)
  # Fuller rear shoulders, lower roof crown, shorter visual deck.
  if j in (3,6) and sec==0:y=328
  if j in (4,5) and sec==0:y=328
  if sec in (2,3) and j in (4,5):y-=32
  if sec in (2,3) and j in (3,6):y-=12
 base.append((x,y,z))
poses=[]
for angle in (0,-3,-6,3,6):
 t=math.radians(angle);poses.append([(round((x*math.cos(t)+(z-950)*math.sin(t))/4)*4,y,round((950-x*math.sin(t)+(z-950)*math.cos(t))/10)*10) for x,y,z in base])
model=bytes(v for p in poses for x,y,z in p for v in ((x//4)&255,y//4,z//10));(O/'player-model.bin').write_bytes(model)
cache=bytearray((R/'assets/player-projection.bin').read_bytes())
for p,pose in enumerate(poses):
 for l,lift in enumerate((-12,-8,-6,-4,0,4,6,8,12)):
  xs=[];ys=[]
  for i,(x,y,z) in enumerate(pose):
   q=491520//(1450+z);xs.append(128-math.trunc(x*q/4096));ys.append(154-math.trunc((y-500+(lift if i<60 else 0))*q/4096))
  block=struct.pack('<92h',*xs)+struct.pack('<92h',*ys)+b''.join(struct.pack('<hhh',x,-y,1) for x,y in zip(xs,ys))
  slot=p*9+l;off=slot//8*8192+slot%8*920;cache[off:off+920]=block
  oldcache=(R/'assets/player-projection.bin').read_bytes()
  for i in range(60,92):assert cache[off+i*2:off+i*2+2]==oldcache[off+i*2:off+i*2+2] and cache[off+184+i*2:off+186+i*2]==oldcache[off+184+i*2:off+186+i*2]
(O/'player-projection.bin').write_bytes(cache)
# Retain the proven faces, adding only faces needed to close new silhouette
# pixels after the shell adjustment. Preserve the original depth order/UVs.
source_mesh=Path('C:/MSX/public-road-cockpit/assets/player-mesh.json')
mesh=json.loads(source_mesh.read_text());full=[]
for f in mesh['faces']:
 for rev in (False,True):
  ids=f['indices'][::-1] if rev else f['indices'];uv=[f['uv'][i:i+2] for i in range(0,8,2)]
  if rev:uv.reverse()
  full.append((ids,bytes(ids+[85]+[0]*6+[242]),bytes(v for pair in uv for v in pair)))
oldpacket=(R/'assets/player-packet.bin').read_bytes();keep=set()
for i in range(oldpacket[0]):
 header=oldpacket[1+i*12:13+i*12];uv=oldpacket[1+oldpacket[0]*12+i*8:1+oldpacket[0]*12+(i+1)*8]
 matches=[j for j,(_,h,u) in enumerate(full) if h==header and u==uv];assert len(matches)==1;keep.add(matches[0])
uncovered=set();covers=[set() for _ in full]
for slot in range(45):
 off=slot//8*8192+slot%8*920;xs=struct.unpack_from('<92h',cache,off);ys=struct.unpack_from('<92h',cache,off+184)
 masks=[]
 for ids,_,_ in full:
  mask=Image.new('1',(256,212));ImageDraw.Draw(mask).polygon([(xs[i],ys[i]) for i in ids],fill=1);masks.append(np.array(mask))
 missing=np.logical_or.reduce(masks)&~np.logical_or.reduce([masks[i] for i in keep])
 for y,x in zip(*np.where(missing)):
  key=(slot,int(y)*256+int(x));uncovered.add(key)
  for i,m in enumerate(masks):
   if m[y,x]:covers[i].add(key)
while uncovered:
 best=max(range(len(full)),key=lambda i:len(covers[i]&uncovered));assert covers[best]&uncovered
 keep.update((best&~1,best|1));uncovered-=covers[best]
headers=b''.join(full[i][1] for i in sorted(keep));uvs=b''.join(full[i][2] for i in sorted(keep))
packet=bytes([len(keep)])+headers+uvs;assert len(packet)<1024
(O/'player-packet.bin').write_bytes(packet.ljust(4096,b'\0'))
(O/'asset-report.json').write_text(json.dumps(dict(scope='Player shell and surface materials only',camera_unchanged=True,wheel_contacts_unchanged=True,vertices=92,faces=len(keep),colors=['black','red','blue'],image_generation='Built-in image_gen, supplied unbranded coupe references',palette_unchanged=True),indent=2))
print('Prepared player assets; wheel projections identical in all45 states; faces',len(keep))
