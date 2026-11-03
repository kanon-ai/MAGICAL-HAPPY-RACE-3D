"""After broad inland terrain exists, fill only above its first road cross-section."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for external in (False,True):
 suffix='-external-88h' if external else '';name='MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom' if external else 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
 source=R/f'outputs/six-route-inland-ground{suffix}'/name;original=source.read_bytes();rom=bytearray(original)
 expected='06bd43dd2a4cd527e3dbbfd87972eb06d01c3b65cfa6a95a0fe11fbf00f43133' if external else '08b45f7755a075b88e59c1d757817fde0ac40112f10900cc34860d808c574c11'
 assert hashlib.sha256(original).hexdigest()==expected
 O=R/f'outputs/six-route-ground-crop{suffix}';O.mkdir(exist_ok=True)
 asm=f"""org 0db2bh
 ld a,({S['_route_piece']})
 cp 9
 jr nc,inland
full_height:
 ld a,({S['_view_bottom']})
 ret
inland:
 ; No road band exists when only the bottom cross-section was emitted.
 ld a,({S['_view_bottom']})
 ld hl,{S['_sea_crest']-74}
 cp (hl)
 jr z,full_height
 jr c,full_height
 ld a,({S['_sea_crest']})
 cp 64
 jr c,full_height
 cp (ix-2)
 jr nc,overlap
 ld a,(ix-2)
overlap:
 ; One pixel overlap avoids a zero-height VDP command and raster edge gaps.
 inc a
 ret
"""
 (O/'crop.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'crop.asm'),str(O/'crop.bin')],check=True)
 code=(O/'crop.bin').read_bytes();assert len(code)<=62
 at=3*16384+8192+0x1b2b;assert rom[at:at+62]==bytes([255])*62
 rom[at:at+len(code)]=code
 patch=214*16384+8192+0xc7e;assert rom[patch:patch+3]==bytes([0x3a])+S['_view_bottom'].to_bytes(2,'little')
 rom[patch:patch+3]=bytes.fromhex('cd 2b db')
 assert all(i in range(at,at+len(code)) or i in range(patch,patch+3) for i,(a,b) in enumerate(zip(rom,original)) if a!=b)
 (O/name).write_bytes(rom)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=expected,helper_bytes=len(code),scope='Redundant inland background fill crop only; native pixel equivalence pending.')
 (O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
