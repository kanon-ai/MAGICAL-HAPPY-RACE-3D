"""Add a third-lane divider to the widening rear-view road."""
from pathlib import Path
import ast,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
tree=ast.parse((R/'tools/build_passing_mirror_width.py').read_text())
asm=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='asm' for t in n.targets))
asm=asm.replace(' call 06000h\n ld c,a',' call 06000h\n ld (0f6fah),a\n ld c,a')
asm=asm.replace(' pop iy\n pop de\n add hl,de\n pop de\n pop bc\n jp 08d35h',''' pop iy
 pop hl
 pop de
 pop bc
 call divider_vertices
 push de
 ld de,(0f6f8h)
 add hl,de
 pop de
 jp 08d35h''')
asm+='''
divider_vertices:
 push bc
 push de
 push hl
 ld a,040h
 out (INDEX),a
 ld a,c
 add a,a
 add a,24
 out (DATA),a
 ld a,050h
 out (INDEX),a
 ld a,(0f6fah)
 cp 16
 jr c,hidden
 dec hl
hidden:
 push bc
 push de
 call 08d35h
 pop de
 pop bc
 pop hl
 push hl
 push bc
 push de
 call 08d35h
 pop de
 pop bc
 ld a,040h
 out (INDEX),a
 ld a,c
 add a,a
 add a,c
 add a,a
 add a,4
 out (DATA),a
 ld a,050h
 out (INDEX),a
 pop hl
 pop de
 pop bc
 ret
init_faces:
 call 0aa07h
 ld hl,divider_faces
 ld bc,02100h+DATA
 otir
 ret
divider_faces:
 db 24,25,27,26,0,0,0,0,0,0,15
 db 26,27,29,28,0,0,0,0,0,0,15
 db 28,29,31,30,0,0,0,0,0,0,15
'''
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-markers'+suffix);out=R/('outputs/six-route-passing-mirror-lines-v2'+suffix);out.mkdir(exist_ok=True)
 index=0x8d if suffix else 0x9d
 text=f'INDEX equ {index}\nDATA equ {index+2}\n'+asm
 (out/'mirror-lines.asm').write_text(text)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'mirror-lines.asm'),str(out/'mirror-lines.bin'),str(out/'mirror-lines.sym')],check=True)
 symbols={x.split()[0]:int(x.split()[2].rstrip('H'),16) for x in (out/'mirror-lines.sym').read_text().splitlines()}
 code=(out/'mirror-lines.bin').read_bytes();assert len(code)<0x321
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 assert old[off(0xb02c):off(0xb02c)+3]==bytes.fromhex('c335a9')
 for a,expected,label in ((0xac14,'cd358d','first_edge'),(0xac1c,'cd358d','second_edge'),(0xaa24,'cd07aa','init_faces')):
  at=off(a);assert old[at:at+3]==bytes.fromhex(expected)
  rom[at:at+3]=b'\xcd'+symbols[label].to_bytes(2,'little')
 for a,expected,new in ((0xac2c,24,32),(0xac3c,12,15)):
  at=off(a);assert old[at]==expected;rom[at]=new
 rom[off(0xb030):off(0xb030)+len(code)]=code
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),symbols=symbols,playable_adoption=False),indent=2));print(out.name,len(code))
