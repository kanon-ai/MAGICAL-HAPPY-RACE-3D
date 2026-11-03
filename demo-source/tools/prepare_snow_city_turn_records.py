"""Verify generated geometry and form native-compatible compact records."""
from pathlib import Path
import json,hashlib
from mesh_geometry_codec import encode,decode
R=Path(__file__).resolve().parents[1]
reports=[]
for stage in ('snow','city'):
 folder=R/'work/snow-city-turn'/stage;assert (folder/'outputs/candidate.json').is_file()
 a=folder/'assets';road=(a/'long-course.bin').read_bytes();mesh=(a/'building-mesh.bin').read_bytes();rear=(a/'rear-course.bin').read_bytes()
 assert len(road)==4096*256 and len(rear)==4096*32
 expected=(R/('work/city-silhouettes/city/outputs/city-expected.bin' if stage=='city' else 'work/lined-column-dictionary/snow-expected.bin')).read_bytes()
 records=[];changed=[]
 for i in range(4096):
  p=road[i*256:(i+1)*256];at=i//17*8192+i%17*480;m=mesh[at:at+480];parts=[]
  for j in range(0,480,60):
   c=encode(m[j:j+60]);assert decode(c)==m[j:j+60]
   if stage=='snow':c=bytes(9)+c[9:11]+bytes(19)
   parts.append(c)
  record=b''.join(p[j:j+3] for j in range(0,123,9))+p[123:]+b''.join(parts)+rear[i*32:(i+1)*32]
  assert len(record)==447
  old=expected[i*447:(i+1)*447]
  if old!=record:changed.append(i)
  if (stage=='snow' and i<2048) or (stage=='city' and i>=2048):assert record==old,(stage,i,'unrelated half changed')
  records.append(record)
 raw=b''.join(records);(folder/'outputs'/f'{stage}-expected.bin').write_bytes(raw)
 report=dict(stage=stage,records=len(records),mesh_roundtrip_count=4096*8,changed_records=len(changed),first_changed=min(changed),last_changed=max(changed),unrelated_half_exact=True,sha256=hashlib.sha256(raw).hexdigest(),scope='Host geometry codec/scope checks; native projection and capacity pending')
 reports.append(report);print(report)
(R/'outputs/snow-city-turn-study/compact-proof.json').write_text(json.dumps(reports,indent=2))
