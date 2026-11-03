from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'tools/bitpacked_sample.asm';s=p.read_text()
old=' xor a\nbitpacked_multiply:\n add a,c\n djnz bitpacked_multiply\n'
assert s.count(old)==1
s=s.replace(old,' ld a,b\n db 0edh,0c9h ; R800 MULUB A,C -> HL\n ld a,l\n')
(R/'tools/bitpacked_sample_mul.asm').write_text(s)
