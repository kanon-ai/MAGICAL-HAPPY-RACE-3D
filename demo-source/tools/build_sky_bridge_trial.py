from pathlib import Path
import json,hashlib,subprocess,re
import numpy as np
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text());banks=[191,196,197,198,199]
free=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())['free_slots'];assert all([b,8192] in free for b in banks)
data=(R/'outputs/sky-bridge-study/city-night-bands.bin').read_bytes();assert len(data)==13*2496
pal=np.array([int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]).reshape(256,3)
colors=[]
for k in range(33):
 rgb=pal[158]*(1-k/32)+pal[12]*(k/32);colors.append(int(np.argmin(((pal-rgb)**2*np.array([.2126,.7152,.0722])).sum(axis=1))))
for external in (False,True):
 suffix='-external-88h' if external else '';name='MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom' if external else 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
 src=R/f'outputs/six-route-city-trees-world{suffix}';O=R/f'outputs/six-route-sky-bridge{suffix}';O.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 expected='e335940074188f70c96f928b4dd7d2ee299c8cbea0352c4e13d5330811c298c0' if external else '05dd2043a379a72b8dba041d2f50837b3d1948e5fd40a3f5c098acdb7dbea0ec';assert hashlib.sha256(rom).hexdigest()==expected
 control=0x89 if external else 0x99;vram=control-1
 asm=f"""org 06000h
 ; Original HL=pan,DE=destinationY; caller mix lies beyond two return addresses.
 ld (0f6d0h),hl
 ld (0f6d2h),de
 ld hl,4
 add hl,sp
 ld c,(hl)
 inc hl
 ld b,(hl)
 ld (0f6d4h),bc
 push bc
 ld hl,(0f6d0h)
 call {S['_draw_scene_sky']}
 ld a,({S['_scene_target']})
 cp 5
 ret nz
 ; Replace the top's hard vertical divide with one gradual sky color.
 ld a,({S['_camera_mode']})
 or a
 jr z,band
 ld hl,(0f6d4h)
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 ld de,colors
 add hl,de
 ld a,(hl)
 push af
 inc sp
 ld hl,52
 push hl
 ld hl,256
 push hl
 ld de,(0f6d2h)
 ld e,0
 ld hl,0
 call {S['_gfx_fill']}
band:
 ld hl,(0f6d4h)
 ld a,h
 or a
 ret nz
 ld a,l
 or a
 ret z
 ; Nearest8pixel pan bin; source texture32x78 is packed64x39.
 ld a,(0f6d0h)
 add a,52
 srl a
 srl a
 srl a
 ld l,a
 ld h,0
 ld e,l
 ld d,0
 add hl,hl
 add hl,de
 ld de,pointers
 add hl,de
 ld a,(hl)
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld (06000h),a
 ex de,hl
 push hl
 call {S['_gfx_wait']}
 pop hl
 ld a,10
 out ({control}),a
 ld a,08eh
 out ({control}),a
 ld d,10
 ld e,39
upload:
 ld a,192
 out ({control}),a
 ld a,d
 or 040h
 out ({control}),a
 ld bc,{64*256+vram}
 otir
 call {S['_bgm_poll']}
 inc d
 dec e
 jr nz,upload
 ; Clip the feather band against both screen edges.
 ld hl,240
 ld de,(0f6d4h)
 or a
 sbc hl,de
 ld b,32
 ld c,0
 bit 7,h
 jr z,right_edge
 xor a
 sub l
 ld c,a
 ld a,32
 sub c
 ld b,a
 ld hl,0
 jr clip_ready
right_edge:
 ld a,l
 cp 225
 jr c,clip_ready
 neg
 ld b,a
clip_ready:
 ld (0f6d6h),hl
 ld a,b
 ld (0f6d8h),a
 ld a,c
 add a,192
 ld (0f6d9h),a
 call draw_half
 ld hl,(0f6d2h)
 ld de,39
 add hl,de
 ld (0f6d2h),hl
 ld a,(0f6d9h)
 add a,32
 ld (0f6d9h),a
 jp draw_half
draw_half:
 xor a
 push af
 inc sp
 ld hl,39
 push hl
 ld a,(0f6d8h)
 ld l,a
 ld h,0
 push hl
 ld hl,(0f6d2h)
 push hl
 ld hl,(0f6d6h)
 push hl
 ld a,(0f6d9h)
 ld l,a
 ld h,0
 ld de,650
 call {S['_gfx_blit']}
 ret
colors: db {','.join(map(str,colors))}
pointers:
"""
 for n in range(13):asm+=f' db {banks[n//3]}\n dw {0x6200+(n%3)*2496}\n'
 (O/'bridge.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'bridge.asm'),str(O/'bridge.bin')],check=True)
 code=(O/'bridge.bin').read_bytes();assert len(code)<=512,len(code)
 for i,bank in enumerate(banks):
  at=bank*16384+8192;assert rom[at:at+8192]==bytes([255])*8192
  block=bytearray([255])*8192;block[:len(code)]=code
  for j in range(3):
   n=i*3+j
   if n<13:block[512+j*2496:512+(j+1)*2496]=data[n*2496:(n+1)*2496]
  rom[at:at+8192]=block
 # RAM trampoline restores page1 mapper before executing caller return.
 tr=bytes.fromhex('3e bf 32 00 60 cd 00 60 3e fc 32 00 60 e1 c1 e9')
 at=3*16384+8192+0x1bda;assert rom[at:at+len(tr)]==bytes([255])*len(tr);rom[at:at+len(tr)]=tr
 at=16384+8192+0xb7f;assert rom[at:at+3]==b'\xcd'+S['_draw_scene_sky'].to_bytes(2,'little');rom[at:at+3]=bytes.fromhex('cddadb')
 (O/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=expected,helper_bytes=len(code),reserved_halfbanks=banks,free_bytes=344064-40960,scope='City/night32pxpan-quantizedbridge anduniformupper-skyfade. Native tests pending; uploads everytransitionframe.')
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
