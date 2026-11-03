"""Lossless group copy via 16 unrolled LDIs in the retired mirror rectangle body."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
asm='''org 0a945h
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 ld de,0
 ld a,c
 and 15
 jr z,blocks
tail:
 ldi
 dec a
 jr nz,tail
blocks:
 ld a,b
 or c
 jr z,done
block:
'''+ ' ldi\n'*16+''' jp pe,block
done:
 jp 0f05fh
'''
def codeoff(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-traffic-overtake'+suffix);O=R/('outputs/six-route-decoder-copy'+suffix);O.mkdir(exist_ok=True)
 (O/'copy.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'copy.asm'),str(O/'copy.bin')],check=True)
 helper=(O/'copy.bin').read_bytes();assert len(helper)<128
 rom=bytearray((src/name).read_bytes());old=bytes(rom)
 at=8192+0x56;target=codeoff(0xa945)
 assert rom[at:at+9]==bytes.fromhex('4e234623110000edb0')
 assert rom[codeoff(0xa935):target]==bytes.fromhex('3ecf320060cd00603efc320060c351b3')
 # The complete old rectangle path is bypassed at B02C by the accepted mirror renderer.
 assert rom[codeoff(0xb02c):codeoff(0xb02c)+3]==bytes.fromhex('c335a9')
 rom[at:at+9]=bytes.fromhex('c345a9')+bytes(6)
 rom[target:target+len(helper)]=helper
 assert len(rom)==4194304 and all(at<=i<at+9 or target<=i<target+len(helper) for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(helper),scope='Group byte copy only. Rejected multiply trial is not included; original decoder math/data retained. Native validation pending.'),indent=2))
 print(O,len(helper))
