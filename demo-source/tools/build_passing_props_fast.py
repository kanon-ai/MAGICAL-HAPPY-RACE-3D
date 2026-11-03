"""Skip scenery widening work only when no visible object can reach it."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
asm="""org 06500h
 ld a,(0e24fh)
 and 7
 cp 2
 jp z,060ebh
 cp 3
 jp z,060ebh
 cp 1
 ret nz
 ld hl,(0e247h)
 ld de,15364
 or a
 sbc hl,de
 ret c
 jp 060ebh
"""
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-four-arches'+suffix);out=R/('outputs/six-route-passing-props-fast'+suffix);out.mkdir(exist_ok=True)
 (out/'props-fast.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'props-fast.asm'),str(out/'props-fast.bin')],check=True)
 code=(out/'props-fast.bin').read_bytes();p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);at=off(0xa9dd)
 assert old[at:at+2]==bytes.fromhex('eb60'),old[at-1:at+3].hex()
 assert old[at-1]==0xcd
 bank=211*16384+8192+0x500;assert old[bank:bank+len(code)]==b'\xff'*len(code)
 rom[at:at+2]=(0x6500).to_bytes(2,'little');rom[bank:bank+len(code)]=code
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),playable_adoption=False,runtime_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
