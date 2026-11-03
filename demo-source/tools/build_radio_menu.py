from pathlib import Path
import subprocess,os,re,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/radio-menu';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6500','--data-loc','0xdff8','-Wl-b_HOME=0x6af0',str(R/'src/radio_menu.c'),'-o',str(W/'menu.ihx')],env=env,check=True)
mp=(W/'menu.map').read_text();ui=int(re.search(r'([0-9A-F]{8})\s+_radio_menu\s',mp)[1],16)
slots=[(207,0x6300,0x8000),(208,0x6200,0x8000),(209,0x6200,0x8000),(199,0x6c00,0x8000)]
chunks=[];payload=[];slot=0;at=slots[0][1]
for name in ('bgm1','bgm2'):
 data=(R/f'assets/radio/{name}.opz').read_bytes();pos=0;parts=[]
 while pos<len(data):
  bank,start,end=slots[slot];n=min(end-at,len(data)-pos);parts.append((bank,at,n));payload.append((bank*16384+at-0x4000,data[pos:pos+n]));pos+=n;at+=n
  if at==end:slot+=1;at=slots[slot][1]
 chunks.append(parts)
chunks.append([(193,0x6000,8192),(194,0x6000,len((R/'assets/radio/bgm3.opz').read_bytes())-8192)])
asm='''org 0de80h
input_hook:
 call 0d0c7h
 push af
 push bc
 push de
 push hl
 push ix
 in a,(0aah)
 ld d,a
 and 0f0h
 out (0aah),a
 in a,(0a9h)
 ld e,a
 ld a,d
 and 0f0h
 or 1
 out (0aah),a
 in a,(0a9h)
 ld c,a
 ld a,d
 out (0aah),a
 ld a,(0caf9h)
 bit 5,e
 jr nz,c6
 xor a
c6: bit 6,e
 jr nz,c7
 ld a,1
c7: bit 7,e
 jr nz,c8
 ld a,2
c8: bit 0,c
 jr nz,colors_done
 ld a,3
colors_done:
 ld (0caf9h),a
 ld a,(0dff0h)
 bit 1,e
 jr nz,b2
 xor a
b2: bit 2,e
 jr nz,b3
 ld a,1
b3: bit 3,e
 jr nz,music_chosen
 ld a,2
music_chosen:
 ld hl,0dff0h
 cp (hl)
 jr z,done
 ld (hl),a
 call load_song
done:
 pop ix
 pop hl
 pop de
 pop bc
 pop af
 ret
load_song:
 call 0d606h
 ld a,(0dff0h)
 add a,a
 ld e,a
 ld d,0
 ld hl,tables
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 push de
 pop ix
 in a,(0fch)
 push af
 ld a,(0ee23h)
 out (0fch),a
 ld de,0100h
copy_next:
 ld a,(ix+0)
 or a
 jr z,copied
 ld (06000h),a
 ld l,(ix+1)
 ld h,(ix+2)
 ld c,(ix+3)
 ld b,(ix+4)
 ldir
 ld bc,5
 add ix,bc
 jr copy_next
copied:
 pop af
 out (0fch),a
 ld a,255
 ld (06000h),a
 call 0d603h
 ; Sample simulation timer immediately after the bounded transfer.
 call 0d600h
 ret
tables:
 dw song0,song1,song2
'''
for i,parts in enumerate(chunks):
 asm+=f'song{i}:\n'
 for b,a,n in parts:asm+=f' db {b}\n dw {a},{n}\n'
 asm+=' db 0\n'
asm+=''' defs 0df60h-$,0ffh
title_hook:
 push af
 push bc
 push de
 push hl
 ld a,200
 ld (06000h),a
 call 06500h
 ld a,255
 ld (06000h),a
 pop hl
 pop de
 pop bc
 pop af
 jp 0c4a6h
 defs 0dff0h-$,0ffh
 db 2
'''
(W/'radio.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'radio.asm'),str(W/'radio.bin'),str(W/'radio.sym')],check=True)
code=(W/'radio.bin').read_bytes();assert len(code)<=0x180
phys=lambda a:(1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 d=R/('outputs/bonnet-wide-test'+suffix);src=next(d.glob('*.rom'));old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((d/'manifest.json').read_text())['sha256'];rom=bytearray(old);allowed=set()
 def put(at,data,expected):
  assert old[at:at+len(data)]==expected,(hex(at),old[at:at+len(data)].hex()[:80]);rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 for at,data in payload:put(at,data,bytes([255])*len(data))
 put(phys(0xde80),code,bytes([255])*len(code))
 put(0xe9a7,bytes.fromhex('cd80de'),bytes.fromhex('cdc7d0'))
 # Car selector now reads the shared selection; keys5..8 handled at input.
 at=215*16384+8192+0x1580
 jump=0x7580+old[at:at+80].index(bytes.fromhex('47 3a fa ca'))
 put(at,bytes.fromhex('3af9cac3')+jump.to_bytes(2,'little'),bytes.fromhex('dbaa57e6f0d3'))
 # 75A9 is the LD B,A immediately after the legacy selected store.
 assert old[at+jump-0x7580]==0x47
 hb=200*16384+8192
 put(0xe409,bytes.fromhex('c360df'),bytes.fromhex('c3a6c4'))
 for l in (W/'menu.ihx').read_text().splitlines():
  b=bytes.fromhex(l[1:]);assert sum(b)%256==0
  if b[3]==0:
   a=int.from_bytes(b[1:3],'big');data=b[4:-1];assert 0x6500<=a and a+len(data)<0x6b00;put(hb+a-0x6000,data,bytes([255])*len(data))
 # Confirm every song reconstructs exactly from the new ROM.
 for i,parts in enumerate(chunks):assert b''.join(rom[b*16384+a-0x4000:b*16384+a-0x4000+n] for b,a,n in parts)==(R/f'assets/radio/bgm{i+1}.opz').read_bytes()
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/radio-menu'+suffix);out.mkdir(exist_ok=True);(out/src.name).write_bytes(rom)
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),bytes=len(rom),radio_state=0xdff0,colors_state=51961,song_chunks=chunks,scope='Title radio/color menu and keys123/5678 only; camera/bonnet/physics preserved.'),indent=2));print(out)
