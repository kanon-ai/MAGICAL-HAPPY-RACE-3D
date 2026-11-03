"""Trial: retain shared tree5 for identity1 in the final snow piece only."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
code=bytearray();labels={};fix=[]
def emit(h):code.extend(bytes.fromhex(h))
def jr(op,label):emit(op);fix.append((len(code),label));emit('00')
emit('3a4fe2fe1f');jr('20','old')
emit('dd7ef8fe01');jr('20','old')
emit('3e05');jr('18','store')
labels['old']=len(code);emit('dd7ef8b73e04');jr('20','store');emit('3e07')
labels['store']=len(code);emit('dd77f8c9')
for at,label in fix:code[at]=(labels[label]-at-1)&255
assert len(code)<=32
for suffix in ('','-external-88h'):
    source=R/('outputs/six-route-boundary-nibble-dispatch'+suffix)
    path=next(source.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
    a=0xd7e0;at=(1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
    previous=bytes.fromhex('dd7ef8b73e0420023e07dd77f8c9')
    assert old[at:at+len(previous)]==previous
    # Facade selector was relocated to9650; DBAC unconditionally jumps there.
    # Reuse only its unreachable former body, retaining the redirect.
    def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
    retired=bytes.fromhex('dd6ef6dd66f7113a00193a4fe2860600fe29dd7ef8300afe010e05c8fe03c81805fe030e01c8fe020e02c80e00c9')
    assert old[off(0xdbac):off(0xdbac)+len(retired)]==bytes.fromhex('c35096')+retired[3:]
    assert len(code)<=len(retired)-3
    snow=(source/'snow-atlas.bin').read_bytes();city=(source/'city-atlas.bin').read_bytes()
    assert all(snow[y*256+192:y*256+256]==city[y*256+192:y*256+256] for y in range(128,192))
    rom[off(0xdbaf):off(0xdbaf)+len(code)]=code
    rom[at:at+3]=bytes.fromhex('c3afdb')
    assert len(rom)==4194304
    changes=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
    assert all(at<=i<at+3 or off(0xdbaf)<=i<off(0xdbaf)+len(code) for i in changes)
    out=R/('outputs/six-route-snow-city-trees'+suffix);out.mkdir(exist_ok=True)
    (out/path.name).write_bytes(rom)
    for f in source.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),changed_bytes=len(changes),helper_bytes=len(code),shared_tree_pixels=4096,scope='Only piece31 identity1 scenery uses shared tree5; geometry and gameplay unchanged',native_verified=False),indent=2))
    print(out.name,len(code))
