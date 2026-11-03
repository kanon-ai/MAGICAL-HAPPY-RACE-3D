from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
 d=R/('outputs/radio-menu'+suffix);src=next(d.glob('*.rom'));old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((d/'manifest.json').read_text())['sha256']
 at=251*16384+8192;block=old[at:at+1024];n=block[0];assert n==50
 faces=[block[1+i*11:1+(i+1)*11] for i in range(n)];uv=[block[1+n*11+i*8:1+n*11+(i+1)*8] for i in range(n)]
 rear=[i for i,f in enumerate(faces) if set(f[:4]) in ({0,1,4,5},{1,2,3,4})];assert rear==[34,35,36,37]
 order=[i for i in range(n) if i not in rear]+rear
 data=bytes([n])+b''.join(faces[i] for i in order)+b''.join(uv[i] for i in order)+block[1+n*19:]
 assert len(data)==1024;rom=bytearray(old);rom[at:at+1024]=data
 assert rom[:at]==old[:at] and rom[at+1024:]==old[at+1024:]
 out=R/('outputs/truck-wheel-order'+suffix);out.mkdir(exist_ok=True);(out/src.name).write_bytes(rom)
 (out/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),changed_bytes=sum(a!=b for a,b in zip(old,rom)),scope='Truck rear-face painter order only. All face geometry, UVs, materials, near packet, models and runtime unchanged.'),indent=2))
s=(R/'tools/verify_radio_menu.py').read_text().replace('outputs/radio-check','outputs/truck-wheel-check').replace('outputs/radio-menu','outputs/truck-wheel-order');(R/'tools/verify_truck_wheel_order.py').write_text(s)
