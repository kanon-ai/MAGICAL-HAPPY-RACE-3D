"""Merge verified four-arch LOD into passing-lane candidate, guarded bytewise."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
 def rom(name):return next((R/('outputs/'+name+suffix)).glob('*.rom'))
 old=rom('six-route-drive-structures-carfix2').read_bytes();donor=rom('six-route-arch-series-lod').read_bytes();src=rom('six-route-passing-gap-history');current=src.read_bytes();merged=bytearray(current)
 changes=[i for i,(a,b) in enumerate(zip(old,donor)) if a!=b]
 assert len(changes)==2449
 assert all(i//16384==210 or i in (43343,43344) for i in changes)
 assert current[210*16384:211*16384]==old[210*16384:211*16384]
 for i in changes:assert current[i]==old[i],i;merged[i]=donor[i]
 assert len(merged)==4194304
 out=R/('outputs/six-route-passing-four-arches'+suffix);out.mkdir(exist_ok=True);(out/src.name).write_bytes(merged)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src.parent/name).read_bytes())
 report=dict(bytes=len(merged),sha256=hashlib.sha256(merged).hexdigest(),changed_bytes=len(changes),playable_adoption=False,runtime_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
