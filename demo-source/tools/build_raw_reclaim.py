"""Lossless in-place raw pattern compression trial, preserving all decoded data."""
from pathlib import Path
import json,hashlib
from audit_stage_repack_space import audit
from study_column_runs import column_pack
R=Path(__file__).resolve().parents[1];study=json.loads((R/'outputs/raw-pattern-reclaim-study.json').read_text())
selected={tuple(x['pointer']):x for x in study['selected']}
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-building-pair-cache'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 g=R/('outputs/six-route-city-silhouettes'+suffix);layout=json.loads((g/'geometry-layout.json').read_text());forest=(g/'forest-expected.bin').read_bytes();city=(g/'city-expected.bin').read_bytes()
 proof,_,patterns,groups,slots=audit(old,layout,forest,{'city':city})
 if not suffix:assert proof['rom_sha256']==study['sha256']
 allowed=bytearray(len(old));freed=[]
 for ptr,x in selected.items():
  at,n,raw=patterns[ptr];assert raw and n==32 and at==x['offset']
  packed=bytes(column_pack(old[at:at+32]));assert len(packed)==x['compressed_bytes']
  rom[at:at+len(packed)]=packed;allowed[at:at+len(packed)]=bytes([1])*len(packed)
  freed.append([at+len(packed),32-len(packed)])
 changes=0
 for entries in layout['groups'].values():
  for bank,address in entries:
   at=bank*16384+(address&0x7fff)-0x4000;end=at+2+int.from_bytes(old[at:at+2],'little');cursor=at+2
   for count in [175]+[30]*8+[32]:
    length=int.from_bytes(old[cursor:cursor+2],'little');cursor+=2;partend=cursor+length
    for first in range(0,count,8):
     flags=old[cursor];cursor+=1
     for j in range(min(8,count-first)):
      cursor+=1
      if flags&(1<<j):
       ptr=(old[cursor],int.from_bytes(old[cursor+1:cursor+3],'little'))
       if ptr in selected:rom[cursor+2]&=127;allowed[cursor+2]=1;changes+=1
       cursor+=3
    assert cursor==partend
   assert cursor==end
 assert changes==study['selected_reference_count']
 seam=json.loads((R/('outputs/six-route-early-seam-data'+suffix)/'manifest.json').read_text())
 for at,n in seam['writes']:assert rom[at:at+n]==old[at:at+n]
 assert all(x==y or allowed[i] for i,(x,y) in enumerate(zip(old,rom)))
 proof=audit(rom,layout,forest,{'city':city})[0]
 out=R/('outputs/six-route-raw-reclaim'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 proof.update(bytes=len(rom),nominal_freed_bytes=sum(n for _,n in freed),freed_spans=freed,changed_pointer_flags=changes,scope='All decoded records exact; reclaimed tails fragmented, not yet allocated; native speed unverified',adopted=False)
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,proof['rom_sha256'],proof['nominal_freed_bytes'],flush=True)
