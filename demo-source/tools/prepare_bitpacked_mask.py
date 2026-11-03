from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'tools/bitpacked_sample.asm').read_text()
old=''' pop af
 ld b,a
 xor a
bitpacked_mask_loop:
 scf
 rla
 djnz bitpacked_mask_loop
 and c
'''
new=''' pop af
 ld d,c
 ld c,a
 ld b,0
 ld hl,bitpacked_masks
 add hl,bc
 ld a,(hl)
 and d
'''
assert s.count(old)==1
s=s.replace(old,new)+'\nbitpacked_masks:\n db 0,1,3,7,15,31,63,127,255\n'
(R/'tools/bitpacked_sample_mask.asm').write_text(s)
