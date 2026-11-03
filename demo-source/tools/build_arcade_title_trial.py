from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];labels=json.loads((R/'assets/title-copy.json').read_text(encoding='utf-8-sig'))
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-arcade-cache'+suffix);O=R/('outputs/six-route-arcade-title'+suffix);O.mkdir(exist_ok=True)
 old=(src/name).read_bytes();rom=bytearray(old);allowed=set()
 first=old.index(b'PUBLIC ROAD / COCKPIT\0');second=old.index(b'< COAST DRIVE >\0');third=old.index(b'5 CARS / OPEN COAST\0')
 assert second==first+22 and third==second+16
 data=labels['title'].encode()+b'\0'+labels['mode'].encode()+b'\0';assert len(data)<=38
 rom[first:first+38]=data.ljust(38,b'\0');allowed.update(range(first,first+38))
 cpu=lambda pos:0x8000+(pos//16384-1)*8192+(pos%16384-8192)
 pattern=b'\x21'+cpu(second).to_bytes(2,'little')+bytes.fromhex('e5114100')
 at=old.index(pattern);assert old.count(pattern)==1
 rom[at+1:at+3]=cpu(first+len(labels['title'])+1).to_bytes(2,'little');allowed.update([at+1,at+2])
 desc=labels['description'].encode()+b'\0';assert len(desc)<=20
 rom[third:third+20]=desc.ljust(20,b'\0');allowed.update(range(third,third+20))
 assert len(rom)==4194304
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),labels=labels,scope='Title/menu strings and one relocated string pointer only; native visual validation pending'),indent=2))
 print(O)
