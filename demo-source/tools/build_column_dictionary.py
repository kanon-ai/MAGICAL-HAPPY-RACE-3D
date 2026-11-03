"""Isolated six-route shared-pattern pack, with exact random-access verification."""
from pathlib import Path
import json,sys
from mesh_geometry_codec import encode
from study_column_runs import column_pack,sample
R=Path(__file__).resolve().parents[1]
joined='--joined' in sys.argv
O=R/('work/joined-column-dictionary' if joined else 'work/column-dictionary');O.mkdir(parents=True,exist_ok=True)
stages=('coast','canyon','forest','snow','city','night')
patterns=[bytes(32)];ids={patterns[0]:0};references={};originals={}
for stage in stages:
    a=R/'assets' if stage=='coast' else R/('work/joined-route-shapes' if joined else 'work/route-shapes')/stage/'assets'
    road=(a/'long-course.bin').read_bytes();mesh=(a/'building-mesh.bin').read_bytes();rear=(a/'rear-course.bin').read_bytes()
    records=[]
    for i in range(4096):
        p=road[i*256:(i+1)*256];at=i//17*8192+i%17*480;m=mesh[at:at+480]
        records.append(b''.join(p[j:j+3] for j in range(0,123,9))+p[123:]+b''.join(encode(m[j:j+60]) for j in range(0,480,60))+rear[i*32:(i+1)*32])
    refs=bytearray()
    for first in range(0,4096,32):
        for field in range(447):
            base=records[first][field]
            key=bytes((records[first+j][field]-base)&255 for j in range(32))
            if key not in ids:ids[key]=len(patterns);patterns.append(key)
            refs.extend(bytes([base])+ids[key].to_bytes(2,'little'))
    references[stage]=bytes(refs);originals[stage]=records
    print(stage,'references prepared',flush=True)
assert len(patterns)<65536
coded=[]
for i,pattern in enumerate(patterns):
    data=column_pack(pattern)
    assert bytes(sample(data,j) for j in range(32))==pattern
    coded.append(data)
    if i%10000==0:print('patterns',i,'/',len(patterns),flush=True)
# Each dictionary entry is four bytes for a cheap shift/mask lookup at runtime.
# Pattern addresses here are logical half-bank offsets, resolved by a trial ROM.
blocks=[];locations=[None]*len(patterns)
for i in sorted(range(len(coded)),key=lambda i:len(coded[i]),reverse=True):
    data=coded[i]
    available=[j for j,b in enumerate(blocks) if len(b)+len(data)<=8192]
    if available:slot=max(available,key=lambda j:len(blocks[j]))
    else:slot=len(blocks);blocks.append(bytearray())
    locations[i]=(slot,len(blocks[slot]));blocks[slot].extend(data)
assert len(blocks)<256
directory=b''.join(bytes([slot])+offset.to_bytes(2,'little')+b'\0' for slot,offset in locations)
(O/'patterns.bin').write_bytes(b''.join(b+b'\xff'*(8192-len(b)) for b in blocks))
(O/'index.bin').write_bytes(directory)
for stage,refs in references.items():
    (O/f'{stage}-references.bin').write_bytes(refs)
    (O/f'{stage}-expected.bin').write_bytes(b''.join(originals[stage]))
    for phase,record in enumerate(originals[stage]):
        group=phase//32;index=phase%32;restored=bytearray()
        for field in range(447):
            at=(group*447+field)*3;base=refs[at];identifier=int.from_bytes(refs[at+1:at+3],'little')
            slot,offset=locations[identifier];length=blocks[slot][offset]
            restored.append((base+sample(blocks[slot][offset:offset+length+1],index))&255)
        assert restored==record,(stage,phase)
    print(stage,'all 4096 samples exact',flush=True)
pattern_bytes=len(blocks)*8192
index_bytes=((len(directory)+8191)//8192)*8192
reference_bytes=6*((128+5)//6)*8192 # six 1341-byte group records fit per half-bank
layout=json.loads((R/'outputs/rom-layout-audit.json').read_text())
old=json.loads((R/'assets/runtime-pack-report.json').read_text())
fixed=layout['reserved_bytes']-old['bank_padded_bytes']-old['index_bytes']
extra=5*(4096+65536+131072)
geometry=pattern_bytes+index_bytes+reference_bytes+6*128*3
report=dict(pattern_count=len(patterns),all_24576_samples_exact=True,
            pattern_bytes=pattern_bytes,index_bytes=index_bytes,reference_bytes=reference_bytes,
            geometry_bytes=geometry,conservative_total=geometry+fixed+extra,
            remaining_estimate=4194304-geometry-fixed-extra,
            limitation='Offline pack only. Final physical allocation, native random-access speed and driving integration unverified.')
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
