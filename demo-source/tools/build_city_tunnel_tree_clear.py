from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/portal-tree-mask';W.mkdir(exist_ok=True)
raw=(R/'work/lined-route-shapes/city/assets/long-course.bin').read_bytes();slots=[]
for phase in range(3030,3286):
 dep=326400-phase*100;found=[]
 if 650<=dep<=22000:
  width=min(250,round(174000/dep));size=max(0,min(254,round(336000/dep)-1))
  for k in range(8):
   b=raw[phase*256+128+k*8:phase*256+136+k*8]
   if b[7]==width and b[4]==size:found.append(k)
 assert len(found)<=1,(phase,found)
 slots.append(found[0] if found else 15)
mask=bytes(slots[i]|slots[i+1]<<4 for i in range(0,256,2))
(W/'mask.bin').write_bytes(mask);(W/'slots.json').write_text(json.dumps(slots))
asm='''org 0b28ah
push af
push hl
push de
push bc
ld a,(0e24fh)
cp 39
jr nz,done
ld hl,(0e24bh)
ld de,-3030
add hl,de
ld a,h
or a
jr nz,done
ld a,l
and 1
ld c,a
srl l
ld de,table
add hl,de
ld a,(hl)
bit 0,c
jr z,mask_low
rrca
rrca
rrca
rrca
mask_low:
and 15
cp 8
jr nc,done
add a,a
add a,a
add a,a
ld l,a
ld h,0
ld de,0e2e9h
add hl,de
ld (hl),0
done:
pop bc
pop de
pop hl
pop af
ret
table:
'''+ 'db '+','.join(str(x) for x in mask)+'\n'
(W/'filter.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'filter.asm'),str(W/'filter.bin')],check=True)
code=(W/'filter.bin').read_bytes();assert 0xb28a+len(code)<=0xb351,len(code)
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-city-tunnel-portal-lod'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();b=bytearray(old)
 stub=old[off(0xb260):off(0xb260)+39];assert stub[:3]==bytes.fromhex('cda9bb') and stub[-1]==0xc9,stub.hex()
 new=bytes.fromhex('cd8ab2')+stub;assert 0xb260+len(new)<=0xb28a
 b[off(0xb260):off(0xb260)+len(new)]=new;b[off(0xb28a):off(0xb28a)+len(code)]=code
 assert len(b)==4194304 and all(off(0xb260)<=i<off(0xb351) for i,(a,z) in enumerate(zip(old,b)) if a!=z)
 out=R/('outputs/six-route-city-tunnel-tree-clear'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(b)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'filter_bytes':len(code),'scope':'Hide world tree408 only city piece39 using phase-indexed slot map. Native verification pending.'};(out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
