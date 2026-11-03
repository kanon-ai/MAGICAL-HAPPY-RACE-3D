"""Approved front-contact movement cap; no new rear collision or clock rule."""
from pathlib import Path
import json,subprocess,hashlib,sys
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
spaced='--traffic-spaced' in sys.argv
rhythm='--traffic-rhythm' in sys.argv or spaced
passing='--passing-zones' in sys.argv or rhythm
flow='--traffic-flow' in sys.argv or passing
variant='traffic-spaced' if spaced else 'traffic-rhythm' if rhythm else 'passing-zones' if passing else 'traffic-flow' if flow else 'front-gap'
O=R/('outputs/six-route-'+variant);O.mkdir(exist_ok=True)
asm=f'''org 06000h
 push de
 ld b,5
loop:
 ld a,5
 sub b
 ld e,a
 ld d,0
 ld hl,{S['_traffic_contact']}
 add hl,de
 ld a,(hl)
 or a
 jr z,next
 ld hl,{S['_traffic_tag']}
 add hl,de
 ld a,(hl)
 cp 2
 jr z,next
 ld hl,{S['_traffic_lane']}
 add hl,de
 ld a,(hl)
 ld e,a
 add a,a
 sbc a,a
 ld d,a
 ld hl,({S['_player_x']})
 or a
 sbc hl,de
 bit 7,h
 jr z,positive
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
positive:
 ld a,h
 or a
 jr nz,next
 ld a,l
 cp 28
 jr nc,next
 ld a,5
 sub b
 add a,a
 ld e,a
 ld d,0
 ld hl,{S['_traffic_z']}
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld de,({S['_distance']})
 or a
 sbc hl,de
 ld a,h
 and 03fh
 ; All rear gaps and forward gaps >=256 remain unaffected.
 or a
 jr nz,next
 ld a,l
 sub 16
 jr nc,limit
 xor a
limit:
 cp c
 jr nc,next
 ld c,a
next:
 djnz loop
 pop de
 ; Reproduce the displaced instruction before original distance addition.
 ld hl,{S['_distance']}
 ret
'''
if flow:
 asm=asm.replace(' ld c,a\nnext:',f''' ld c,a
 ; Match indicated speed to the lead vehicle when movement was capped.
 ld a,5
 sub b
 ld e,a
 ld d,0
 ld hl,{S['_traffic_step_move']}
 add hl,de
 ld a,(hl)
 cp 8
 jr c,speed_index
 ld a,7
speed_index:
 ld e,a
 ld hl,speeds
 add hl,de
 ld a,(hl)
 ld hl,{S['_speed']}
 cp (hl)
 jr nc,next
 ld (hl),a
 inc hl
 ld (hl),0
next:''')
 asm=asm.replace('djnz loop','dec b\n jp nz,loop')
 for condition in ('z','nz','nc'):
  asm=asm.replace('jr '+condition+',next','jp '+condition+',next')
 asm+='''speeds: db 0,3,7,10,14,18,21,25
 org 06100h
lane_gate:
 push bc
 ld a,(ix-4)
 cp 1
 jr z,lane_allowed
 ld b,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,b
 ld b,a
'''+f''' ld a,({S['_event_tick']})
 add a,b
 and 127
 jr z,lane_allowed
 pop bc
 inc sp
 inc sp
 jp 0a1a2h
lane_allowed:
 pop bc
 ret
'''
if rhythm:
 asm=asm.replace(' cp 8\n jr c,speed_index\n ld a,7', ' cp 32\n jr c,speed_index\n ld a,31')
 asm=asm.replace('speeds: db 0,3,7,10,14,18,21,25', 'speeds: db '+','.join(str(i*18//5) for i in range(32)))
if passing:
 # Use the existing lane-clearance and smooth steering path. In two middle
 # pieces of each stage, keep left once there; cars on the right may merge
 # only after the original neighbouring-car/player clearance checks pass.
 asm=asm.replace('lane_gate:\n push bc\n',f'''lane_gate:
 push bc
 push hl
 ld a,({S['_route_piece']})
 and 7
 sub 2
 cp 2
 jr nc,ordinary_zone
 ld a,(ix-4)
 ld l,a
 ld h,0
 ld bc,{S['_traffic_lane']}
 add hl,bc
 bit 7,(hl)
 pop hl
 jr z,lane_allowed
 jr lane_denied
ordinary_zone:
 pop hl
''')
 asm=asm.replace(' jr z,lane_allowed\n pop bc\n inc sp',
                 ' jr z,lane_allowed\nlane_denied:\n pop bc\n inc sp')
if spaced:
 asm+=f'''org 06200h
 ; Respawn outside the visible range, with more open road in passing areas.
 ld bc,2500
 ld a,({S['_route_piece']})
 and 7
 sub 2
 cp 2
 jr nc,spawn_base
 ld bc,6000
spawn_base:
 ld hl,({S['_distance']})
 add hl,bc
 ld b,h
 ld c,l
 ret
'''
(O/'gap.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'gap.asm'),str(O/'gap.bin')],check=True)
code=(O/'gap.bin').read_bytes();assert len(code)<1024
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-night-wrap'+suffix);out=R/('outputs/six-route-'+variant+suffix);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom);view=214*16384+8192
 needle=b'\x21'+S['_distance'].to_bytes(2,'little')+bytes.fromhex('7e8177')
 at=rom.find(needle,view+0x1072,view+0x1100);assert at>=0
 hook=at-view+0x2400;stub=view+0x179e;bank=206*16384+8192
 assert rom[stub:stub+8]==bytes.fromhex('0a16171819181916')
 assert rom[bank:bank+8192]==b'\xff'*8192
 assert rom[view+0x1745:view+0x1748]==bytes.fromhex('c300d7')
 rom[at:at+3]=bytes.fromhex('cd9e3b')
 rom[stub:stub+8]=bytes.fromhex('3ece320060c30060')
 rom[bank:bank+len(code)]=code
 ranges=[(at,at+3),(stub,stub+8),(bank,bank+len(code))]
 if flow:
  def physical(address):return (1+(address-0x8000)//8192)*16384+8192+(address-0x8000)%8192
  gate=physical(0xa03b);trampoline=physical(0xd7ee)
  assert rom[gate:gate+3]==bytes.fromhex('caa2a1')
  assert rom[trampoline:trampoline+8]==bytes(8)
  rom[gate:gate+3]=bytes.fromhex('cdeed7')
  rom[trampoline:trampoline+8]=bytes.fromhex('3ece320060c30061')
  margin=physical(0xa118)
  assert rom[margin:margin+6]==bytes.fromhex('3e88bb3eff9a')
  # Existing signed compare: player > -120 becomes > -1200 (75m).
  rom[margin:margin+6]=bytes.fromhex('3e50bb3efb9a')
  ranges += [(gate,gate+3),(trampoline,trampoline+8),(margin,margin+6)]
  if rhythm:
   for address,old,new in [(0xa262,bytes.fromhex('c604'),bytes.fromhex('c608')),
                           (0xa28d,bytes.fromhex('dd36f507'),bytes.fromhex('dd36f50e'))]:
    p=physical(address);assert rom[p:p+len(old)]==old,(hex(address),rom[p:p+len(old)].hex())
    rom[p:p+len(old)]=new;ranges.append((p,p+len(new)))
  if spaced:
   p=physical(0xa5f9);old=b'\x3a'+S['_distance'].to_bytes(2,'little')+bytes.fromhex('c6e84f3a')+(S['_distance']+1).to_bytes(2,'little')+bytes.fromhex('ce0347')
   assert rom[p:p+12]==old
   rom[p:p+12]=bytes.fromhex('cdf6d7')+bytes(9);ranges.append((p,p+12))
   p=physical(0xd7f6);assert rom[p:p+8]==bytes(8)
   rom[p:p+8]=bytes.fromhex('3ece320060c30062');ranges.append((p,p+8))
 assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(before,rom)) if x!=y)
 assert len(rom)==4194304;(out/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),hook=hook,helper_bytes=len(code),
  traffic_flow=flow,passing_zones=passing,traffic_rhythm=rhythm,spaced=spaced,scope='Front contact gap16 cap. Optional traffic-flow: staggered decisions for all five cars, 75m player-approach clearance, lead-speed cap when blocked. Passing zones: pieces 2/3 within each stage keep left through existing safe lane changes, freeing the right lane. Rhythm: cruise steps8..10, passing14. Spaced: respawn base2500 normally,6000 in passing areas, plus existing slot offset/clearance. Road geometry remains two lanes. No lap clock/rear collision change.',runtime_verified=False),indent=2))
print('front-gap helper',len(code),'bytes; hook',hex(hook))
