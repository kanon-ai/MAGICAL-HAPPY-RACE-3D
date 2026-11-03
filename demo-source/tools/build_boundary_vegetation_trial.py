"""Keep shared broadleaf/shrub sprites across the coast-canyon atlas boundary."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-vegetation';O.mkdir(exist_ok=True)
source=R/'outputs/six-route-trial-joined/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
rom=bytearray(source.read_bytes());S=json.loads((R/'outputs/symbols.json').read_text())
# Equivalent scoped rule change:
# if ((p[5]&7)==5 || (p[5]&7)==7) continue;
# These shared vegetation sprites do not need the architectural atlas masks.
needle=b'\x3a'+S['_route_piece'].to_bytes(2,'little')+bytes.fromhex('d6 08 38 07 3a')+S['_route_piece'].to_bytes(2,'little')+bytes.fromhex('d6 0e 38 18')
assert len(needle)==14 and rom.count(needle)==1
at=rom.index(needle)
rom[at:at+2]=bytes.fromhex('18 0c')
assert all(a==b for i,(a,b) in enumerate(zip(source.read_bytes(),rom)) if i not in (at,at+1))
target=O/source.name;target.write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),patch_offset=at,changed_bytes=2,scope='Broadleaf/shrub bypass architecture masks in canyon too; other objects/rules unchanged. Visual verification required.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
