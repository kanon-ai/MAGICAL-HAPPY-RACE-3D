"""Precompute expanded row center once; preserve every vertex and face."""
from pathlib import Path
import subprocess, hashlib, json
R=Path(__file__).resolve().parents[1]
def off(a): return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
hashes=['02c335e095bd28ffae455a86692b4ecc6d87c727600cf9c45cec1bb04a0512ae','04f10ad8a837af2252fd00f8682b4e47d0bc59c81d26a18557623c363fcd9a63']
for suffix,sha in zip(('', '-external-88h'), hashes):
 p=next((R/('outputs/six-route-rock-bore-gpu-ring'+suffix)).glob('*.rom'));old=p.read_bytes()
 assert hashlib.sha256(old).hexdigest()==sha
 prior=R/('outputs/six-route-road-row-flags-v2'+suffix)
 oldcode=(prior/'row.bin').read_bytes()
 assert old[off(0x9600):off(0x9600)+79]==oldcode
 assert old[off(0x8dc0):off(0x8dc3)]==bytes.fromhex('c30096')
 source=(prior/'row.asm').read_text()
 start=source.index(' ld hl,0');end=source.index('no_shift:')+len('no_shift:')
 source=source[:start]+''' rrca
 jr c,absolute
 rrca
 jr c,shifted
 ld hl,(0e811h)
 jr sum
shifted:
 ld hl,(08dfeh)
 jr sum
absolute:
 ld hl,0
sum:
 add hl,bc
'''+source[end:]
 setup='''org 08dc3h
 push hl
 push de
 ld hl,(0e811h)
 ld de,(0f6eeh)
 add hl,de
 ld (08dfeh),hl
 pop de
 pop hl
 jp 09600h
'''
 out=R/('outputs/six-route-row-center-cache'+suffix);out.mkdir(exist_ok=True)
 for name,asm in [('row',source),('setup',setup)]:
  (out/(name+'.asm')).write_text(asm)
  subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/(name+'.asm')),str(out/(name+'.bin'))],check=True)
 code=(out/'row.bin').read_bytes();entry=(out/'setup.bin').read_bytes()
 assert len(code)<=80 and len(entry)<=0x8dfe-0x8dc3
 rom=bytearray(old)
 rom[off(0x9600):off(0x9650)]=code+bytes(80-len(code))
 rom[off(0x8dc0):off(0x8dc3)]=bytes.fromhex('c3c38d')
 rom[off(0x8dc3):off(0x8dc3)+len(entry)]=entry
 # Two scratch bytes reside in retired stream code, not an unproven RAM gap.
 rom[off(0x8dfe):off(0x8e00)]=bytes(2)
 (out/p.name).write_bytes(rom)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=sha,bytes=len(rom),row_bytes=len(code),setup_bytes=len(entry),adopted=False,native_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
