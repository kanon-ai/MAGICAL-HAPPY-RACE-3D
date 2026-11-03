from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-night-boulevard'+suffix);out=R/('outputs/six-route-aligned-sky'+suffix);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 asm=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.asm').read_text()
 start=asm.index(" ; Replace the top's")
 end=asm.index('band:\n',start)
 asm=asm[:start]+f''' ; Follow the panorama seam: old sky on left, incoming sky on right.
 ld a,({S['_camera_mode']})
 or a
 jr z,band
 ld a,158
 push af
 inc sp
 ld hl,52
 push hl
 ld hl,256
 push hl
 ld de,(0f6d2h)
 ld e,0
 ld hl,0
 call {S['_gfx_fill']}
 ld hl,(0f6d4h)
 ld a,h
 or l
 jr z,band
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
