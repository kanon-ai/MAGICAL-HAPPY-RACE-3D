"""Clear only layout-declared retired/free slots in an isolated ROM trial."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
layout=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())
reserved={188,189,190,191,196,197,198,199}
free=[(b,o) for b,o in layout['free_slots'] if b not in reserved]
assert len(free)==37
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-integrated'+suffix);O=R/('outputs/six-route-clean-free'+suffix);O.mkdir(exist_ok=True)
 before=(src/name).read_bytes();rom=bytearray(before);changed=[]
 for bank,offset in free:
  at=bank*16384+offset
  if rom[at:at+8192]!=b'\xff'*8192:changed.append([bank,offset])
  rom[at:at+8192]=b'\xff'*8192
 assert len(rom)==4194304
 (O/name).write_bytes(rom)
 for a in ('city-atlas.bin','night-atlas.bin'):(O/a).write_bytes((src/a).read_bytes())
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(before).hexdigest(),free_bytes=len(free)*8192,free_slots=free,retired_non_ff_slots_cleared=changed,scope='Only layout-declared free slots cleared; runtime validation pending.')
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(len(changed),'retired slots cleared',O)
