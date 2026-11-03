"""Night panorama and its existing city transition samples; no runtime edit."""
from pathlib import Path
import json,hashlib,re,numpy as np
R=Path(__file__).resolve().parents[1]
old=(R/'assets/night-sky.bin').read_bytes();new=(R/'outputs/night-wrap-art/night-sky.bin').read_bytes()
assert len(old)==len(new)==19968
pal=np.array([int(x)*255/31 for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]).reshape(256,3)
city=np.frombuffer((R/'assets/city-sky.bin').read_bytes(),dtype=np.uint8).reshape(78,256)
def bands(data):
 sky=np.frombuffer(data,dtype=np.uint8).reshape(78,256);result=[]
 for pan in range(-48,49,8):
  x=(pan+np.arange(-16,16))&255;t=np.linspace(0,1,32)[None,:,None]
  rgb=pal[city[:,x]]*(1-t)+pal[sky[:,x]]*t
  q=np.argmin((((rgb[:,:,None,:]-pal[None,None,:,:])**2)*[.2126,.7152,.0722]).sum(axis=3),axis=2).astype(np.uint8)
  result.append(np.concatenate((q[:39],q[39:]),axis=1).tobytes())
 return result
before_bands,after_bands=bands(old),bands(new)
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-snow-rocks'+suffix);out=R/('outputs/six-route-night-wrap'+suffix);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom);ranges=[]
 for n in range(3):
  at=(164+n)*16384+8192;a=old[n*8192:(n+1)*8192];b=new[n*8192:(n+1)*8192]
  assert rom[at:at+len(a)]==a;rom[at:at+len(b)]=b;ranges.append((at,at+len(b)))
 for n,(a,b) in enumerate(zip(before_bands,after_bands)):
  bank=[191,196,197,198,199][n//3];at=bank*16384+8192+512+(n%3)*2496
  assert rom[at:at+2496]==a;rom[at:at+2496]=b;ranges.append((at,at+2496))
 assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(before,rom)) if x!=y)
 assert len(rom)==4194304;(out/name).write_bytes(rom)
 for asset in ('snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'night-sky.bin').write_bytes(new)
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),additional_rom_bytes=0,
  code_exact=True,scope='Only night panorama and 13 existing city/night bridge samples. Runtime and art acceptance pending.'),indent=2))
print('Two 4 MiB night panorama trials; code and allocation unchanged.')
