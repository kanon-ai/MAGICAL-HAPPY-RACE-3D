"""Run the verified joined-data pipeline in a separate expressive namespace.

Only offline asset paths/flags change. Existing ROMs and capture evidence stay
intact. Native decoder, physics, art and audio are the verified baseline.
"""
from pathlib import Path
import sys, subprocess, hashlib, json
R=Path(__file__).resolve().parents[1]
variant='adaptive' if '--adaptive' in sys.argv else 'expressive'
if '--stable' in sys.argv:variant='stable'
if '--lined' in sys.argv:variant='lined'
STEPS=[
 ('build_column_dictionary.py',[]),
 ('build_hybrid_dictionary.py',[]),
 ('pack_appearance_tiles.py',[]),
 ('verify_dictionary_native.py',['coast','--components','--jump17','--hybrid','--pack-only']),
 ('build_dictionary_standalone.py',['--hybrid']),
 ('plan_six_route_layout.py',['--dedup']),
 ('build_appearance_trial.py',['--relocated','--dedup']),
 ('build_six_route_trial.py',['--dedup']),
]
if '--step' in sys.argv:
 i=int(sys.argv[sys.argv.index('--step')+1]);name,args=STEPS[i]
 source=R/'tools'/name
 code=source.read_text().replace('joined-',variant+'-').replace('-joined','-'+variant)
 if variant in ('stable','lined') and name=='build_column_dictionary.py':
  # Stages16..31 unconditionally resolve active objects to sprites4/5/7.
  # apply_coast_appearance still uses mesh+40 (compact+9) for left placement.
  # Preserve that exact signed delta; other mesh bytes have no visible reader.
  needle='from mesh_geometry_codec import encode\n'
  assert needle in code
  code=code.replace(needle,needle+"def visible_mesh(record,stage):\n    return bytes(9)+record[9:11]+bytes(19) if stage in ('forest','snow') else record\n")
  needle='encode(m[j:j+60]) for j in range(0,480,60)'
  assert needle in code
  code=code.replace(needle,'visible_mesh(encode(m[j:j+60]),stage) for j in range(0,480,60)')
 # Offline dictionary IDs may exceed 65535. Native component pointers remain
 # exactly three bytes; only the intermediate host-side reference ID widens.
 replacements={
  'build_column_dictionary.py':[("ids[key].to_bytes(2,'little')","ids[key].to_bytes(3,'little')"),('len(patterns)<65536','len(patterns)<16777216'),('(group*447+field)*3','(group*447+field)*4'),('refs[at+1:at+3]','refs[at+1:at+4]')],
  'build_hybrid_dictionary.py':[('range(0,len(data),3)','range(0,len(data),4)'),('data[at+1:at+3]','data[at+1:at+4]'),('(group*447+field)*3','(group*447+field)*4'),('budget=256*1024','budget=32*1024')],
  'verify_dictionary_native.py':[('(group*447+first+within)*3','(group*447+first+within)*4'),('refs[at+1:at+3]','refs[at+1:at+4]')],
 }
 for old,new in replacements.get(name,[]):
  assert old in code,(name,old)
  code=code.replace(old,new)
 sys.argv=[str(source),*args,'--'+variant]
 exec(compile(code,str(source),'exec'),dict(__name__='__main__',__file__=str(source)))
else:
 start=int(sys.argv[sys.argv.index('--from')+1]) if '--from' in sys.argv else 0
 for i,(name,_) in enumerate(STEPS):
  if i<start:continue
  print('STEP',i,name,flush=True)
  subprocess.run([sys.executable,__file__,'--step',str(i),'--'+variant],cwd=R,check=True)
 name='MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
 before=(R/'outputs/six-route-trial-joined'/name).read_bytes()
 after=(R/'outputs/six-route-mirror'/name).read_bytes()
 rom=bytearray((R/f'outputs/six-route-trial-{variant}-dedup'/name).read_bytes())
 changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
 for i in changed:
  assert rom[i]==before[i],('Transition patch conflict',i)
  rom[i]=after[i]
 if variant in ('adaptive','stable','lined'):
  proof=json.loads((R/'work/adaptive-road-reader/reader-proof.json').read_text())
  at=16384+8192+proof['patch_address']-0x8000
  old=bytes.fromhex(proof['original_bytes']);assert rom[at:at+len(old)]==old
  rom[at:at+len(old)]=bytes.fromhex(proof['replacement_bytes'])
  helper=(R/'work/adaptive-road-reader/reader.bin').read_bytes()
  at=214*16384+8192+proof['helper_address']-0x2400
  assert rom[at:at+len(helper)]==b'\xff'*len(helper)
  rom[at:at+len(helper)]=helper
 out=R/f'outputs/six-route-{variant}';out.mkdir(exist_ok=True)
 (out/name).write_bytes(rom)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),transition_patch_bytes=len(changed),runtime_verified=False)
 (out/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report)
