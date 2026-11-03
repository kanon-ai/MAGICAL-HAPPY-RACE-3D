"""Exact byte-ramp evaluation with the already-required R800 MULUB."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
old=bytes.fromhex('46236e260029292929297cf620677db16f7e80c9')
new=bytes.fromhex('46237eedc97d80c9')
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-traffic-overtake'+suffix);O=R/('outputs/six-route-decoder-multiply'+suffix);O.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom);at=8192+0x180
 assert rom[at:at+len(old)]==old
 rom[at:at+len(old)]=new+bytes(len(old)-len(new))
 assert len(rom)==4194304 and all(at<=i<at+len(old) for i,(a,b) in enumerate(zip(before,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),address='F180',old_bytes=old.hex(),new_bytes=new.hex(),scope='General ramp sample only: (base + delta*index) modulo256. Other sample types, decoder layout, product table and game rules unchanged. Runtime verification pending.'),indent=2))
 print(O)
