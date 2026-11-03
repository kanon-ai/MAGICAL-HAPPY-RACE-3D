from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
s=(R/'tools/build_building_vertices_trial.py').read_text();asm=s.split('asm=f"""',1)[1].split('"""',1)[0];asm=eval('f'+repr(asm))
old='''shifted_width:
 srl a
 push bc
 push de
 call '''+str(S['_camera_shift'])+'''
 ex de,hl
 pop de
 pop bc
'''
new='''shifted_width:
 bit 0,(ix-2)
 jr nz,cached_shift
 srl a
 push bc
 push de
 call '''+str(S['_camera_shift'])+'''
 ex de,hl
 pop de
 pop bc
 ld (ix-6),l
 ld (ix-7),h
 jr shift_ready
cached_shift:
 ld l,(ix-6)
 ld h,(ix-7)
shift_ready:
'''
assert old in asm;asm=asm.replace(old,new)
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-city-silhouettes'+suffix);p=next(src.glob('*.rom'));original=p.read_bytes();rom=bytearray(original)
 out=R/('outputs/six-route-building-pair-cache'+suffix);out.mkdir(exist_ok=True)
 (out/'kernel.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'kernel.asm'),str(out/'kernel.bin')],check=True)
 code=(out/'kernel.bin').read_bytes();assert len(code)<=142,len(code)
 at=16384+8192+0x1975;prior=(R/'outputs/six-route-building-vertices/vertices.bin').read_bytes();assert original[at:at+len(prior)]==prior
 assert original[at+len(prior):at+142]==bytes(142-len(prior))
 rom[at:at+142]=code+bytes(142-len(code));assert len(rom)==4194304
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'bytes':len(rom),'kernel_bytes':len(code),'sha256':hashlib.sha256(rom).hexdigest(),'scope':'Pairwise camera shift reuse only; native validation pending','adopted':False}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
