"""Cover sea below the incoming canyon panorama before road drawing."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-ground';O.mkdir(exist_ok=True)
source=R/'outputs/six-route-vegetation/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
rom=bytearray(source.read_bytes());S=json.loads((R/'outputs/symbols.json').read_text())
asm=f'''org 0fd80h
 ; Original draw_sea epilogue: restore its local stack and IX first.
 pop af
 pop ix
 ld a,({S['_route_piece']})
 sub 7
 cp 2
 ret nc
 ld hl,({S['_scene_pan']})
 ld a,h
 or a
 ret nz
 ld a,l
 or a
 ret z
 call {S['_page_y']}
 ld a,({S['_camera_mode']})
 or a
 ld a,78
 jr z,top_ready
 ld a,130
top_ready:
 ld c,a
 ld b,0
 ex de,hl
 add hl,bc
 ex de,hl
 ld a,({S['_view_bottom']})
 sub c
 ld l,a
 ld h,0
 ld a,75
 push af
 inc sp
 push hl
 ld hl,({S['_scene_pan']})
 push hl
 ld a,l
 neg
 ld l,a
 ld h,0
 call {S['_gfx_fill']}
 ret
'''
(O/'ground.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'ground.asm'),str(O/'ground.bin')],check=True)
code=(O/'ground.bin').read_bytes();assert len(code)<=128
at=255*16384+8192+1344;assert rom[at:at+128]==b'\xff'*128
rom[at:at+len(code)]=code
# VIEW image offset DFC is draw_sea's shared epilogue.
at=214*16384+8192+0xdfc;assert rom[at:at+4]==bytes.fromhex('f1 dd e1 c9')
rom[at:at+4]=bytes.fromhex('c3 80 fd 00')
target=O/source.name;target.write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),scope='Coast-canyon incoming panorama strip receives canyon ground before road drawing. Other scenes untouched; visual/FPS verification pending.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
