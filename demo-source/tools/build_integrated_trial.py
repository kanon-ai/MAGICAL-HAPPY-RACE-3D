"""Integrate independently verified, non-overlapping visual changes."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-sky-bridge-top'+suffix);vertex=R/('outputs/six-route-building-vertices'+suffix);base=R/('outputs/six-route-city-walk-continuity'+suffix);O=R/('outputs/six-route-integrated'+suffix);O.mkdir(exist_ok=True)
 original=(src/name).read_bytes();b=bytearray(original);assert hashlib.sha256(original).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 start=16384+8192+0x1975;end=16384+8192+0x1a03
 assert b[start:end]==(base/name).read_bytes()[start:end]
 patch=(vertex/name).read_bytes()[start:end];assert patch[:6]==bytes.fromhex('dd36fe00c1c5');b[start:end]=patch
 assert len(b)==4194304
 (O/name).write_bytes(b)
 for a in ['city-atlas.bin','night-atlas.bin']:(O/a).write_bytes((src/a).read_bytes())
 report=dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),vertex_source_sha256=hashlib.sha256((vertex/name).read_bytes()).hexdigest(),bytes=len(b),free_bytes=303104,scope='City sidewalks, world-selected trees, cached feather/night fade, redundant sky fills removed, compact building vertices. Full-route verification pending.')
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
