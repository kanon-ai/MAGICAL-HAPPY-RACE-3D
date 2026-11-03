"""Stage1 atlas and existing terrain face materials; all other ROM banks preserved."""
from pathlib import Path
import sys,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];A=R/'assets/pixel-coast'
sys.path.insert(0,str(R.parents[3]/'public-road-cockpit/tools'))
from graphics_codec import compress
raw=(A/'coast-atlas.bin').read_bytes();packed=bytearray(40960)
ends=[]
for page,start in enumerate((0,3*8192+632)):
 pos=start
 for i in range(32):
  chunk=bytes([1])+compress(raw[page*32768+i*1024:page*32768+(i+1)*1024])
  if pos//8192!=(pos+len(chunk)-1)//8192:pos=(pos//8192+1)*8192
  assert pos+len(chunk)<=(3*8192+632 if page==0 else 40960)
  packed[pos:pos+len(chunk)]=chunk;pos+=len(chunk)
 ends.append(pos)
mat=json.loads((A/'materials.json').read_text())
extra='''
coast_surfaces:
 push bc
 ld a,(ix-9)
 push af
 ld a,(ix-1)
 add a,a
 add a,a
 ld d,a
 add a,a
 add a,d
 ld (ix-9),a
 ld a,(60649)
 or a
 jr z,coast_active
 ld hl,(60650)
 ld de,225
 or a
 sbc hl,de
 jr c,coast_active
 ld a,(ix-1)
 ld e,a
 ld d,0
 ld hl,0e833h
 add hl,de
 ld a,(hl)
 xor 128
 ld c,a
 ld hl,left_walk
 ld a,6
 call face
 ld a,(ix-1)
 ld e,a
 ld d,0
 ld hl,0e817h
 add hl,de
 ld c,(hl)
 ld hl,old_right_land
 ld a,1
 call face
 pop af
 ld (ix-9),a
 pop bc
 ret
coast_active:
 ld c,SANDFALLBACK
 ld hl,left_walk
 ld a,6
 call face
 ld c,GRASSFALLBACK
 ld hl,old_right_land
 ld a,1
 call face
 pop af
 ld (ix-9),a
 pop bc
 ld a,(ix-5)
 and 7
 add a,112
 ld h,a
 ld a,c
 and 7
 add a,112
 cp h
 jr c,coast_road_ready
 jr z,coast_road_ready
 sub 8
coast_road_ready:
 ld l,a
 ld d,64
 ld e,127
 ld b,4
 call coast_uv
 ld a,(ix-5)
 and 3
 add a,100
 ld h,a
 ld a,c
 and 3
 add a,100
 cp h
 jr c,coast_land_ready
 jr z,coast_land_ready
 sub 4
coast_land_ready:
 ld l,a
 ld d,64
 ld e,95
 ld b,6
 call coast_uv
 ld d,96
 ld e,127
 ld b,1
coast_uv:
 ld a,065h
 out (157),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 add a,b
 out (159),a
 ld a,053h
 out (157),a
 ld a,d
 out (159),a
 ld a,h
 out (159),a
 ld a,e
 out (159),a
 ld a,h
 out (159),a
 ld a,e
 out (159),a
 ld a,l
 out (159),a
 ld a,d
 out (159),a
 ld a,l
 out (159),a
 ret
'''.replace('SANDFALLBACK',str(mat['sand_fallback'])).replace('GRASSFALLBACK',str(mat['grass_fallback']))
source=(R/'outputs/six-route-inland-uv/helper.asm').read_text()
source=source.replace(' ret\nleft_land:', ' jp coast_surfaces\nleft_land:')+extra
for suffix in ('','-external-88h'):
 O=R/('outputs/pixel-coast'+suffix);O.mkdir(exist_ok=True)
 code=source if not suffix else source.replace('(157)','(141)').replace('(159)','(143)')
 (O/'helper.asm').write_text(code)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'helper.asm'),str(O/'helper.bin')],check=True)
 src=R/('outputs/modern-traffic'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes()
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 rom=bytearray(old);allowed=set()
 for n in range(5):
  at=(16+n)*16384+8192;rom[at:at+8192]=packed[n*8192:(n+1)*8192];allowed.update(range(at,at+8192))
 at=188*16384+8192;helper=(O/'helper.bin').read_bytes()
 prior=(R/('outputs/six-route-inland-uv'+suffix)/'helper.bin').read_bytes()
 assert old[at:at+len(prior)]==prior and set(old[at+len(prior):at+8192])<={255}
 rom[at:at+8192]=helper+bytes([255])*(8192-len(helper));allowed.update(range(at,at+8192))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/p.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),compressed_page_ends=ends,helper_bytes=len(helper),scope='Stage1 atlas and terrain material helper only; palette, geometry, physics, cars, panorama, music unchanged',native_verified=False),indent=2))
 print(O,ends,len(helper))
