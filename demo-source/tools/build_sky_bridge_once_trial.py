"""Remove the split top-sky fill which the bridge immediately overwrites."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-sky-bridge-cache'+suffix);o=R/('outputs/six-route-sky-bridge-once'+suffix);o.mkdir(exist_ok=True)
 original=(src/name).read_bytes();assert hashlib.sha256(original).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 b=bytearray(original);at=16384+8192+0xb73;assert b[at:at+3]==b'\xcd'+S['_draw_night_sky_top'].to_bytes(2,'little');b[at:at+3]=bytes(3);(o/name).write_bytes(b)
 for asset in ['city-atlas.bin','night-atlas.bin']:(o/asset).write_bytes((src/asset).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),scope='Remove overwritten old split-top fill only; same feather/fade. Native equivalence stored separately.',free_bytes=303104),indent=2))
