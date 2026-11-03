"""Use one existing scenery slot for generated snow-covered roadside rocks."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import json,re,subprocess,hashlib
from quantization import indexed
from pack_atlas import pack
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-snow-rocks';O.mkdir(exist_ok=True)
pal=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
im=Image.open(R/'assets/snow-rock-source/snow-rock-v1.png').convert('RGBA')
box=im.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox();assert box
im=im.crop(box);im.thumbnail((64,24),Image.Resampling.LANCZOS)
tile=Image.new('RGBA',(64,24));tile.alpha_composite(im,((64-im.width)//2,24-im.height))
tile=indexed(tile,SimpleNamespace(FLAT=pal,CAR_COLORS={}),car=True)
tile.save(O/'rock-native.png');tile.resize((512,192),Image.Resampling.NEAREST).save(O/'rock-preview.png')
old=(R/'assets/snow-atlas.bin').read_bytes();atlas=Image.frombytes('P',(256,256),old);atlas.putpalette(pal);atlas.paste(tile,(192,192));data=atlas.tobytes()
assert all((192<=i%256<256 and 192<=i//256<216) for i,(a,b) in enumerate(zip(old,data)) if a!=b)
oldblocks,oldused=pack(old,147);blocks,used=pack(data,147);assert len(blocks)<=len(oldblocks)
asm='''org 0d7e0h
 ld a,(ix-8)
 or a
 ld a,4
 jr nz,store
 ld a,7
store:
 ld (ix-8),a
 ret
'''
(O/'rocks.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'rocks.asm'),str(O/'rocks.bin')],check=True)
code=(O/'rocks.bin').read_bytes();assert len(code)<=32
for suf,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-snow-packed'+suf);out=R/('outputs/six-route-snow-rocks'+suf);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 for i,block in enumerate(oldblocks):
  at=(147+i)*16384+8192;assert rom[at:at+8192]==block
  rom[at:at+8192]=blocks[i] if i<len(blocks) else b'\xff'*8192
 p=214*16384+8192+0x147a;assert rom[p:p+4]==bytes.fromhex('dd36f804')
 rom[p:p+4]=bytes.fromhex('cde0d700')
 q=(1+(0xd7e0-0x8000)//8192)*16384+8192+(0xd7e0-0x8000)%8192
 assert rom[q:q+len(code)]==bytes(len(code));rom[q:q+len(code)]=code
 allowed=[(p,p+4),(q,q+len(code))]+[((147+i)*16384+8192,(148+i)*16384) for i in range(len(oldblocks))]
 assert all(any(a<=i<b for a,b in allowed) for i,(x,y) in enumerate(zip(before,rom)) if x!=y)
 assert len(rom)==4194304;(out/name).write_bytes(rom);(out/'snow-atlas.bin').write_bytes(data)
 for asset in ('city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),atlas_bytes_before=oldused,atlas_bytes_after=used,atlas_banks=len(blocks),helper_bytes=len(code),scope='Snow stage identity0 uses kind7 rocks; same object positions/count, palette and car textures.',runtime_verified=False),indent=2))
 print(suf,oldused,used,len(code))
