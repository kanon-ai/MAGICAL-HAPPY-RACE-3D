"""Enable the prepared snow/city seam without changing simulation or other joins."""
from pathlib import Path
import subprocess, hashlib, json
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
    src=R/('outputs/six-route-snow-city-data'+suffix)
    prior=R/('outputs/six-route-early-seam-taper'+suffix)
    out=R/('outputs/six-route-snow-city-feather'+suffix);out.mkdir(exist_ok=True)
    asm=(prior/'render.asm').read_text()
    needle=' cp 2\n jr z,early\n'
    assert asm.count(needle)==1
    asm=asm.replace(needle,needle+' cp 4\n jr z,early\n')
    needle=' cp 2\n ld a,c\n jr nz,key_ready\n add a,7\nkey_ready:'
    assert asm.count(needle)==1
    asm=asm.replace(needle,' cp 2\n jr z,key_second\n cp 4\n ld a,c\n jr nz,key_ready\n add a,14\n jr key_ready\nkey_second:\n ld a,c\n add a,7\nkey_ready:')
    (out/'render.asm').write_text(asm)
    subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'render.asm'),str(out/'render.bin'),str(out/'render.sym')],check=True)
    code=(out/'render.bin').read_bytes();previous=(prior/'render.bin').read_bytes()
    assert len(previous)<=len(code)<=1024
    p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
    at=211*16384+8192+0x1100
    assert old[at:at+len(previous)]==previous
    assert old[at+len(previous):at+len(code)]==b'\xff'*(len(code)-len(previous))
    rom[at:at+len(code)]=code
    assert len(rom)==4194304 and rom[:at]==old[:at] and rom[at+len(code):]==old[at+len(code):]
    (out/p.name).write_bytes(rom)
    for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    (out/'geometry-layout.json').write_bytes((src/'geometry-layout.json').read_bytes())
    report=dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,scope='Snow to city feather; other joins and simulation preserved; runtime validation pending')
    (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
