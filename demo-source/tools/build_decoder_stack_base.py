"""Keep a variable-field base on stack instead of global RAM."""
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];w=r/'work/decoder-stack-base';w.mkdir(exist_ok=True)
asm='''org 0f126h
 ex af,af'
 ld a,(hl)
 inc hl
 push af
 ld a,(hl)
 inc hl
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 push hl
 ld h,b
 ld l,c
 ld (06000h),a
 ld a,(0f1bch)
 call 0f159h
 pop hl
 pop bc
 add a,b
store:
 ld (de),a
 inc de
 exx
 djnz more
 exx
 ret
more:
 exx
 jr 0f0f8h
'''
(w/'body.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'body.asm'),str(w/'body.bin')],check=True)
body=(w/'body.bin').read_bytes();assert len(body)==35 and body[25]==0x12
expected=bytes.fromhex('087e2332bdf17e234e234623e560693200603abcf1cd59f14f3abdf181e11213d91002d9c9d918aa')
for suffix in ('','-external-88h'):
 src=r/('outputs/six-route-city-alpine-connected'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 at=8192+0x126;assert old[at:at+40]==expected and old[at-2:at]==bytes.fromhex('181e')
 rom[at:at+40]=body+bytes(5);rom[at-1]=25
 assert len(rom)==4194304 and rom[:at-1]==old[:at-1] and rom[at+40:]==old[at+40:]
 out=r/('outputs/six-route-decoder-stack-base'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,native_verified=False,scope='Variable field decoder and constant-path store branch only; layout and packed data unchanged.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
