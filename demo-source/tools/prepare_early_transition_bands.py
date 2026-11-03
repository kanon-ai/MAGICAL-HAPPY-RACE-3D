"""Generate native-palette transition feather bands; measure only, no ROM write."""
from pathlib import Path
import json,re
import numpy as np
from pack_atlas import encode
R=Path(__file__).resolve().parents[1];O=R/'assets/early-transition-bands';O.mkdir(exist_ok=True)
pal=np.array([int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])],dtype=float).reshape(256,3)
report=[]
for width in (24,32,48):
 for old,new in [('coast','canyon'),('canyon','forest')]:
  op=R/'assets'/('vram.bin' if old=='coast' else f'{old}-sky.bin');np_=R/'assets'/f'{new}-sky.bin'
  if not op.exists():
   print('Missing',op);raise SystemExit(1)
  a=np.frombuffer(op.read_bytes()[:19968],dtype=np.uint8).reshape(78,256);b=np.frombuffer(np_.read_bytes(),dtype=np.uint8).reshape(78,256)
  blobs=[];raws=[];rows=[]
  for pan in range(-48,49,16):
   x=(pan+np.arange(-width//2,width//2))&255
   t=np.linspace(0,1,width)[None,:,None];t=t*t*(3-2*t)
   rgb=pal[a[:,x]]*(1-t)+pal[b[:,x]]*t
   q=np.argmin((((rgb[:,:,None,:]-pal[None,None,:,:])**2)*[.2126,.7152,.0722]).sum(axis=3),axis=2).astype(np.uint8)
   packed=np.concatenate((q[:26],q[26:52],q[52:]),axis=1).tobytes();raws.append(packed)
   for y in range(26):
    raw=packed[y*width*3:(y+1)*width*3];e=bytes(encode(raw));rest=bytearray();i=0
    while i<len(e):
     tok=e[i];i+=1;n=(tok&127)+1
     if tok&128:rest.extend(bytes([e[i]])*n);i+=1
     else:rest.extend(e[i:i+n]);i+=n
    assert rest==raw
    rows.append({'pan':pan,'row':y,'offset':sum(map(len,blobs)),'bytes':len(e)});blobs.append(e)
  name=f'{old}-{new}-{width}';(O/(name+'.rle')).write_bytes(b''.join(blobs));(O/(name+'.raw')).write_bytes(b''.join(raws));(O/(name+'.json')).write_text(json.dumps(rows))
  report.append({'name':name,'width':width,'raw_bytes':sum(map(len,raws)),'rle_bytes':sum(map(len,blobs)),'directory_bytes':len(rows)*3,'all_rows_exact':True})
(O/'manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
