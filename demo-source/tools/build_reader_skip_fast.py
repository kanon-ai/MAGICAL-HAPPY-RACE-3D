"""Exact-output trial: compare token length-minus-one, simplify skip subtraction."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];w=R/'work/reader-skip-fast';w.mkdir(exist_ok=True)
oldreader=(R/'work/bitpacked-nibble-reader/reader.bin').read_bytes()
legacy=(R/'outputs/six-route-trial-lined-dedup/decoder.asm').read_text().split('compressed_sample:\n',1)[1].split('saved_page:',1)[0]
assert legacy.count(' and 63\n inc a\n cp c\n jr z,skip\n jr c,skip')==1
legacy=legacy.replace(' and 63\n inc a\n cp c\n jr z,skip\n jr c,skip',' and 63\n cp c\n jr c,skip').replace('skip:\n neg','skip:\n cpl')
nibble=(R/'work/bitpacked-nibble-reader/reader.asm').read_text().split('bitpacked_sample:\n',1)[1]
asm='org 01f00h\n bit 7,(hl)\n jp nz,bitpacked_sample\n'+legacy+'bitpacked_sample:\n'+nibble
(w/'reader.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'reader.asm'),str(w/'reader.bin'),str(w/'reader.sym')],check=True)
new=(w/'reader.bin').read_bytes();assert len(new)<=len(oldreader)
new+=bytes(len(oldreader)-len(new))
for suffix,sha in [('', '9faf12daa2de2ceaf6f0f98e84b548abe470aa0139e73e001cc07fd52e8457a4'),('-external-88h','ebed012879d13cf08c9a82e087e7c358dab77fbec5b4d595124bb8dd5a85ddea')]:
 src=R/('outputs/six-route-city-tunnel-exit-trim-early-tree'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();assert hashlib.sha256(old).hexdigest()==sha
 assert old[0x2600:0x2600+len(new)]==oldreader
 rom=old[:0x2600]+new+old[0x2600+len(new):];assert len(rom)==4194304
 out=R/('outputs/six-route-reader-skip-fast'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps({'source_sha256':sha,'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'changed_region':[0x2600,0x2600+len(new)],'runtime_verified':False},indent=2))
print('Both trial ROMs built; native validation pending')
