"""Isolated zero beach-factor fast path; preserve existing row streamer."""
from pathlib import Path
import hashlib, json, subprocess
R=Path(__file__).resolve().parents[1]
def off(a): return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
hashes=['02c335e095bd28ffae455a86692b4ecc6d87c727600cf9c45cec1bb04a0512ae','04f10ad8a837af2252fd00f8682b4e47d0bc59c81d26a18557623c363fcd9a63']
for suffix,sha in zip(('', '-external-88h'),hashes):
    source=next((R/('outputs/six-route-rock-bore-gpu-ring'+suffix)).glob('*.rom'))
    old=source.read_bytes(); assert hashlib.sha256(old).hexdigest()==sha
    assert old[off(0x8dc0):off(0x8dc3)]==bytes.fromhex('c30096')
    assert old[off(0x8d7f):off(0x8d9b)]==bytes.fromhex('3aefec4fdd7e05edc9cb3ccb1dcb3ccb1dcb3ccb1dcb3ccb1d22f0ec')
    # Old8dc3..8e01 stream is unreachable:8dc0 redirects to9600;
    # that current79byte helper returns directly to8e02.
    prior=(R/('outputs/six-route-road-row-flags-v2'+suffix)/'row.bin').read_bytes()
    assert old[off(0x9600):off(0x9600)+len(prior)]==prior and prior[-3:]==bytes.fromhex('c3028e')
    out=R/('outputs/six-route-row-zero-factor'+suffix);out.mkdir(exist_ok=True)
    asm='''org 08dc3h
 ld a,(0ecefh)
 or a
 jr z,zero
 ld c,a
 ld a,(ix+5)
 db 0edh,0c9h
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 jr store
zero:
 ld hl,0
store:
 ld (0ecf0h),hl
 jp 08d9bh
'''
    (out/'factor.asm').write_text(asm)
    subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'factor.asm'),str(out/'factor.bin')],check=True)
    code=(out/'factor.bin').read_bytes();assert len(code)<=0x8e02-0x8dc3
    rom=bytearray(old);rom[off(0x8d7f):off(0x8d7f)+3]=bytes.fromhex('c3c38d')
    rom[off(0x8dc3):off(0x8dc3)+len(code)]=code
    changed=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
    assert all(off(0x8d7f)<=i<off(0x8d7f)+3 or off(0x8dc3)<=i<off(0x8dc3)+len(code) for i in changed)
    assert len(rom)==4194304
    (out/source.name).write_bytes(rom)
    report=dict(source_sha256=sha,sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),changed_bytes=len(changed),native_verified=False,adopted=False)
    (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
