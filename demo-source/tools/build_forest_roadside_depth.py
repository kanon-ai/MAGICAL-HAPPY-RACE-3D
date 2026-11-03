"""Reuse proven forest repacker with current base/alternate ownership guards."""
from pathlib import Path
p=Path(__file__).with_name('build_forest_groves.py')
s=p.read_text()
s=s.replace('from audit_forest_repack_space import audit','from audit_current_forest_space import inspect\nfrom audit_bitpacked_geometry import audit,sample')
s=s.replace('from study_column_runs import column_pack,sample','from study_column_runs import column_pack')
s=s.replace('from study_column_runs import column_pack', 'from study_column_runs import column_pack\nfrom study_boundary_bitpack import bitpack')
s=s.replace('coded=column_pack(delta);raw=len(coded)>=32;new[delta]=(delta if raw else coded,raw)', 'coded=column_pack(delta);packed=bitpack(delta);coded=min((coded,packed),key=len) if packed[0]==0x84 else coded;raw=len(coded)>=32;new[delta]=(delta if raw else coded,raw)')

s=s.replace("work/forest-groves/forest/assets",'work/forest-roadside-depth/forest/assets')
s=s.replace('outputs/six-route-traffic-cadence','outputs/six-route-rock-bore-gpu-ring')
s=s.replace('_,used,patterns,groups,slots=audit(old);protected=bytes(used)', '_,used,patterns,groups,slots,current_layout,overlay=inspect(old,suffix);protected=bytes(used)')
s=s.replace("layout=json.loads((R/'outputs/dictionary-components-jump17-hybrid-lined/coast/geometry-layout.json').read_text())", 'layout=current_layout')
s=s.replace('report=audit(rom,layout,expected)[0]', '''city=(R/('outputs/six-route-city-silhouettes'+suffix)/'city-expected.bin').read_bytes()
 report=audit(rom,layout,expected,{'city':city})[0]
 overlay['groups']['forest']=entries
 alternate={stage:(R/f'work/snow-city-turn/{stage}/outputs/{stage}-expected.bin').read_bytes() for stage in ('snow','city')}
 assert audit(rom,overlay,expected,alternate)[0]['all_24576_compact_records_exact']''')
s=s.replace('outputs/six-route-forest-groves','outputs/six-route-forest-roadside-depth')
s=s.replace(' fields=[];new={}', ''' previous=(R/('outputs/six-route-city-silhouettes'+suffix)/'forest-expected.bin').read_bytes()
 retained={g for g in range(128) if expected[g*32*447:(g+1)*32*447]==previous[g*32*447:(g+1)*32*447]}
 for g in retained:
  bank,addr=current_layout['groups']['forest'][g];at=bank*16384+(addr&0x7fff)-0x4000
  n=int.from_bytes(old[at:at+2],'little')+2;used[at:at+n]=bytes([1])*n
  for _,ref in groups['forest'][g]:
   if ref is not None:
    at,n,_=patterns[ref];used[at:at+n]=bytes([1])*n
 print('Retained groups',len(retained),flush=True)
 fields=[];new={}''')
s=s.replace(' for g in range(128):\n  fs=[]', " for g in range(128):\n  if g in retained:\n   fields.append(groups['forest'][g]);continue\n  fs=[]")
s=s.replace("for g,fs in enumerate(fields)]+", "for g,fs in enumerate(fields) if g not in retained]+")
s=s.replace(' for g,fs in enumerate(fields):\n  blob=serialize', " for g,fs in enumerate(fields):\n  if g in retained:\n   entries.append(current_layout['groups']['forest'][g]);continue\n  blob=serialize")
s=s.replace('new_patterns=len(new),', 'new_patterns=len(new),retained_groups=len(retained),')
needle="ref=lookup[delta];off,n,_=patterns[ref];used[off:off+n]=b'\\1'*n"
assert s.count(needle)==1
s=s.replace(needle,"""ref=lookup[delta];off,n,raw=patterns[ref]
    if any(protected[off:off+n]):used[off:off+n]=bytes([1])*n
    else:
     # Consolidate forest-exclusive patterns after larger groups instead of
     # pinning scattered tiny records that fragment every available hole.
     new.setdefault(delta,(old[off:off+n],raw));ref=delta""")
s=s.replace(' locations={};written=bytearray(len(old))', """ diagnostic={'free_spans':free,'jobs':[{'kind':key[0],'bytes':n} for key,n in jobs], 'old_forest_group_sizes':[int.from_bytes(old[b*16384+(a&0x7fff)-0x4000:b*16384+(a&0x7fff)-0x4000+2],'little')+2 for b,a in current_layout['groups']['forest']]}
 (R/('outputs/forest-roadside-allocation-diagnostic'+suffix+'.json')).write_text(json.dumps(diagnostic,indent=2))
 locations={};written=bytearray(len(old))""")
s=s.replace(' for key,n in sorted(jobs,key=lambda x:x[1],reverse=True):', """ pending={key:n for key,n in jobs if key[0]=='g'}
 for k in sorted(range(len(free)),key=lambda k:free[k][1]):
  at,size=free[k]
  if not pending or size<min(pending.values()):continue
  choices={0:()}
  for key,n in pending.items():
   for total,keys in list(choices.items()):
    if total+n<=size and total+n not in choices:choices[total+n]=keys+(key,)
  total=max(choices)
  for key in choices[total]:
   n=pending.pop(key);locations[key]=at;written[at:at+n]=bytes([1])*n;at+=n
  free[k]=[at,size-total]
 assert not pending,('group packing',len(pending),sum(pending.values()))
 for key,n in sorted((job for job in jobs if job[0][0]=='p'),key=lambda x:x[1],reverse=True):""")
s=s.replace("('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin')", "tuple(f.name for f in src.glob('*.bin') if f.name.endswith(('-sky.bin','-atlas.bin')))")
exec(compile(s,str(p),'exec'),{'__file__':str(p)})
