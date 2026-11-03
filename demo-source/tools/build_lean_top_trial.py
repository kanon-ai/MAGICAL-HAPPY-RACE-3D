from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-night-boulevard'+suffix);out=R/('outputs/six-route-lean-top'+suffix);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 asm=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.asm').read_text()
 start=asm.index(" ; Replace the top's")
 end=asm.index('band:\n',start)
 asm=asm[:start]+f''' ; Follow the panorama seam: old sky on left, incoming sky on right.
 ld a,({S['_camera_mode']})
 or a
 jp z,band
 ld hl,256
 ld de,(0f6d4h)
 or a
 sbc hl,de
 ld a,h
 or l
 jr z,day_done
 ex de,hl
 ld a,158
 push af
 inc sp
 ld hl,52
 push hl
 push de
 ld de,(0f6d2h)
 ld e,0
 ld hl,0
 call {S['_gfx_fill']}
day_done:
 ld hl,(0f6d4h)
 ld a,h
 or l
 jp z,band
 ld a,12
 push af
 inc sp
 ld hl,52
 push hl
 ld hl,(0f6d4h)
 push hl
 ex de,hl
 ld hl,256
 or a
 sbc hl,de
 ld de,(0f6d2h)
 ld e,0
 call {S['_gfx_fill']}
 ; Eight four-pixel strips match the existing 32-pixel panorama feather.
 ld hl,240
 ld de,(0f6d4h)
 or a
 sbc hl,de
 ld b,8
 ld c,2
upper_loop:
 push bc
 push hl
 ld a,h
 or a
 jr z,upper_positive
 inc a
 jr nz,upper_done
 ld a,l
 add a,4
 jr nc,upper_done
 ld e,a
 ld hl,0
 jr upper_draw
upper_positive:
 ld e,4
 ld a,l
 cp 253
 jr c,upper_draw
 neg
 ld e,a
upper_draw:
 ld d,0
 push hl
 push de
 ld l,c
 ld h,0
 ld de,colors
 add hl,de
 ld a,(hl)
 pop de
 pop hl
 push hl
 push de
 push af
 inc sp
 ld hl,52
 push hl
 push de
 ; gfx_fill takes X in HL, Y in DE, width/height/color on stack.
 ld hl,7
 add hl,sp
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld de,(0f6d2h)
 ld e,0
 call {S['_gfx_fill']}
 pop de
 pop hl
upper_done:
 pop hl
 pop bc
 ld de,4
 add hl,de
 ld a,c
 add a,4
 ld c,a
 djnz upper_loop
'''+asm[end:]
 (out/'bridge.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'bridge.asm'),str(out/'bridge.bin')],check=True)
 code=(out/'bridge.bin').read_bytes();assert len(code)<=512
 oldcode=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.bin').read_bytes()
 for bank in [191,196,197,198,199]:
  at=bank*16384+8192
  assert rom[at:at+len(oldcode)]==oldcode
  rom[at:at+512]=code+bytes([255])*(512-len(code))
 (out/name).write_bytes(rom)
 for asset in ['city-atlas.bin','night-atlas.bin']:(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),bytes=len(rom),runtime_verified=False),indent=2))
 print(suffix,len(code))
