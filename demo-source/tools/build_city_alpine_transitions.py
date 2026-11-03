"""Rebuild both panorama-dependent bridges; keep24px snow and32px night ABI."""
from pathlib import Path
import json,re,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'assets/city-alpine-v2'
p=R/'tools/study_snow_city_bands.py';s=p.read_text().replace("R/'assets/snow-city-transition-study'","R/'assets/city-alpine-v2/transition'").replace('for width in (24,32,48):','for width in (24,):').replace("np_=R/'assets'/f'{new}-sky.bin'","np_=R/'assets/city-alpine-v2/city-sky.bin'")
exec(compile(s,str(p),'exec'),{'__file__':str(p)})
p=R/'tools/plan_snow_city_wider_band.py';s=p.read_text().replace('for width in (32,48):','for width in (24,):').replace('assets/snow-city-transition-study/','assets/city-alpine-v2/transition/').replace('snow-city-wider-band-plan.json','city-alpine-transition-plan.json')
exec(compile(s,str(p),'exec'),{'__file__':str(p)})
plan=json.loads((R/'outputs/city-alpine-transition-plan.json').read_text());assert plan['widths']['24']['fit']
rows=json.loads((A/'transition/snow-city-24.json').read_text());data=(A/'transition/snow-city-24.rle').read_bytes();raw=(A/'transition/snow-city-24.raw').read_bytes()
pal=np.array([int(x)*255/31 for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]).reshape(256,3)
def night_bands(city,night):
    city=np.frombuffer(city,dtype=np.uint8).reshape(78,256);night=np.frombuffer(night,dtype=np.uint8).reshape(78,256);result=[]
    for pan in range(-48,49,8):
        x=(pan+np.arange(-16,16))&255;t=np.linspace(0,1,32)[None,:,None]
        rgb=pal[city[:,x]]*(1-t)+pal[night[:,x]]*t
        q=np.argmin((((rgb[:,:,None,:]-pal[None,None,:,:])**2)*[.2126,.7152,.0722]).sum(axis=3),axis=2).astype(np.uint8)
        result.append(np.concatenate((q[:39],q[39:]),axis=1).tobytes())
    return result
for suffix in ('','-external-88h'):
    src=R/('outputs/six-route-city-alpine-v2-preview'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=bytearray(len(old))
    def write(at,blob):
        assert not any(written[at:at+len(blob)]);rom[at:at+len(blob)]=blob;written[at:at+len(blob)]=b'\1'*len(blob)
    pointers={}
    for job in plan['widths']['24']['placements']:
        i=job['row'];row=rows[i];blob=data[row['offset']:row['offset']+row['bytes']];assert len(blob)==job['bytes'];at=job['at'];write(at,blob)
        pointers[i]=bytes([at//16384])+(0x4000+at%16384).to_bytes(2,'little')
    directory=211*16384+0x7944-0x4000
    write(directory,b''.join(pointers[i] for i in range(182)))
    for i in range(182):
        ptr=rom[directory+3*i:directory+3*i+3];at=ptr[0]*16384+int.from_bytes(ptr[1:],'little')-0x4000;decoded=bytearray()
        while len(decoded)<72:
            tok=rom[at];at+=1;n=(tok&127)+1
            if tok&128:decoded.extend(bytes([rom[at]])*n);at+=1
            else:decoded.extend(rom[at:at+n]);at+=n
        assert decoded==raw[i*72:(i+1)*72]
    night=(src/'night-sky.bin').read_bytes()
    before=night_bands((R/'assets/city-sky.bin').read_bytes(),night);after=night_bands((A/'city-sky.bin').read_bytes(),night)
    for i,(a,b) in enumerate(zip(before,after)):
        at=[191,196,197,198,199][i//3]*16384+8192+512+(i%3)*2496
        assert old[at:at+2496]==a;write(at,b)
    assert len(rom)==4194304 and all(a==b or written[i] for i,(a,b) in enumerate(zip(old,rom)))
    out=R/('outputs/six-route-city-alpine-connected'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
    for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    (out/'manifest.json').write_text(json.dumps({'bytes':len(rom),'sha256':hashlib.sha256(rom).hexdigest(),'snow_rows_exact':182,'night_bands_exact':13,'code_changed':False,'adopted':False,'scope':'Both dependent panorama bridges regenerated; native verification pending'},indent=2));print(out.name)
