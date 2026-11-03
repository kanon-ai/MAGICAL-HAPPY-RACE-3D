"""Taper feather width to zero at transition endpoints, retaining current trial."""
from pathlib import Path
p=Path(__file__).with_name('build_early_seam_render.py')
s=p.read_text().replace('six-route-early-seam-render','six-route-early-seam-taper')
marker=' asm=fallback+head+cache+upload+tail'
patch=''' start=tail.index('clip_band:\\n');end=tail.index('clip_ready:\\n')
 tail=tail[:start]+''' + repr('''clip_band:
 ld a,(0f6d4h)
 cp 128
 jr c,radius_positive
 neg
radius_positive:
 cp 12
 jr c,radius_ready
 ld a,12
radius_ready:
 ld e,a
 add a,a
 ld b,a
 ld a,12
 sub e
 ld c,a
 ld hl,256
 ld de,(0f6d4h)
 or a
 sbc hl,de
 ld a,b
 srl a
 ld e,a
 ld d,0
 or a
 sbc hl,de
''')+'''+tail[end:]
'''+marker
assert marker in s;s=s.replace(marker,patch)
exec(compile(s,str(p),'exec'))
