"""Prepare and verify city cuboid compact records before ROM allocation."""
from pathlib import Path
import json,hashlib
from mesh_geometry_codec import encode,decode
from study_column_runs import column_pack,sample
R=Path(__file__).resolve().parents[1];out=R/'work/city-silhouettes/city/outputs'
def compact(a):
 road=(a/'long-course.bin').read_bytes();mesh=(a/'building-mesh.bin').read_bytes();rear=(a/'rear-course.bin').read_bytes();records=[]
 for i in range(4096):
  p=road[i*256:(i+1)*256];at=i//17*8192+i%17*480;m=mesh[at:at+480];parts=[]
  for j in range(0,480,60):
   c=encode(m[j:j+60]);assert decode(c)==m[j:j+60];parts.append(c)
  records.append(b''.join(p[j:j+3] for j in range(0,123,9))+p[123:]+b''.join(parts)+rear[i*32:(i+1)*32])
 return records
base=compact(R/'work/lined-route-shapes/city/assets')
assert b''.join(base)==(R/'work/lined-column-dictionary/city-expected.bin').read_bytes()
new=compact(R/'work/city-silhouettes/city/assets')
changed=set()
for a,b in zip(base,new):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:changed.add(i)
# Only each cuboid front/back roof-Y bytes may differ.
allowed={175+slot*30+offset for slot in range(8) for offset in (6,7,19,20)}
assert changed<=allowed,(changed-allowed)
patterns={}
for g in range(128):
 for f in range(447):
  first=new[g*32][f];delta=bytes((new[g*32+j][f]-first)&255 for j in range(32))
  if any(delta) and delta not in patterns:
   c=column_pack(delta);assert bytes(sample(c,j) for j in range(32))==delta;patterns[delta]=c
raw=b''.join(new);(out/'city-expected.bin').write_bytes(raw)
report={'baseline_matches_authoritative_expected':True,'all_cuboids_roundtrip_exact':True,'changed_fields':sorted(changed),'roof_y_only':True,'unique_variable_patterns':len(patterns),'compressed_pattern_bytes_before_shared_reuse':sum(min(32,len(c)) for c in patterns.values()),'sha256':hashlib.sha256(raw).hexdigest(),'scope':'Host compact/column roundtrip only, ROM allocation and native run pending'}
(out/'compact-proof.json').write_text(json.dumps(report,indent=2));print(report)
