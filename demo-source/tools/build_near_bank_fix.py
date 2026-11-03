from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];w=R/'work/near-bank-fix';w.mkdir(exist_ok=True)
asm='''org 0d5ceh
 push hl
 ld hl,(06000h)
 ld a,h
 cp 04bh
 jr nz,ordinary
 ld a,l
 cp 042h
 jr nz,ordinary
 ld a,210
 jr selected
ordinary:
 ld a,252
selected:
 push af
 ld a,187
 ld (06000h),a
 call 07800h
 pop af
 ld (06000h),a
 pop hl
 ld a,(ix-11)
 ret
'''
(w/'gate.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'gate.asm'),str(w/'gate.bin')],check=True)
code=(w/'gate.bin').read_bytes();assert len(code)<=0xd600-0xd5ce
phys=lambda a:(1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/impact-stop'+suffix);f=next(src.glob('*.rom'));old=f.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 assert [i for i in range(256) if old[i*16384+8192:i*16384+8194]==bytes.fromhex('424b')]==[210]
 at=phys(0xd5ce);original=bytes.fromhex('3ebb320060cd00783efc320060dd7ef5c9');assert old[at:at+len(original)]==original;assert all(v==255 for v in old[at+len(original):at+len(code)])
 rom=bytearray(old);rom[at:at+len(code)]=code
 out=R/('outputs/near-bank-fix'+suffix);out.mkdir(exist_ok=True);(out/f.name).write_bytes(rom)
 assert all(at<=i<at+len(code) for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (out/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'source_sha256':hashlib.sha256(old).hexdigest(),'changed_range':hex(0xd5ce)+'-'+hex(0xd5ce+len(code)-1),'scope':'Restore tunnel renderer bank 210 after cockpit near-traffic projection; otherwise retain bank 252. No gameplay or visual parameter changes.'},indent=2))
 print(out,len(code))
