"""Allow every ordinary car to use the existing overtaking speed branch."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-mirror-sprite'+suffix);O=R/('outputs/six-route-traffic-overtake'+suffix);O.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());old=bytes(rom)
 address=0xa26b;at=(1+(address-0x8000)//8192)*16384+8192+(address-0x8000)%8192
 assert rom[at:at+2]==bytes.fromhex('2824')
 # Remove the i==1-only skip. The original signed lane>-20 condition,
 # passing speed18, and subsequent NPC/player following brakes remain.
 rom[at:at+2]=b'\0\0'
 assert len(rom)==4194304 and all(at<=i<at+2 for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),changed_cpu_address=hex(address),changed_bytes=2,scope='All five traffic cars use existing passing speed18 while lane>-20; original following brakes, lane clearance, central gap, clocks and rear-contact rules preserved.'),indent=2))
 print(O)
