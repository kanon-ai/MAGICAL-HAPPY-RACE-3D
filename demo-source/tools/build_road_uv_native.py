"""Exact road/foam UV calculation using registers instead of compiler stack spills."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-traffic-overtake'+suffix);O=R/('outputs/six-route-road-uv-native'+suffix);O.mkdir(exist_ok=True)
 old=(src/name).read_bytes();rom=bytearray(old)
 assert old[off(0x94d9):off(0x94d9)+3]==bytes.fromhex('3a4be2')
 assert old[off(0x9552):off(0x9552)+3]==bytes.fromhex('11358c')
 assert old[off(0x96cc):off(0x96cc)+6]==bytes.fromhex('dd34ffc3c294')
 index=0x8d if suffix else 0x9d; data=index+2
 asm=f"""org 094d9h
 ld a,(ix-1)
 ld l,a
 ld h,0
 ld de,0e7f6h
 add hl,de
 ld a,(hl)
 inc hl
 ld e,(hl)
 ld d,0
 ld hl,08c35h
 add hl,de
 ld c,(hl)
 ld e,a
 ld hl,08c35h
 add hl,de
 ld b,(hl)
 ; B=depth[k], C=depth[k+1]. Retain both for foam.
 ld a,(0e24bh)
 add a,b
 and 15
 add a,104
 ld d,a
 ; E is clamped signed depth delta, in [-15,0].
 ld a,c
 sub b
 jr nc,zero_delta
 cp 241
 jr nc,delta_ready
 ld a,241
 jr delta_ready
zero_delta:
 xor a
delta_ready:
 add a,d
 ld e,a
 ld a,065h
 out ({index}),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 add a,4
 out ({data}),a
 ld a,053h
 out ({index}),a
 ld a,64
 out ({data}),a
 ld a,d
 out ({data}),a
 ld a,127
 out ({data}),a
 ld a,d
 out ({data}),a
 ld a,127
 out ({data}),a
 ld a,e
 out ({data}),a
 ld a,64
 out ({data}),a
 ld a,e
 out ({data}),a
 ld a,065h
 out ({index}),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 add a,7
 out ({data}),a
 ld a,053h
 out ({index}),a
 ld a,(0e24bh)
 add a,b
 and 7
 add a,120
 ld d,a
 ld a,(0e24bh)
 add a,c
 and 7
 add a,120
 ld e,a
 ld a,64
 out ({data}),a
 ld a,d
 out ({data}),a
 ld a,127
 out ({data}),a
 ld a,d
 out ({data}),a
 ld a,127
 out ({data}),a
 ld a,e
 out ({data}),a
 ld a,64
 out ({data}),a
 ld a,e
 out ({data}),a
 jp 096cch
"""
 (O/'road-uv.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'road-uv.asm'),str(O/'road-uv.bin')],check=True)
 body=(O/'road-uv.bin').read_bytes();limit=0x96cc-0x94d9;assert len(body)<=limit
 at=off(0x94d9);rom[at:at+limit]=body+bytes(limit-len(body))
 assert len(rom)==4194304 and all(at<=i<at+limit for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),native_bytes=len(body),replaced_bytes=limit,scope='UV loop body only; original loop count, BGM polls, geometry and simulation unchanged. Validation pending.'),indent=2))
 print(O.name,len(body))
