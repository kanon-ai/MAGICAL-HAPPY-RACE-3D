"""Skip per-vertex beach subtraction checks only when beach_extra is zero."""
from pathlib import Path
import subprocess, re, hashlib, json
r=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
    source=r/('outputs/six-route-city-alpine-connected'+suffix)
    oldcode=r/('outputs/six-route-road-row-flags-v2'+suffix)
    asm=(oldcode/'row.asm').read_text()
    body=asm.split('row_stream:',1)[1]
    beach=''' ld a,e
 cp 6
 jr z,beach
 cp 5
 jr nz,no_beach
beach:
 push de
 ld de,(0ecf0h)
 or a
 sbc hl,de
 pop de
no_beach:
'''
    assert beach in body
    fast=body.replace(beach,'')
    for label in ('row_stream','absolute','no_shift'):
        fast=re.sub(r'\b'+label+r'\b','fast_'+label,fast)
    dispatch='''org 09600h
 push hl
 ld hl,(0ecf0h)
 ld a,h
 or l
 pop hl
 jp z,fast_row_stream
'''
    out=r/('outputs/six-route-road-zero-beach'+suffix);out.mkdir(exist_ok=True)
    (out/'row.asm').write_text(dispatch+'row_stream:'+body+'\nfast_row_stream:'+fast)
    subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'row.asm'),str(out/'row.bin')],check=True)
    code=(out/'row.bin').read_bytes();assert len(code)<=172
    path=next(source.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
    at=off(0x9600);before=(oldcode/'row.bin').read_bytes()
    assert old[at:at+len(before)]==before
    assert old[at+len(before):at+172]==bytes(172-len(before))
    rom[at:at+172]=code+bytes(172-len(code))
    assert len(rom)==4194304 and rom[:at]==old[:at] and rom[at+172:]==old[at+172:]
    (out/path.name).write_bytes(rom)
    for f in source.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    report=dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,native_verified=False,scope='Only road row helper; full old path retained for nonzero beach_extra.')
    (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
