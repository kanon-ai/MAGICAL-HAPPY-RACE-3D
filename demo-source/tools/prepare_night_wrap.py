"""Native-size/palette candidate from preserved generated night panorama."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import numpy as np,re,json
from quantization import indexed
R=Path(__file__).resolve().parents[1];O=R/'outputs/night-wrap-art';O.mkdir(exist_ok=True)
pal=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
source=Image.open(R/'assets/night-wrap-source/night-wrap-v1.png').convert('RGB')
rgb=np.array(source.resize((256,78),Image.Resampling.LANCZOS),dtype=float)
# Native sky boundary: chase view extends palette index 12 above the panorama.
# Match its first row exactly; taper only eight native sky rows into the art.
for y in range(8):
 t=y/7;t=t*t*(3-2*t)
 rgb[y]=np.array(pal[36:39])*(1-t)+rgb[y]*t
new=indexed(Image.fromarray(np.rint(rgb).astype(np.uint8)),SimpleNamespace(FLAT=pal,CAR_COLORS={}))
assert all(pal[i*3:i*3+3]==pal[36:39] for i in new.tobytes()[:256])
new.save(O/'night-native.png');(O/'night-sky.bin').write_bytes(new.tobytes())
assert len(new.tobytes())==19968
old=Image.frombytes('P',(256,78),(R/'assets/night-sky.bin').read_bytes());old.putpalette(pal)
canvas=Image.new('RGB',(768,200));d=ImageDraw.Draw(canvas);stats={}
for row,(name,im) in enumerate([('existing',old),('generated candidate',new)]):
 rgb=np.array(im.convert('RGB'),dtype=float)
 delta=np.sqrt(((rgb[:,-1]-rgb[:,0])**2).mean(axis=1))
 stats[name]=dict(edge_mean=float(delta.mean()),edge_max=float(delta.max()))
 d.text((0,row*100),name,fill='white');canvas.paste(im.convert('RGB'),(0,row*100+16))
 wrapped=Image.new('RGB',(256,78));wrapped.paste(im.crop((128,0,256,78)).convert('RGB'),(0,0));wrapped.paste(im.crop((0,0,128,78)).convert('RGB'),(128,0))
 canvas.paste(wrapped,(280,row*100+16));d.line((408,row*100+12,408,row*100+15),fill='red')
canvas.resize((1536,400),Image.Resampling.NEAREST).save(O/'comparison.png')
stats.update(bytes_before=19968,bytes_after=19968,palette_unchanged=True,top_row_matches_sky_fill=True,runtime_verified=False,
             scope='Native asset preview. Edge metric alone does not prove seamless architecture. City/night transition bands must also be regenerated before integration.')
(O/'validation.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
