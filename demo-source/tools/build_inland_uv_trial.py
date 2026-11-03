from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suf,n in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-forest-mix'+suf);out=R/('outputs/six-route-inland-uv'+suf);out.mkdir(exist_ok=True);base=R/('outputs/six-route-forest-shade'+suf)
 asm=(base/'helper.asm').read_text();needle='original_uv:\n';assert asm.count(needle)==1
 asm=asm.replace(needle,needle+f" ld a,({S['_route_piece']})\n cp 8\n ret nc\n")
 (out/'helper.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'helper.asm'),str(out/'helper.bin')],check=True)
 old=(base/'helper.bin').read_bytes();code=(out/'helper.bin').read_bytes();assert len(code)<=8192;rom=bytearray((src/n).read_bytes());at=188*16384+8192;assert rom[at:at+len(old)]==old
 rom[at:at+8192]=code+bytes([255])*(8192-len(code));(out/n).write_bytes(rom)
 for a in ['city-atlas.bin','night-atlas.bin']:(out/a).write_bytes((src/a).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),runtime_verified=False),indent=2))
