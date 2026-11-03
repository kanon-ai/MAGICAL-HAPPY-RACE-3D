"""A compact cab-over box truck, using 52 vertices and the existing 25-face budget.

The footprint and axle centers match the established passenger-car envelope;
the cargo box and cabin are modelled separately along shared section rings.
"""
from pathlib import Path
import json,re
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
model=[]
# z, bottom width, belt width, belt height, roof width, roof height
sections=[(0,340,352,880,352,920),(300,340,352,880,352,920),
          (1050,340,352,880,352,920),(1200,336,356,340,316,760),
          (1700,332,356,340,316,760),(1900,316,348,260,320,580)]
for z,b,shoulder,sy,upper,uy in sections:
    model.extend([(-b,60,z),(-shoulder,sy,z),(-upper,uy,z),
                  (upper,uy,z),(shoulder,sy,z),(b,60,z)])
for z in (220,1360):
    model.extend([(-328,y,z+d) for y,d in [(60,0),(0,60),(0,260),(60,320),(220,320),(280,260),(280,60),(220,0)]])
faces=[]
def face(ids,color=14,uv=None):faces.append(list(ids)+[color]+(uv or [0]*8))
panel=[224,40,224,32,255,32,255,40]
glass=[192,31,192,16,223,16,223,31]
for k in range(5):
    a=k*6;b=a+6
    face([a+2,a+3,b+3,b+2],128 if k==4 else 14,[192,15,223,15,223,0,192,0] if k==4 else None)
    face([a+1,a+2,b+2,b+1],128 if k>=3 else 14,glass if k>=3 else None)
    face([a,a+1,b+1,b],128,panel)
face([0,1,4,5],128,[224,43,224,32,255,32,255,43])
face([1,2,3,4],14)
face([30,31,34,35],128,[192,43,192,32,223,32,223,43])
face([31,32,33,34],15)
for base in (36,44):
    for ids in [(0,1,2,3),(0,3,4,7),(7,4,5,6)]:
        uv=[]
        for j in ids:
            _,y,z=model[base+j];start=model[base][2]
            uv += [224+round((z-start)/320*31),31-round(y/280*31)]
        face([base+j for j in ids],128,uv)
assert len(model)==52 and len(faces)==25
packets=bytearray()
for near in (False,True):
    fs=[];uvs=[]
    order=[17,18]+[12-(j//3)*3+j%3 if j<15 else (j if j<17 else j+2) for j in range(23)]
    for k in order:
        if near and k in (15,16):continue
        f=faces[k]
        for reverse in (False,True):
            ids=f[:4][::-1] if reverse else f[:4]
            fs.extend(ids+[0]*6+[f[4]])
            pairs=[f[5:][t:t+2] for t in range(0,8,2)]
            if reverse:pairs.reverse()
            uvs.extend(v for pair in pairs for v in pair)
    block=bytes([len(fs)//11])+bytes(fs)+bytes(uvs)
    assert len(block)<=1024
    packets.extend(block+bytes(1024-len(block)))
for scale in (1,.75):
    for x,y,z in model:packets.extend((round(x*scale/4)&255,round(y*scale/4),round(z*scale/10)))
assert len(packets)==2360
(R/'assets/truck-packets.bin').write_bytes(packets)
# Occupy only the unused area below the shared wheel; preserve every existing UV.
vram=bytearray((R/'checkpoints/storage-verified/assets/vram.bin').read_bytes())
texture=Image.new('P',(32,12),14);d=ImageDraw.Draw(texture)
d.rectangle((1,0,30,9),fill=15)
for y in (2,4,6,8):d.line((2,y,29,y),fill=14)
d.line((15,0,15,9),fill=14)
d.line((9,1,9,9),fill=14);d.line((22,1,22,9),fill=14)
d.rectangle((0,10,31,11),fill=12)
d.rectangle((1,10,5,10),fill=51);d.rectangle((26,10,30,10),fill=51)
d.rectangle((13,10,18,10),fill=15)
pixels=texture.tobytes()
for y in range(12):vram[65536+(32+y)*256+224:65536+(32+y)*256+256]=pixels[y*32:(y+1)*32]
(R/'assets/vram.bin').write_bytes(vram)
values=[int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{',1)[1].split('}',1)[0])]
texture.putpalette([round(v*255/31) for v in values]);texture.resize((320,120),Image.Resampling.NEAREST).save(R/'assets/truck-material-preview.png')
(R/'assets/truck-model.json').write_text(json.dumps(dict(vertices=model,faces=faces,
    footprint_matches_existing=True,face_count=25,vertex_count=52,
    texture_region=[224,244,255,255],resident_slots=[768,832],model_ram=['F700-F79B','F79C-F837']),indent=2))
print('Truck: 2360 model/packet bytes; 384 reused VRAM pixels; unchanged footprint.')
