"""Cull only the guaranteed inner volume of cockpit traffic, not passing cars."""
from pathlib import Path
import json, subprocess, hashlib

R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
O=R/'outputs/six-route-camera-inside';O.mkdir(exist_ok=True)
traffic=(R/'assets/traffic-packets.bin').read_bytes()
truck=(R/'assets/truck-packets.bin').read_bytes()
models=[traffic[6144+i*156:6144+(i+1)*156] for i in range(3)]+[truck[2048:2204]]
table=bytearray()
for model in models:
    rings=[list(model[i*18:(i+1)*18]) for i in range(6)]
    for ring in rings:
        vertices=[ring[j:j+3] for j in range(0,18,3)]
        assert vertices[0][1]==vertices[5][1]==15
        assert 15<=vertices[1][1]==vertices[4][1]<=vertices[2][1]==vertices[3][1]
        assert len({v[2] for v in vertices})==1
        for left,right in zip(vertices[:3],vertices[3:][::-1]):
            assert left[0]-256 == -right[0]
    for depth in range(384):
        # depth is twice the model Z byte. Convex inner rectangle stays inside
        # all six-sided section edges; floor conservatively shrinks its bounds.
        row=(0,0)
        for a,b in zip(rings,rings[1:]):
            lo,hi=2*a[2],2*b[2]
            if lo <= depth < hi:
                widths=[]
                for index in (9,12,15):
                    widths.append((a[index]*(hi-depth)+b[index]*(depth-lo))//(hi-lo))
                roof=(a[7]*(hi-depth)+b[7]*(depth-lo))//(hi-lo)
                row=(min(widths),roof)
                break
        table.extend(row)
assert len(table)==3072
asm=f'''org 06000h
 ; trampoline saved caller A (variant), preserving SDCC call1 inputs.
 pop af
 push af
 push hl
 push bc
 push de
 ld c,a
 ld a,({S['_car_draw_id']})
 cp 254
 jr z,visible
 ld a,({S['_camera_mode']})
 or a
 jr nz,visible
 ld hl,({S['_projection_base']})
 bit 7,h
 jr z,visible
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
 ld de,380
 or a
 sbc hl,de
 jr nc,visible
 add hl,de
 add hl,hl
 ld a,c
 add a,a
 add a,c
 add a,062h
 ld d,a
 ld e,0
 add hl,de
 ld c,(hl)
 inc hl
 ld b,(hl)
 ld a,c
 or a
 jr z,visible
 ld hl,({S['_projection_x']})
 bit 7,h
 jr z,positive_x
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
positive_x:
 ld e,c
 ld d,0
 sla e
 rl d
 sla e
 rl d
 or a
 sbc hl,de
 jr nc,visible
 ld hl,({S['_projection_y']})
 bit 7,h
 jr z,visible
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
 ld de,61
 or a
 sbc hl,de
 jr c,visible
 add hl,de
 ld e,b
 ld d,0
 sla e
 rl d
 sla e
 rl d
 or a
 sbc hl,de
 jr nc,visible
 ; Camera strictly inside known solid interior: suppress this forward draw.
hidden:
 pop de
 pop bc
 pop hl
 pop af
 ret
visible:
 pop de
 pop bc
 pop hl
 pop af
 push ix
 ld ix,0
 jp 02a64h
'''
(O/'inside.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'inside.asm'),str(O/'inside.bin'),str(O/'inside.sym')],check=True)
code=(O/'inside.bin').read_bytes();assert len(code)<=512
payload=code+b'\xff'*(512-len(code))+table
payload+=b'\xff'*(8192-len(payload))
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
    src=R/('outputs/six-route-snow-rocks'+suffix)
    out=R/('outputs/six-route-camera-inside'+suffix);out.mkdir(exist_ok=True)
    rom=bytearray((src/name).read_bytes());before=bytes(rom)
    view=214*16384+8192
    hook=view+0x65e;stub=view+0x179e;bank=206*16384+8192
    assert rom[hook:hook+6]==bytes.fromhex('dde5dd210000')
    assert rom[stub:stub+9]==bytes.fromhex('0a1617181918191617')
    assert rom[bank:bank+8192]==b'\xff'*8192
    assert rom[view+0x1745:view+0x1748]==bytes.fromhex('c300d7')
    rom[hook:hook+6]=bytes.fromhex('c39e3b000000')
    rom[stub:stub+9]=bytes.fromhex('f53ece320060c30060')
    rom[bank:bank+8192]=payload
    ranges=[(hook,hook+6),(stub,stub+9),(bank,bank+8192)]
    assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(before,rom)) if x!=y)
    assert len(rom)==4194304
    target=out/name
    if not target.exists() or target.read_bytes()!=rom:
        target.write_bytes(rom)
    for asset in ('snow-atlas.bin','city-atlas.bin','night-atlas.bin'):
        (out/asset).write_bytes((src/asset).read_bytes())
    (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),
        helper_bytes=len(code),table_bytes=len(table),bank=206,stub='3B9E-3BA6',
        scope='Cockpit camera strictly inside conservative vehicle inner volume only; exterior near-plane clipping remains unresolved.',
        runtime_verified=False),indent=2))
print('Camera-inside trial:',len(code),'code bytes;',len(table),'table bytes')
