"""Build an unused, isolated ROM helper for the approved temporary third lane."""
from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-road-uv-preserved'+suffix);O=R/('outputs/six-route-passing-profile'+suffix);O.mkdir(exist_ok=True)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(R/'src/passing_layout.asm'),str(O/'passing-layout.bin')],check=True)
 code=(O/'passing-layout.bin').read_bytes();assert len(code)<=8192
 rompath=next(src.glob('*.rom'));rom=bytearray(rompath.read_bytes());at=208*16384+8192
 assert rom[at:at+8192]==bytes([255])*8192,'Reserved half-bank no longer free'
 rom[at:at+len(code)]=code
 assert len(rom)==4194304
 (O/rompath.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps({'bytes':len(rom),'helper_bytes':len(code),'bank':208,'sha256':hashlib.sha256(rom).hexdigest(),'integrated_into_game':False,'scope':'Unused helper only. Road geometry, AI, clocks and assets unchanged. Native test maps the helper explicitly.'},indent=2))
 print(O.name,len(code))
