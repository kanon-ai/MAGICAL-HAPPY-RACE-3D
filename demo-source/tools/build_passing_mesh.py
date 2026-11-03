"""Isolated third-lane road renderer; traffic/props integration is still pending."""
from pathlib import Path
import json, subprocess, hashlib,sys
STRUCTURES="--structures" in sys.argv
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-'+('drive-structures-carfix2' if STRUCTURES else 'road-uv-preserved')+suffix)
 out=R/('outputs/six-route-'+('passing-structures' if STRUCTURES else 'passing-mesh')+suffix);out.mkdir(exist_ok=True)
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 index=0x8d if suffix else 0x9d;data=index+2
 def assemble(name,text):
  (out/(name+'.asm')).write_text(text)
  subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/(name+'.asm')),str(out/(name+'.bin'))],check=True)
  return (out/(name+'.bin')).read_bytes()
 # Scratch: F610..F6C3 extra vertices; F6ED original width, EE/EF delta,
 # F6F0 row count, F6F1 active, F6F2 displayed width, F6F3 current fraction.
 helper=(R/'src/passing_layout.asm').read_text()+f'''
 defs 06070h-$,0
prepare_row:
 ld a,(ix+5)
 ld (0f6f2h),a
 ld a,(0f6edh)
 ld l,a
 ld h,0
 ld de,08c35h
 add hl,de
 ld e,(hl)
 ld d,0
 sla e
 rl d
 sla e
 rl d
 ld hl,(0e247h)
 ld a,(0e24fh)
 call 06000h
 ld (0f6f3h),a
 ld c,a
 ld a,(0f6f2h)
 db 0edh,0c9h
 ; delta=floor(displayed_width * fraction * 5 /128).
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,de
 ld b,7
delta_shift:
 srl h
 rr l
 djnz delta_shift
 ld (0f6eeh),hl
 ; Save the extra divider in a separate vertex pool, never city vertex9.
 ld a,(0f6f0h)
 ld c,12
 db 0edh,0c9h
 ld de,0f610h
 add hl,de
 push hl
 ld a,(0f6f2h)
 ld e,a
 ld d,0
 srl a
 srl a
 ld l,a
 ld h,0
 add hl,de
 ld de,(0e811h)
 add hl,de
 ex de,hl
 pop hl
 ld a,(0f6f2h)
 srl a
 srl a
 srl a
 srl a
 srl a
 srl a
 inc a
 ld c,a
 ld a,(0f6f3h)
 cp 16
 jr nc,stripe_visible
 ld c,0
 jr stripe_ready
stripe_visible:
 ld a,1
 ld (0f6f1h),a
stripe_ready:
 call store_vertex
 ld a,e
 add a,c
 ld e,a
 jr nc,no_carry
 inc d
no_carry:
 call store_vertex
 ld hl,0f6f0h
 inc (hl)
 ret
store_vertex:
 ld (hl),e
 inc hl
 ld (hl),d
 inc hl
 ld a,(0e813h)
 neg
 ld (hl),a
 inc hl
 sbc a,a
 ld (hl),a
 inc hl
 ld (hl),1
 inc hl
 ld (hl),0
 inc hl
 ret
 defs 06140h-$,0
draw_divider:
 ld a,(0f6f1h)
 or a
 ret z
 ; Preserve original screen-space matrices and destination from road RUN.
 ld a,040h
 out ({index}),a
 ld a,180
 out ({data}),a
 ld a,050h
 out ({index}),a
 ld hl,0f610h
 ld a,(0f6f0h)
 ld c,12
 db 0edh,0c9h
 ld b,l
 ld hl,0f610h
upload_vertices:
 ld a,(hl)
 out ({data}),a
 inc hl
 djnz upload_vertices
 ld a,058h
 out ({index}),a
 ld a,136
 out ({data}),a
 ld a,052h
 out ({index}),a
 ld a,(0f6f0h)
 dec a
 ld b,a
 ld hl,0e7deh
 ld e,180
faces:
 ld a,(hl)
 inc hl
 and 1
 jr z,blank_face
 ld a,e
 out ({data}),a
 inc a
 out ({data}),a
 add a,2
 out ({data}),a
 dec a
 out ({data}),a
 jr attributes
blank_face:
 ld a,e
 out ({data}),a
 out ({data}),a
 out ({data}),a
 out ({data}),a
attributes:
 xor a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 ld a,15
 out ({data}),a
 inc e
 inc e
 djnz faces
 ld a,054h
 out ({index}),a
 ld a,180
 out ({data}),a
 xor a
 out ({data}),a
 ld a,136
 out ({data}),a
 xor a
 out ({data}),a
 ld a,042h
 out ({index}),a
 ld a,(0f6f0h)
 add a,a
 out ({data}),a
 ld a,059h
 out ({index}),a
 ld a,(0f6f0h)
 dec a
 out ({data}),a
 ld a,048h
 out ({index}),a
 ld a,7
 out ({data}),a
wait_divider:
 in a,({index})
 rrca
 jr nc,finished
 call 0cacbh
 jr wait_divider
finished:
 ld a,054h
 out ({index}),a
 xor a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 out ({data}),a
 ret
'''
 code=assemble('passing-mesh',helper);assert len(code)<8192
 at=208*16384+8192;assert old[at:at+8192]==bytes([255])*8192
 rom[at:at+len(code)]=code
 tramp='''org 09568h
capture_width:
 ld (ix-4),c
 ld a,c
 ld (0f6edh),a
 ld a,(ix-1)
 or a
 ret nz
 ld (0f6f0h),a
 ld (0f6f1h),a
 ld (0f6eeh),a
 ld (0f6efh),a
 ld (0f6f4h),a
 ld a,(0e24fh)
 and 7
 cp 2
 jr z,enable_mesh
 cp 3
 jr z,enable_mesh
 cp 1
 ret nz
 push hl
 push de
 ld hl,(0e247h)
 ld de,15364
 or a
 sbc hl,de
 pop de
 pop hl
 ret c
enable_mesh:
 ld a,1
 ld (0f6f4h),a
 ret
row_prepare:
 push af
 ld a,(0f6f4h)
 or a
 jr nz,prepare_active
 pop af
 jp 0daf0h
prepare_active:
 push bc
 push de
 push hl
 ld a,208
 ld (06000h),a
 call 06070h
 pop hl
 pop de
 pop bc
 pop af
 jp 0daf0h
near_row:
 xor a
 ld (0f6edh),a
 jp 08d74h
shift_vertex:
 add hl,bc
 jr nz,shift_done
 ld a,e
 cp 9
 jr z,shift_right
 cp 8
 jr z,shift_right
 cp 7
 jr z,shift_right
 cp 4
 jr z,shift_right
 cp 3
 jr nz,shift_done
shift_right:
 push de
 ld de,(0f6eeh)
 add hl,de
 pop de
shift_done:
 ld a,e
 cp 6
 ret
end_road:
 ld a,208
 ld (06000h),a
 call 06140h
 ld a,252
 ld (06000h),a
 ld sp,ix
 pop ix
 ret
'''
 # Use assembler symbol file for guarded patch addresses.
 (out/'passing-tramp.asm').write_text(tramp)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'passing-tramp.asm'),str(out/'passing-tramp.bin'),str(out/'passing-tramp.sym')],check=True)
 symbols={x.split()[0]:int(x.split()[2].rstrip('H'),16) for x in (out/'passing-tramp.sym').read_text().splitlines()}
 body=(out/'passing-tramp.bin').read_bytes();assert 0x9568+len(body)<=0x96ac
 assert old[off(0x9568):off(0x9568)+len(body)]==bytes(len(body))
 rom[off(0x9568):off(0x9568)+len(body)]=body
 patches=[(0x9098,'dd71fc','capture_width',0xcd),(0x8da7,'cdf0da','row_prepare',0xcd),(0x9244,'cd748d','near_row',0xcd),(0x8dd2,'097bfe06','shift_vertex',0xcd),(0x9723,'ddf9dd','end_road',0xc3)]
 for addr,expected,label,opcode in patches:
  expected=bytes.fromhex(expected);at=off(addr);assert old[at:at+len(expected)]==expected,(hex(addr),old[at:at+len(expected)].hex())
  rom[at:at+len(expected)]=bytes([opcode])+symbols[label].to_bytes(2,'little')+bytes(len(expected)-3)
 assert rom[off(0x96ac):off(0x96ac)+16]==old[off(0x96ac):off(0x96ac)+16]
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),trampoline_bytes=len(body),playable_adoption=False,pending='Traffic, offroad limits, right-side props, mirror and runtime validation'),indent=2))
 print(out.name,len(code),len(body),flush=True)
