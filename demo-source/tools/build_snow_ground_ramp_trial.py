"""Spread forest/snow terrain colors across a longer world-space approach."""
from pathlib import Path
import json,re,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
origin=S['_terrain_active']+1;ramp=origin+2
joined='--panorama' in sys.argv
variant='snow-connected' if joined else 'snow-ground-ramp'
O=R/('outputs/six-route-'+variant);O.mkdir(exist_ok=True)
asm=f'''org 03b48h
prepare:
 ld a,({S['_route_piece']})
 cp 23
 jr z,approach
 cp 24
 jr z,arrival
 jp {S['_prepare_terrain_ground']+3}
approach:
 ld hl,({S['_distance']})
 ld de,13828
 or a
 sbc hl,de
 jr c,inactive
 ld de,-1020
 add hl,de
 jr store
arrival:
 ld hl,({S['_distance']})
 ld a,h
 cp 10
 jr nc,inactive
 ld de,1536
 add hl,de
store:
 ld ({origin}),hl
 ld hl,14868
 ld ({ramp}),hl
 ld a,1
 ld ({S['_terrain_active']}),a
 ret
inactive:
 xor a
 ld ({S['_terrain_active']}),a
 ret
offset:
 ld hl,({origin})
 add hl,bc
 ld a,({S['_route_piece']})
 cp 23
 jr z,scale
 cp 24
 ret nz
scale:
 sra h
 rr l
 sra h
 rr l
 ret
'''
(O/'ramp.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'ramp.asm'),str(O/'ramp.bin'),str(O/'ramp.sym')],check=True)
code=(O/'ramp.bin').read_bytes();assert len(code)<=184
off=int(re.search(r'offset\s+EQU\s+0([0-9A-F]+)H',(O/'ramp.sym').read_text()).group(1),16)
def at(a):return 214*16384+8192+a-0x2400
for suf,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-'+('forest-snow-taper' if joined else 'direct-mesh')+suf);out=R/('outputs/six-route-'+variant+suf);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 assert rom[at(15173):at(15173)+3]==bytes.fromhex('c300d7')
 assert rom[at(14868):at(14868)+9]==bytes([43,47,116,91,90,73,72,64,63])
 p=at(S['_prepare_terrain_ground']);assert rom[p:p+3]==b'\x3a'+S['_route_piece'].to_bytes(2,'little')
 rom[p:p+3]=bytes.fromhex('c3483b')
 needle=b'\x2a'+origin.to_bytes(2,'little')+b'\x09'
 start=at(S['_terrain_ground']);end=at(S['_car_resident_init']);q=rom.find(needle,start,end);assert q>=start
 assert rom.find(needle,q+1,end)==-1
 rom[q:q+4]=b'\xcd'+off.to_bytes(2,'little')+b'\x00'
 # The original mesh expansion and its offset table are unreachable after JP D700.
 rom[at(0x3b48):at(0x3b48)+len(code)]=code
 ranges=[(p,p+3),(q,q+4),(at(0x3b48),at(0x3b48)+len(code))]
 assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(before,rom)) if x!=y)
 assert len(rom)==4194304;(out/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),helper_bytes=len(code),additional_rom_banks=0,scope='Only world-space forest/snow terrain color ramp; route, geometry, collision and timing unchanged.',runtime_verified=False),indent=2))
print('helper bytes',len(code))
