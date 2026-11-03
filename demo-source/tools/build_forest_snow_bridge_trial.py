"""Isolated wider forest/snow join; preserve all other scenes and rules."""
from pathlib import Path
import json,re,subprocess,hashlib,sys
import numpy as np
R=Path(__file__).resolve().parents[1]
taper='--taper' in sys.argv
variant='forest-snow-taper' if taper else 'forest-snow-bridge'
S=json.loads((R/'outputs/symbols.json').read_text())
banks=list(range(201,208))
pal=np.array([int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]).reshape(256,3)
old=np.frombuffer((R/'assets/forest-sky.bin').read_bytes(),dtype=np.uint8).reshape(78,256)
new=np.frombuffer((R/'assets/snow-sky.bin').read_bytes(),dtype=np.uint8).reshape(78,256)
bands=[]
for pan in range(-48,49,16):
 x=(pan+np.arange(-32,32))&255
 t=np.linspace(0,1,64)[None,:,None];t=t*t*(3-2*t)
 rgb=pal[old[:,x]]*(1-t)+pal[new[:,x]]*t
 q=np.argmin((((rgb[:,:,None,:]-pal[None,None,:,:])**2)*[.2126,.7152,.0722]).sum(axis=3),axis=2).astype(np.uint8)
 bands.append(np.concatenate((q[:26],q[26:52],q[52:]),axis=1).tobytes())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-direct-mesh'+suffix);out=R/('outputs/six-route-'+variant+suffix);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom);control=0x89 if suffix else 0x99;vram=control-1
 free=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())['free_slots']
 assert all([bank,8192] in free for bank in banks)
 # Tail-jump into the existing helper for all other stages, preserving arguments.
 asm=f'''org 06000h
 ld a,({S['_scene_target']})
 cp 3
 jr z,forest
 jp 0db60h
forest:
'''
 base=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.asm').read_text()
 head=base[base.index(' ; Original'):base.index(f' ld a,({S["_scene_target"]})')]
 asm+=head
 body=base[base.index('band:\n'):base.index('colors:')]
 body=body.replace('ld hl,240','ld hl,224').replace('ld b,32','ld b,64').replace('ld a,32','ld a,64').replace('cp 225','cp 193')
 body=body.replace('add a,192','add a,0').replace('ld a,192','ld a,0')
 body=body.replace('ld a,10\n out','ld a,11\n out').replace('ld d,10','ld d,34').replace('ld e,39','ld e,26').replace(str(64*256+vram),str(192*256+vram))
 body=body.replace('ld de,39','ld de,26').replace('ld hl,39','ld hl,26').replace('ld de,650','ld de,738').replace('add a,32','add a,64')
 body=body.replace(' jp draw_half\ndraw_half:', ''' call draw_half
 ld hl,(0f6d2h)
 ld de,26
 add hl,de
 ld (0f6d2h),hl
 ld a,(0f6d9h)
 add a,64
 ld (0f6d9h),a
 jp draw_half
draw_half:''')
 body=body.replace('out (153)',f'out ({control})').replace('out (137)',f'out ({control})')
 body=body.replace('add a,52\n srl a\n srl a\n srl a','add a,56\n srl a\n srl a\n srl a\n srl a')
 body=body.replace('Nearest8pixel pan bin; source texture32x78 is packed64x39.','Nearest16pixel pan bin; source64x78 is packed192x26.')
 if taper:
  start=body.index('clip_band:\n');end=body.index('clip_ready:\n',start)
  body=body[:start]+'''clip_band:
 ; Narrow the band at screen edges so no half-blended strip pops in/out.
 ld a,(0f6d4h)
 cp 128
 jr c,radius_positive
 neg
radius_positive:
 cp 32
 jr c,radius_ready
 ld a,32
radius_ready:
 ld e,a
 add a,a
 ld b,a
 ld a,32
 sub e
 ld c,a
 ld hl,256
 ld de,(0f6d4h)
 or a
 sbc hl,de
 ld a,b
 srl a
 ld e,a
 ld d,0
 or a
 sbc hl,de
'''+body[end:]
 asm+=body+'pointers:\n'+''.join(f' db {b}\n dw 06200h\n' for b in banks)
 (out/'bridge.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'bridge.asm'),str(out/'bridge.bin')],check=True)
 code=(out/'bridge.bin').read_bytes();assert len(code)<=512,len(code)
 for bank,data in zip(banks,bands):
  at=bank*16384+8192;assert rom[at:at+8192]==b'\xff'*8192,bank
  rom[at:at+8192]=code+b'\xff'*(512-len(code))+data+b'\xff'*(8192-512-len(data))
 at=3*16384+8192+0x1b60;assert rom[at:at+8]==b'\xff'*8
 rom[at:at+8]=bytes.fromhex('3ebf320060c30060')
 at=3*16384+8192+0x1bda;assert rom[at:at+2]==bytes([0x3e,191]);rom[at+1]=201
 assert len(rom)==4194304
 allowed=[(bank*16384+8192,bank*16384+16384) for bank in banks]
 allowed += [(3*16384+8192+0x1b60,3*16384+8192+0x1b68),(3*16384+8192+0x1bdb,3*16384+8192+0x1bdc)]
 changed=np.flatnonzero(np.frombuffer(before,dtype=np.uint8)!=np.frombuffer(rom,dtype=np.uint8))
 assert all(any(lo<=int(i)<hi for lo,hi in allowed) for i in changed)
 (out/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),additional_reserved_bytes=7*8192,vram=[0,738,192,26],runtime_verified=False),indent=2))
 print(suffix,len(code))
