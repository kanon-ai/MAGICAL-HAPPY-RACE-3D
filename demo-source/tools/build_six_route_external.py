"""Apply audited baseline I/O-only variant differences to the isolated trial."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
internal=(R/'outputs/MAGICAL_HAPPY_RALLY_3D.rom').read_bytes()
external=(R/'outputs/external-88h/MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H.rom').read_bytes()
assert hashlib.sha256(internal).hexdigest()=='506fa0b7106a5e9ea681f9da5045e878b4a02f31d64df1f1be3f4534826dd670'
assert hashlib.sha256(external).hexdigest()=='19b17a1097b521d9f49499d0e20147d3e1f74e68d1ce1af0aef7490d26ff4391'
source=R/'outputs/six-route-mirror-dedup/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
expressive='--expressive' in sys.argv
if expressive:source=R/'outputs/six-route-expressive/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
lined='--lined' in sys.argv
if lined:source=R/'outputs/six-route-lined/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
if '--canyon-scenery' in sys.argv:source=R/'outputs/six-route-canyon-scenery/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
if '--fast-rock' in sys.argv:source=R/'outputs/six-route-fast-rock/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
rom=bytearray(source.read_bytes());diff=[i for i,(a,b) in enumerate(zip(internal,external)) if a!=b]
assert len(diff)==321
for at in diff:
 assert rom[at]==internal[at],('Variant conflict',at)
 rom[at]=external[at]
O=R/'outputs/six-route-external-88h';O.mkdir(exist_ok=True)
if expressive:O=R/'outputs/six-route-expressive-external-88h';O.mkdir(exist_ok=True)
if lined:O=R/'outputs/six-route-lined-external-88h';O.mkdir(exist_ok=True)
if '--canyon-scenery' in sys.argv:O=R/'outputs/six-route-canyon-scenery-external-88h';O.mkdir(exist_ok=True)

if '--fast-rock' in sys.argv:O=R/'outputs/six-route-fast-rock-external-88h';O.mkdir(exist_ok=True)

target=O/'MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom';target.write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),internal_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),io_only_changed_bytes=len(diff),runtime_verified=False,scope='External88h trial only; emulator and physical hardware verification pending.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
