"""Smooth pixel-tree scaling; accepted coast-scale ROMs remain untouched."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
W=R/'work/pixel-tree-smooth';W.mkdir(exist_ok=True)
asm="""org 0bfffh
 ld a,(ix-14)
 ld e,a
 ld l,a
 ld h,0
 inc hl
 srl h
 rr l
 srl h
 rr l
 ld a,e
 sub l
 ld (ix-14),a
"""
(W/'round.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'round.asm'),str(W/'round.bin')],check=True)
old=bytes.fromhex('dd7ef2cb3fdd77fbdd7ef20f0fe63fdd77fcdd7efbdd86fcdd77f2')
code=(W/'round.bin').read_bytes();assert len(code)<=len(old)
code+=bytes(len(old)-len(code))
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
indices=[off(0xbfff+i) for i in range(len(old))]
for suffix in ('','-external-88h'):
 src=R/('outputs/coast-scale'+suffix);p=next(src.glob('*.rom'));b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 assert bytes(b[i] for i in indices)==old
 out=bytearray(b)
 for i,v in zip(indices,code):out[i]=v
 assert all(i in indices for i,(x,y) in enumerate(zip(b,out)) if x!=y)
 O=R/('outputs/pixel-tree-smooth'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(out)
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(out).hexdigest(),source_sha256=hashlib.sha256(b).hexdigest(),bytes=len(out),scope='Round-tree height: rounded 3*h/4 instead of two truncated shifts. Pixel art and all other bytes preserved.'),indent=2))
heights=[max(1,h-((h+1)//4)) for h in range(1,256)]
assert all(0<=b-a<=1 for a,b in zip(heights,heights[1:]))
print('Both ROMs patched; exhaustive 255-size monotonic scaling check passed.')
