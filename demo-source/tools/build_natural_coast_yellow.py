from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parents[1];W=R/'work/natural-coast';W.mkdir(exist_ok=True)
A=R/'assets/player-four-colours';A.mkdir(exist_ok=True)
for p in (R/'assets/modern-player').glob('*'):
 if p.is_file():shutil.copy2(p,A/p.name)
s=(R/'tools/prepare_modern_player.py').read_text().split("board=Image.new")[0]
s=s.replace("assets/modern-player","assets/player-four-colours").replace("('black','red','blue')","('black','red','blue','yellow')")
s=s.replace("  # Nearest palette", "  elif color=='yellow':a[mask]=np.stack((r*.98+g*.02,r*.72+g*.10,g*.18),axis=2)[mask]\n  # Nearest palette")
exec(compile(s,'yellow-materials','exec'),{'__file__':str(R/'tools/prepare_modern_player.py')})
for c in ('black','red','blue'):assert (A/f'{c}-materials.bin').read_bytes()==(R/f'assets/modern-player/{c}-materials.bin').read_bytes()
s=(R/'tools/build_modern_player.py').read_text().replace("assets/modern-player","assets/player-four-colours").replace("outputs/modern-player","outputs/modern-player-yellow").replace("('black','red','blue')","('black','red','blue','yellow')")
s=s.replace(' ld (selected),a\n ld b,a',' bit 4,e\n jr nz,not_yellow\n ld a,3\nnot_yellow:\n ld (selected),a\n ld b,a')
s=s.replace(' add hl,de\ntable_ready:', ' add hl,de\n dec a\n jr z,table_ready\n add hl,de\ntable_ready:')
s=s.replace("1:BLK 2:RED 3:BLUE", "1:BK 2:R 3:B 4:Y")
exec(compile(s,'yellow-selector','exec'),{'__file__':str(R/'tools/build_modern_player.py')})
# Stable appearance choice belongs to the world object. Never use frame index,
# screen order or current distance to choose a species (would cause popping).
asm='''org 07c00h
 ld a,(0e24fh)
 cp 8
 jr nc,store_kind
 ld a,c
 cp 5
 jr nz,store_kind
 ld a,(ix-9)
 cp 2
 jr z,low_shrub
 cp 3
 jr nz,short_tree
 ld c,4
short_tree:
 ld l,(ix-12)
 ld h,(ix-11)
 bit 5,(hl)
 ld b,0
 jr z,height_ready
 ld a,(hl)
 xor 128
 ld (hl),a
 ld b,1
height_ready:
 ld l,(ix-5)
 ld h,(ix-4)
 ld de,4
 add hl,de
 ld a,(hl)
 ld d,a
 srl a
 srl a
 ld e,a
 ld a,d
 sub e
 bit 0,b
 jr z,height_store
 srl e
 sub e
height_store:
 ld (hl),a
 jr store_kind
low_shrub:
 ld c,7
store_kind:
 ld l,(ix-12)
 ld h,(ix-11)
 ld a,(hl)
 and 248
 or c
 ld (hl),a
 ret
'''
(W/'vegetation.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'vegetation.asm'),str(W/'vegetation.bin')],check=True)
helper=(W/'vegetation.bin').read_bytes()
for suffix in ('','-external-88h'):
 src=R/('outputs/pixel-coast-traffic-fit'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 a=next((R/('outputs/modern-player'+suffix)).glob('*.rom')).read_bytes();b=next((R/('outputs/modern-player-yellow'+suffix)).glob('*.rom')).read_bytes()
 changed=[]
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:assert old[i]==x,(i,old[i],x);rom[i]=y;changed.append(i)
 at=211*16384+8192+0x1c00;assert old[at:at+len(helper)]==bytes([255])*len(helper);rom[at:at+len(helper)]=helper
 needle=bytes.fromhex('dd6ef4dd66f57ee6f8b1dd6ef4dd66f577');start=214*16384+8192
 at=old.find(needle,start,start+6144);assert at>=0 and old.find(needle,at+1,start+6144)<0
 rom[at:at+len(needle)]=bytes.fromhex('3ed3320060cd007c')+bytes(len(needle)-8)
 O=R/('outputs/natural-coast-yellow'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(rom)
 assert len(rom)==4194304
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),vegetation_helper_bytes=len(helper),colour_changes=len(changed),scope='Coast tree species/height from stable appearance choices; fourth yellow player colour. No road, traffic, collision or other-stage scenery changes.',native_verified=False),indent=2))
 print(O)
