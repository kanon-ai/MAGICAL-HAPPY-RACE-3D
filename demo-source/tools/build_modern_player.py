"""Player-only overlay on the hashed accepted ROM; original is never modified."""
from pathlib import Path
import json,hashlib,subprocess
from pack_atlas import encode
R=Path(__file__).resolve().parents[1];A=R/'assets/modern-player'
S=json.loads((R/'outputs/symbols.json').read_text())
state=S['_bgm_poll']+46;tramp=S['_bgm_poll']+3;reader=tramp+26
def resident(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix,sha in [('', '6e44423ff275cb4c17ec9a3d564a9f41037c49aecf65ec2cc1e38f7f8d354bb5'),('-external-88h','9291cfda55ef2aaebcc8825b2c0d9e97c647cc2eeb4871e13a565a33eb50f3fd')]:
 src=next((R/('outputs/six-route-traffic-near-truck-fast'+suffix)).glob('*.rom'));old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==sha
 O=R/('outputs/modern-player'+suffix);O.mkdir(exist_ok=True);rom=bytearray(old);allowed=set()
 def put(at,data):
  rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 def bankput(b,o,data):put(b*16384+8192+o,data)
 # Projection slots occupy only 920 bytes each; all listed holes are explicit
 # packet/cache padding, never generic FF-byte guesses or course storage.
 packet=(R/'assets/player-packet.bin').read_bytes();assert packet[0]==26 and packet[1024:]==bytes(3072)
 newpacket=(A/'player-packet.bin').read_bytes();bankput(215,0,newpacket)
 count_at=214*16384+8192+0x2bd4-0x2400
 assert old[count_at-1:count_at+3]==bytes.fromhex('3e1a1815');put(count_at,bytes([newpacket[0]]))
 cache=(A/'player-projection.bin').read_bytes()
 for b in range(6):bankput(216+b,0,cache[b*8192:(b+1)*8192])
 bankput(215,4096,(A/'player-model.bin').read_bytes())
 slots=[(215,1024,4096)]+[(216+b,7360,8192) for b in range(5)]+[(221,4600,8192)]
 for b,a,z in slots:assert not any(rom[b*16384+8192+a:b*16384+8192+z])
 table=bytearray();dedup={};slot=0;at=slots[0][1]
 for color in ('black','red','blue'):
  data=(A/f'{color}-materials.bin').read_bytes()
  for row in range(96):
   raw=data[row*48:row*48+48]
   if raw not in dedup:
    enc=bytes(encode(raw))
    if at+len(enc)>slots[slot][2]:slot+=1;at=slots[slot][1]
    b=slots[slot][0];bankput(b,at,enc);dedup[raw]=bytes([b])+int(0x6000+at).to_bytes(2,'little');at+=len(enc)
   table.extend(dedup[raw])
 bankput(215,0x1800,table)
 port=0x88 if suffix else 0x98;control=port+1
 asm=f'''org 07580h
selected equ {state}
loaded equ {state+1}
last_rows equ {state+2}
last_stage equ {state+4}
entry:
 in a,(0aah)
 ld d,a
 and 0f0h
 out (0aah),a
 in a,(0a9h)
 ld e,a
 ld a,d
 out (0aah),a
 ld a,(selected)
 bit 1,e
 jr nz,not_black
 xor a
not_black:
 bit 2,e
 jr nz,not_red
 ld a,1
not_red:
 bit 3,e
 jr nz,not_blue
 ld a,2
not_blue:
 ld (selected),a
 ld b,a
 ld a,(loaded)
 cp b
 jr nz,full
 ld a,(60649)
 ld b,a
 ld a,(last_stage)
 cp b
 jr nz,full
 ld hl,(60650)
 ld de,(last_rows)
 or a
 sbc hl,de
 ret z
 ld a,h
 or a
 jr nz,full
 ld a,l
 cp 2
 jr nz,full
 ; Only the two newly streamed player rows need restoring. All other
 ; scenery rows are untouched, without a full texture upload each frame.
 ld hl,(60650)
 ld (last_rows),hl
 ld a,h
 or a
 ret nz
 ld a,l
 cp 130
 ret c
 cp 225
 ret nc
 sub 130
 ld d,a
 add a,2
 ld e,a
 jr upload
full:
 ld a,(selected)
 ld (loaded),a
 ld a,(60649)
 ld (last_stage),a
 ld hl,(60650)
 ld (last_rows),hl
 ld de,96
upload:
 push de
 call {S['_gfx_wait']}
 pop de
 push de
 ld a,(selected)
 ld hl,07800h
 ld de,288
 or a
 jr z,table_ready
 add hl,de
 dec a
 jr z,table_ready
 add hl,de
table_ready:
 pop de
 push de
 ld a,d
 ld e,a
 ld d,0
 add hl,de
 add hl,de
 add hl,de
 pop de
rows:
 push de
 push hl
 ; VRAM destination: x80, y896 + row. VDP direct writes are bounded to48.
 ld a,d
 add a,128
 ld e,a
 rrca
 rrca
 rrca
 rrca
 rrca
 rrca
 and 3
 add a,12
 out ({control}),a
 ld a,08eh
 out ({control}),a
 ld a,80
 out ({control}),a
 ld a,e
 and 63
 or 040h
 out ({control}),a
 ld a,(hl)
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 call {reader}
 ld hl,{S['_graphics_buffer']}
 ld e,48
token:
 ld a,(hl)
 inc hl
 ld d,a
 and 127
 inc a
 ld b,a
 ld a,e
 sub b
 ld e,a
 bit 7,d
 jr nz,repeat_run
 ld c,{port}
 otir
 jr run_done
repeat_run:
 ld a,(hl)
 inc hl
repeat_pixel:
 out ({port}),a
 djnz repeat_pixel
run_done:
 ld a,e
 or a
 jr nz,token
 ld a,215
 ld (06000h),a
 call {S['_bgm_poll']}
 pop hl
 inc hl
 inc hl
 inc hl
 pop de
 inc d
 ld a,d
 cp e
 jr nz,rows
 ret
'''
 (O/'selector.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'selector.asm'),str(O/'selector.bin')],check=True)
 code=(O/'selector.bin').read_bytes();assert len(code)<640
 assert old[215*16384+8192+0x1580:215*16384+8192+0x1800]==b'\xff'*640
 bankput(215,0x1580,code)
 # Reuse only the 49 obsolete bytes following the merged BGM poll's JP.
 assert old[resident(tramp):resident(tramp)+49]==bytes(49)
 stub=bytes.fromhex('f5c5d5e53ed7320060cd80753efc320060e1d1c1f10e003e08c9')
 assert len(stub)==26;put(resident(tramp),stub)
 # Bank changes execute in resident RAM; copy one bounded encoded row before
 # returning to bank215. graphics_buffer is the existing loading scratch.
 readcode=bytes.fromhex('32006001310011')+S['_graphics_buffer'].to_bytes(2,'little')+bytes.fromhex('edb03ed7320060c9')
 assert len(readcode)==17 and reader+17==state
 put(resident(reader),readcode);put(resident(state),bytes([1,255,255,255,255]))
 hook=214*16384+8192+S['_draw_player_car']-0x2400
 assert old[hook:hook+4]==bytes.fromhex('0e003e08')
 put(hook,b'\xcd'+tramp.to_bytes(2,'little')+b'\0')
 # Replace the existing title description within its original allocation.
 label=b'1:BLK 2:RED 3:BLUE\0'
 labels=json.loads((R/'assets/title-copy.json').read_text(encoding='utf-8-sig'))
 previous=labels['description'].encode()+b'\0';p=old.find(previous)
 assert p>=0 and old.find(previous,p+1)<0 and len(label)<=20
 put(p,label.ljust(20,b'\0'))
 assert len(rom)==len(old) and all(i in allowed for i,(x,y) in enumerate(zip(old,rom)) if x!=y)
 (O/src.name).write_bytes(rom)
 report=dict(bytes=len(rom),source_sha256=sha,sha256=hashlib.sha256(rom).hexdigest(),selector_bytes=len(code),unique_texture_rows=len(dedup),texture_bytes=sum(len(encode(k)) for k in dedup),state_address=state,scope='Player-only mesh/materials and colour keys 1/2/3 in chase view. Physics, traffic, courses, palette, audio unchanged.',native_verified=False)
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
