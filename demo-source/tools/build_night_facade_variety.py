"""Night facade variety using existing tiles, fixed to world piece identity."""
from pathlib import Path
import ast,subprocess,hashlib,json
R=Path(__file__).resolve().parents[1]
node=next(n for n in ast.parse((R/'tools/build_city_facade_variety_v2.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='asm' for t in n.targets));original=ast.literal_eval(node.value)
asm=original.replace(' cp 2\n jr z,balcony','variation:\n cp 2\n jr z,balcony').replace('night:\n cp 3\n ld c,1\n ret z\noriginal_building:', 'night:\n cp 3\n ld c,1\n ret z\n cp 1\n ld c,0\n ret z\n jr variation\noriginal_building:')
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
oldcode=(R/'outputs/six-route-city-facade-variety-v2/facades.bin').read_bytes()
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-forest-roadside-depth'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 out=R/('outputs/six-route-night-facade-variety'+suffix);assert not out.exists();out.mkdir()
 (out/'facades.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'facades.asm'),str(out/'facades.bin')],check=True)
 code=(out/'facades.bin').read_bytes();assert len(code)<=92
 at=off(0x9650);assert old[at:at+len(oldcode)]==oldcode and old[at+len(oldcode):at+92]==bytes(92-len(oldcode))
 rom[at:at+len(code)]=code;assert len(rom)==4194304 and rom[:at]==old[:at] and rom[at+92:]==old[at+92:]
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'bytes':len(rom),'helper_bytes':len(code),'changed_bytes':sum(a!=b for a,b in zip(old,rom)),'sha256':hashlib.sha256(rom).hexdigest(),'scope':'Only night kind0/2 facade selection; existing atlas and geometry unchanged. Native/visual/performance validation pending.','adopted':False}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
