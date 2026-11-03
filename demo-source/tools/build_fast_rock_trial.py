"""Replace only projected rock roof deformation with bounded R800 assembly."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-fast-rock';O.mkdir(exist_ok=True)
name='MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom';source=R/'outputs/six-route-canyon-scenery'/name
original=source.read_bytes();assert hashlib.sha256(original).hexdigest()=='3ba7be84fa5ac53f0a22bfbde62c17c7777231a5ed50affffa02d3f836ebfe35'
rom=bytearray(original);start=0xda25;end=0xdb69;at=3*16384+8192+start-0xc000
assert rom[at:at+4]==bytes.fromhex('7b d5 5f 16')
asm="""org 0da25h
 ; Preserve caller slot E, keep-mask C and SDCC frame IX.
 push bc
 push de
 push ix
 push iy
 ld a,e
 ld c,60
 db 0edh,0c9h
 inc h
 push hl
 pop iy
 ld c,2
vertex:
 ; IY=mesh, IX=the next roof vertex. C visits 2,3,6,7 only.
 ld a,c
 add a,a
 add a,a
 add a,c
 ld e,a
 ld d,0
 push iy
 pop hl
 add hl,de
 push hl
 pop ix
 ld e,(ix+4)
 ld d,0
 ld a,b
 cp 6
 jr nz,double_height
 ld l,e
 ld h,0
 srl l
 add hl,de
 jr height_ready
double_height:
 ex de,hl
 add hl,hl
height_ready:
 bit 2,c
 jr z,height_final
 ld d,h
 ld e,l
 srl h
 rr l
 srl h
 rr l
 ex de,hl
 or a
 sbc hl,de
height_final:
 ex de,hl
 ; Ground vertex is (j XOR 3); subtract the full 16-bit height.
 ld a,c
 xor 3
 ld l,a
 add a,a
 add a,a
 add a,l
 add a,2
 ld l,a
 ld h,0
 push de
 push iy
 pop de
 add hl,de
 pop de
 ld a,(hl)
 inc hl
 ld h,(hl)
 ld l,a
 or a
 sbc hl,de
 ld (ix+2),l
 ld (ix+3),h
 ; Inset left/right roof corners by exactly floor(width/4).
 ld a,(ix+4)
 srl a
 srl a
 ld e,a
 ld d,0
 bit 0,c
 jr nz,positive_inset
 xor a
 sub e
 ld e,a
 sbc a,a
 ld d,a
positive_inset:
 ld l,(ix+0)
 ld h,(ix+1)
 add hl,de
 ld (ix+0),l
 ld (ix+1),h
 inc c
 ld a,c
 cp 4
 jr nz,next_vertex
 ld c,6
next_vertex:
 ld a,c
 cp 8
 jp c,vertex
 pop iy
 pop ix
 pop de
 pop bc
 jp 0db69h
"""
(O/'fast-rock.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'fast-rock.asm'),str(O/'fast-rock.bin'),str(O/'fast-rock.sym')],check=True)
code=(O/'fast-rock.bin').read_bytes();assert len(code)<=end-start
rom[at:at+end-start]=code+b'\xff'*(end-start-len(code))
assert len(rom)==len(original)==4194304
assert rom[:at]==original[:at] and rom[at+end-start:]==original[at+end-start:]
(O/name).write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),replacement_bytes=len(code),reclaimed_code_bytes=end-start-len(code),scope='Rock roof deformation only. Native equivalence and performance validation pending.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
