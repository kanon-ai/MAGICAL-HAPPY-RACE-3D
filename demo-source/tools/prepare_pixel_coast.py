"""Stage1 artwork only; preserves ocean, player and all other scene atlases."""
from pathlib import Path
from PIL import Image
import numpy as np,re,json
R=Path(__file__).resolve().parents[1];A=R/'assets/pixel-coast'
pal=np.array([round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])],dtype=np.int32).reshape(256,3)
base=(A/'baseline-atlas.bin').read_bytes();atlas=Image.frombytes('P',(256,256),base);atlas.putpalette(pal.astype('uint8').ravel().tolist())
def indexed(image,size,transparent=False):
 if transparent:
  image=image.convert('RGBA');alpha=np.array(image.getchannel('A'));ys,xs=np.where(alpha>=180);assert len(xs)
  image=image.crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
 image=image.resize(size,Image.Resampling.LANCZOS)
 a=np.array(image.convert('RGB').quantize(colors=40,method=Image.Quantize.MEDIANCUT).convert('RGB')).astype(np.int32)
 dist=a.reshape(-1,1,3)-pal[None,1:,:]
 pixels=((dist[:,:,0]**2+dist[:,:,1]**2*1.2+dist[:,:,2]**2).argmin(axis=1)+1).astype('uint8')
 if transparent:pixels[np.array(image.getchannel('A')).ravel()<128]=0
 out=Image.frombytes('P',size,pixels.tobytes());out.putpalette(atlas.getpalette());return out
source=Image.open(A/'facades-master.png');w,h=source.size
tiles=[indexed(source.crop((x*w//3+3,y*h//2+3,(x+1)*w//3-3,(y+1)*h//2-3)),(64,64)) for y in range(2) for x in range(3)]
for tile,pos in zip((tiles[0],tiles[1],tiles[2],tiles[5],tiles[3],tiles[4]),((0,0),(64,0),(128,0),(192,0),(0,64),(64,64))):atlas.paste(tile,pos)
plants=Image.open(A/'plants-master.png').convert('RGBA')
for box,size,pos in [((0,0,760,1024),(78,128),(0,128)),((780,0,1536,610),(64,64),(192,128)),((760,625,1536,1024),(64,32),(192,192))]:atlas.paste(indexed(plants.crop(box),size,True),pos)
def nearest(rgb):return int(np.sum((pal[1:]-rgb)**2,axis=1).argmin()+1)
sand=[11,68] # Two close warm shades; sparse fine grain, no large dark patches.
grass=[nearest(c) for c in ((78,116,91),(74,112,87),(82,120,95))]
for y in range(8):
 for x in range(32):
  # Duplicate four-row periods, so projected band UVs never cross another tile.
  t=y%4;pattern=(x*7+t*11)%29
  atlas.putpixel((192+x,224+y),sand[1 if (x*17+t*13)%97==2 else 0])
  atlas.putpixel((224+x,224+y),grass[1 if pattern in (3,4,5) else 2 if pattern==19 else 0])
for y in range(16):
 for x in range(64):
  # One RGB555 step of grain, no large patches or random per-frame noise.
  t=y%8;grain=(x*13+t*17)%61
  atlas.putpixel((192+x,232+y),28 if grain in (0,27) else 27)
data=atlas.tobytes()
for y in range(128,256):assert data[y*256+80:y*256+192]==base[y*256+80:y*256+192]
assert data[248*256:]==base[248*256:] or all(data[y*256+192:y*256+256]==base[y*256+192:y*256+256] for y in range(248,256))
(A/'coast-atlas.bin').write_bytes(data);atlas.save(A/'coast-atlas.png');atlas.resize((768,768),Image.Resampling.NEAREST).save(A/'coast-atlas-preview.png')
(A/'materials.json').write_text(json.dumps(dict(sand=sand,grass=grass,road=[27,28],sand_fallback=min(range(128,256),key=lambda i:sum((pal[i]-pal[sand[0]])**2)),grass_fallback=min(range(128,256),key=lambda i:sum((pal[i]-pal[grass[0]])**2))),indent=2))
print('Coast atlas ready; player, sea and foam preserved.')
