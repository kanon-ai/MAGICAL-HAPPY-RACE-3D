"""Four-byte R800 multiplication replacement; all packed data untouched."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
for port in ('internal','external'):
 proof=json.loads((R/f'outputs/bitpacked-mul-native/{port}/validation.json').read_text())
 assert proof['all_samples_exact'] and proof['preserved_registers_and_stack_exact'] and proof['samples']==6912
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-bitpacked-columns'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 needle=bytes.fromhex('af8110fd');at=old.find(needle,0x2600,0x2700)
 assert at>=0 and old.find(needle,at+1,0x2700)<0
 rom[at:at+4]=bytes.fromhex('78edc97d')
 assert all(x==y or at<=i<at+4 for i,(x,y) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-bitpacked-mul'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_bytes((src/'geometry-layout.json').read_bytes())
 report={'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'offset':at,'changed_bytes':4,'scope':'Packed reader multiplication only; geometry bytes unchanged, native unit passed; rendering/performance pending'}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(suffix,report)
