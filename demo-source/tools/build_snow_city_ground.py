"""Extend only snow/city terrain approach, preserving the forest/snow helper ABI."""
from pathlib import Path
import subprocess,json,hashlib,re
R=Path(__file__).resolve().parents[1]
asm='''org 03b48h
 ld a,(57935)
 sub 23
 and 247
 jr z,approach
 dec a
 jr z,arrival
fallback:
 ld a,(57935)
 jp 14749
approach:
 ld hl,(57927)
 ld de,13828
 or a
 sbc hl,de
 jr c,fallback
 ld de,-1020
 add hl,de
 jr store
arrival:
 ld hl,(57927)
 ld a,h
 cp 10
 jr nc,fallback
 ld de,1536
 add hl,de
store:
 ld (60645),hl
 call 03bech
 ld (60647),hl
 ld a,1
 ld (60644),a
 ret
offset:
 ld hl,(60645)
 add hl,bc
 ld a,(57935)
 sub 23
 and 247
 cp 2
 ret nc
 sra h
 rr l
 sra h
 rr l
 ret
'''
pointer='''org 03bech
 ld a,(57935)
 cp 25
 ld hl,14868
 ret c
 ld hl,14877
 ret
'''
def at(a):return 214*16384+8192+a-0x2400
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-snow-city-feather'+suffix);out=R/('outputs/six-route-snow-city-ground'+suffix);out.mkdir(exist_ok=True)
 for name,source in [('ground',asm),('pointer',pointer)]:
  (out/(name+'.asm')).write_text(source)
  subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/(name+'.asm')),str(out/(name+'.bin')),str(out/(name+'.sym'))],check=True)
 code=(out/'ground.bin').read_bytes();ptr=(out/'pointer.bin').read_bytes()
 previous=(R/'outputs/six-route-snow-connected/ramp.bin').read_bytes()
 assert len(code)<=len(previous)==86 and len(ptr)<=20
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 assert old[at(0x3b48):at(0x3b48)+86]==previous
 assert old[at(0x3bec):at(0x3bec)+20]==b'\xff'*20
 assert old[at(14877):at(14877)+9]==bytes([63,64,72,73,90,91,116,47,43])
 offset=int(re.search(r'offset\s+EQU\s+0([0-9A-F]+)H',(out/'ground.sym').read_text()).group(1),16)
 hook=old.find(bytes.fromhex('cd873b00'),at(14895),at(14979));assert hook>=0
 rom[hook:hook+3]=b'\xcd'+offset.to_bytes(2,'little')
 rom[at(0x3b48):at(0x3b48)+86]=code+bytes(86-len(code))
 rom[at(0x3bec):at(0x3bec)+len(ptr)]=ptr
 allowed=((hook,hook+3),(at(0x3b48),at(0x3b48)+86),(at(0x3bec),at(0x3bec)+len(ptr)))
 assert all(any(a<=i<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,rom)) if x!=y)
 assert len(rom)==4194304
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_bytes((src/'geometry-layout.json').read_bytes())
 report=dict(bytes=len(rom),helper_bytes=len(code),pointer_bytes=len(ptr),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,scope='Snow/city world-space ground ramp only; native validation pending')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
