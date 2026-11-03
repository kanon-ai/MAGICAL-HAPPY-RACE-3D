"""City boulevard material/ground trial. Uses existing eight faces per road band.

Executable helper lives in a reserved ROM upper half-bank; RAM trampolines
restore mapper252 before returning. Public build/assets are never overwritten.
"""
from pathlib import Path
import json,hashlib,subprocess,re
from pack_atlas import pack
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
layout=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())
reserved=[(188,8192),(189,8192),(190,8192)];assert all(list(p) in layout['free_slots'] for p in reserved)
city=bytearray((R/'assets/city-atlas.bin').read_bytes());old_city=bytes(city)
# Native material pattern: eight-row period, staggered concrete paving slabs.
for y in range(240,256):
 for x in range(128,192):
  yy=y-240;xx=x-128;shift=8 if (yy//4)&1 else 0
  grout=yy%4==0 or (xx+shift)%16==0
  city[y*256+x]=72 if grout else (64 if ((xx+shift)//16+yy//4)&1 else 69)
assert all(city[i]==old_city[i] for i in range(65536) if not (240<=i//256<256 and 128<=i%256<192))
oldblocks,_=pack(old_city,156);newblocks,used=pack(city,156);assert len(newblocks)<=len(oldblocks)
night=bytearray((R/'assets/night-atlas.bin').read_bytes());old_night=bytes(night)
for y in range(240,256):night[y*256+128:y*256+192]=city[y*256+128:y*256+192]
assert all(night[i]==old_night[i] for i in range(65536) if not (240<=i//256<256 and 128<=i%256<192))
oldnightblocks,_=pack(old_night,167);newnightblocks,night_used=pack(night,167)
assert len(newnightblocks)<=len(oldnightblocks)
for external in (False,True):
 suffix='-external-88h' if external else '';name='MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom' if external else 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
 source=R/f'outputs/six-route-ground-crop{suffix}'/name;original=source.read_bytes();rom=bytearray(original)
 expected='c6f97abb3aee33a2456545a5fece24add15bbd3983d8e8c24012d4c667c8d41c' if external else '49d778af9d8167788f718ed11280bb01e168c1987760b862be48c18e673762f3'
 assert hashlib.sha256(original).hexdigest()==expected
 O=R/f'outputs/six-route-city-walk-continuity{suffix}';O.mkdir(exist_ok=True)
 port=0x8d if external else 0x9d
 asm=f"""org 06000h
 jp left_faces
 jp right_face
 jp pavement_uv
is_city:
 ld a,({S['_route_piece']})
 sub 32
 cp 8
 ret
left_faces:
 ; Preserve the original cache address until it has been written.
 ld a,(ix-8)
 ld d,a
 ld a,({S['_route_piece']})
 cp 9
 jr nc,left_inland
 ld a,d
 xor 128
 jr left_store
left_inland:
 call is_city
 ld a,d
 jr nc,left_store
 xor 64
left_store:
 ld (bc),a
 call sync_right
 ld c,(ix-8)
 ld hl,left_land
 ld a,({S['_route_piece']})
 cp 9
 jr nc,left_land_ready
 ld hl,degenerate
 ld c,128
left_land_ready:
left_color_ready:
 xor a
 call face
 call is_city
 jr c,city_faces
 ld a,3
 ld hl,old_right_verge
 ld c,11
 jp face
city_faces:
 ld a,3
 ld hl,right_land
 ld c,(ix-8)
 call face
 ld a,6
 ld hl,left_walk
 ld c,128
 call face
 ld a,7
 ld hl,left_curb
 ld c,73
 jp face
sync_right:
 ; A stage/material change must also reset face1 even if its color cache hit.
 ld a,(ix-8)
 push af
 ld a,({S['_route_piece']})
 cp 8
 jr c,shade_right
 ld a,(ix-8)
 cp 43
 jr nz,right_sync_ready
shade_right:
 ld a,(ix-1)
 ld hl,{S['_sea_crest']-74}
 ld e,a
 ld d,0
 add hl,de
 ld e,(hl)
 ld d,0
 ld hl,36549
 add hl,de
 ld a,(hl)
 add a,40
 ld (ix-8),a
right_sync_ready:
 call right_face
 pop af
 ld (ix-8),a
 ret
right_face:
 call is_city
 ld hl,old_right_land
 ld c,(ix-8)
 jr nc,right_ready
 ld hl,right_walk
 ld c,128
right_ready:
 ld a,1
 jp face
face:
 ; A=face within band, HL=four relative vertices, C=material.
 ld e,a
 ld a,058h
 out ({port}),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 add a,e
 out ({port+2}),a
 ld a,052h
 out ({port}),a
 ld d,(ix-9)
 ld b,4
face_vertices:
 ld a,(hl)
 add a,d
 out ({port+2}),a
 inc hl
 djnz face_vertices
 xor a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 ld a,c
 out ({port+2}),a
 ret
pavement_uv:
 call is_city
 jr nc,original_uv
 ; Unwrap one eight-row period into the duplicated 16-row paving strip.
 ld a,(ix-5)
 cp c
 jr nc,uv_unwrapped
 ld a,c
 sub 8
 ld c,a
uv_unwrapped:
 ld e,1
 call select_uv
 ld e,6
 call select_uv
 ret
select_uv:
 ld a,065h
 out ({port}),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 add a,e
 out ({port+2}),a
 ld a,053h
 out ({port}),a
 ld a,0
 out ({port+2}),a
 ld a,(ix-5)
 out ({port+2}),a
 ld a,63
 out ({port+2}),a
 ld a,(ix-5)
 out ({port+2}),a
 ld a,63
 out ({port+2}),a
 ld a,c
 out ({port+2}),a
 ld a,0
 out ({port+2}),a
 ld a,c
 out ({port+2}),a
 ret
original_uv:
 ld a,64
 out ({port+2}),a
 ld a,(ix-5)
 out ({port+2}),a
 ld a,127
 out ({port+2}),a
 ld a,(ix-5)
 out ({port+2}),a
 ld a,127
 out ({port+2}),a
 ld a,c
 out ({port+2}),a
 ld a,64
 out ({port+2}),a
 ld a,c
 out ({port+2}),a
 ret
left_land: db 0,7,19,12
degenerate: db 0,0,0,0
old_right_verge: db 3,4,16,15
right_land: db 5,9,21,17
left_walk: db 6,1,13,18
left_curb: db 7,6,18,19
old_right_land: db 4,5,17,16
right_walk: db 3,5,17,15
"""
 def assemble(stem,code):
  (O/(stem+'.asm')).write_text(code)
  subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/(stem+'.asm')),str(O/(stem+'.bin')),str(O/(stem+'.sym'))],check=True)
  return (O/(stem+'.bin')).read_bytes()
 code=assemble('city-helper',asm);assert len(code)<=8192
 rom[188*16384+8192:189*16384]=code+bytes([255])*(8192-len(code))
 ram=f"""org 0dac1h
 ld a,188
 ld (06000h),a
 call 06000h
 ld a,252
 ld (06000h),a
 ret
org 0dacfH
 ld a,(hl)
 ld d,a
 ld a,({S['_route_piece']})
 cp 9
 jr nc,cache_inland
 ld a,d
 xor 128
 jr cache_sub
cache_inland:
 sub 32
 cp 8
 ld a,d
 jr nc,cache_sub
 xor 64
cache_sub:
 sub (ix-8)
 ret
org 0daf0h
 ld c,a
 ld a,({S['_route_piece']})
 sub 32
 cp 8
 ld a,c
 jr nc,old_table
 add a,189
 jr select_bank
old_table:
 add a,212
select_bank:
 ld (06000h),a
 ret
org 0db09h
 ld a,188
 ld (06000h),a
 call 06003h
 ld a,252
 ld (06000h),a
 ; Match road_face's callee cleanup of three stack argument bytes.
 pop hl
 pop de
 inc sp
 jp (hl)
 defs 0db2bh-$,255
"""
 helpers=assemble('city-trampolines',ram);assert len(helpers)==106
 at=3*16384+8192+0x1ac1
 oldhelper=(R/f'outputs/six-route-inland-ground{suffix}/inland-ground.bin').read_bytes();assert rom[at:at+106]==oldhelper
 rom[at:at+106]=helpers
 def patch(offset,old,new):
  assert rom[offset:offset+len(old)]==old,(hex(offset),rom[offset:offset+len(old)].hex(),old.hex())
  assert len(old)==len(new);rom[offset:offset+len(old)]=new
 code_start=16384+8192
 oldcmp=rom[code_start+0x130d:code_start+0x1311];assert oldcmp[0]==0xcd and oldcmp[-1]==0
 patch(code_start+0x130d,oldcmp,bytes.fromhex('cd cf da 00'))
 patch(code_start+0xda7,bytes.fromhex('c6 d4 32 00 60'),bytes.fromhex('cd f0 da 00 00'))
 patch(code_start+0x142f,bytes.fromhex('cd 4f 8d'),bytes.fromhex('cd 09 db'))
 olduv=rom[code_start+0x16ac:code_start+0x16cc]
 assert olduv[:2]==bytes.fromhex('3e 40') and len(olduv)==32
 uv=assemble('city-uv-trampoline',"""org 096ach
 ld a,188
 ld (06000h),a
 call 06006h
 ld a,252
 ld (06000h),a
 jp 096cch
""")
 patch(code_start+0x16ac,olduv,uv+bytes(32-len(uv)))
 transfer=bytearray((R/'assets/road-transfer.bin').read_bytes());assert len(transfer)==16384
 for w in range(256):
  half=w+(w>>2);shoulder=max(1,w//10)
  for vertex,x,absolute in [(5,half+shoulder+w*3//4,0),(9,2048,1)]:
   at=w*64+vertex*4;transfer[at:at+4]=x.to_bytes(2,'little',signed=True)+bytes([0,absolute])
 for i in range(2):rom[(189+i)*16384+8192:(190+i)*16384]=transfer[i*8192:(i+1)*8192]
 for i,block in enumerate(oldblocks):
  at=(156+i)*16384+8192;assert original[at:at+8192]==block
  rom[at:at+8192]=newblocks[i] if i<len(newblocks) else bytes([255])*8192
 for i,block in enumerate(oldnightblocks):
  at=(167+i)*16384+8192;assert original[at:at+8192]==block
  rom[at:at+8192]=newnightblocks[i] if i<len(newnightblocks) else bytes([255])*8192
 (O/'night-atlas.bin').write_bytes(night)
 # The city's broad ground and its approach/exit ramps use the same green.
 scene=255*16384+8192
 colors=bytes([43,75,43,63,91,9]);region=bytes(rom[scene:scene+1344]);assert region.count(colors)==1
 at=scene+region.index(colors);rom[at+4]=43
 view=214*16384+8192;region=bytes(rom[view:view+6144])
 old_ramps=bytes([63,64,64,72,72,82,82,90,91,91,116,121,124,125,151,184,194,9]);assert region.count(old_ramps)==1
 at=view+region.index(old_ramps);rom[at:at+18]=bytes([63,64,72,73,90,91,116,47,43,43,42,5,5,5,5,9,9,9])
 assert len(rom)==4194304
 (O/name).write_bytes(rom);(O/'city-atlas.bin').write_bytes(city);(O/'city-road-transfer.bin').write_bytes(transfer)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=expected,bytes=len(rom),helper_rom_bytes=len(code),new_halfbanks=reserved,free_bytes=368640-3*8192,city_atlas_packed_bytes=used,city_geometry_route_pieces=[32,39],ground_transition_route_pieces=[31,32,39,40],night_atlas_shared_pavement=True,night_atlas_packed_bytes=night_used,scope='City sidewalks and green ground, with shared pavement in streamed night atlas. Runtime results stored separately.')
 (O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
