from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];w=R/'work/early-seam-decode';w.mkdir(exist_ok=True)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(R/'src/early_seam_decode.asm'),str(w/'decode.bin'),str(w/'decode.sym')],check=True)
code=(w/'decode.bin').read_bytes();assert len(code)<256
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-early-seam-data'+suffix);p=next(src.glob('*.rom'));b=bytearray(p.read_bytes());at=211*16384+8192+0x1000;assert b[at:at+len(code)]==b'\xff'*len(code);b[at:at+len(code)]=code
 out=R/('outputs/six-route-early-seam-decode'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(b)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'helper_bytes':len(code),'entry':28672,'scope':'Decoder only, no rendering hook installed'},indent=2));print(suffix,len(code))
