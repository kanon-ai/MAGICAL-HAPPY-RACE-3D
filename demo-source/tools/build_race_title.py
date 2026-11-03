from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];needle=b'MAGICAL HAPPY RALLY 3D\0';new=b'MAGICAL HAPPY RACE 3D\0';O=R/'outputs/race-title-review';O.mkdir(exist_ok=True)
for suffix,label in (('','INTERNAL_98H'),('-external-88h','EXTERNAL_88H')):
 src=R/('outputs/front-contact-zero'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256'];assert old.count(needle)==1
 at=old.index(needle);rom=bytearray(old);rom[at:at+len(needle)]=new.ljust(len(needle),b'\0');assert rom[:at]==old[:at] and rom[at+len(needle):]==old[at+len(needle):]
 d=R/('outputs/race-title'+suffix);d.mkdir(exist_ok=True);name='MAGICAL_HAPPY_RACE_3D_'+label+'.rom';(d/name).write_bytes(rom)
 (d/'manifest.json').write_text(json.dumps(dict(title='MAGICAL HAPPY RACE 3D',source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),title_offset=at,scope='Title text and distribution filenames only; accepted collision/gameplay/art/audio unchanged.'),indent=2))
s=(R/'tools/verify_radio_menu.py').read_text(encoding='utf-8-sig').replace('outputs/radio-check','outputs/race-title-check').replace('outputs/radio-menu','outputs/race-title');(R/'tools/verify_race_title.py').write_text(s,encoding='utf-8')
