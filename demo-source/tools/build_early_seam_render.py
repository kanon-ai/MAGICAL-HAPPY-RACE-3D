"""Early two-stage feather overlay using isolated stack decoder and existing VRAM strip."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-early-seam-decode'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);out=R/('outputs/six-route-early-seam-render'+suffix);out.mkdir(exist_ok=True)
 control=0x89 if suffix else 0x99;vram=control-1
 oldasm=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.asm').read_text()
 head=oldasm[oldasm.index(' ; Original'):oldasm.index(f' ld a,({S["_scene_target"]})')]
 fallback=f'''org 07100h
 ld a,({S['_scene_target']})
 cp 1
 jr z,early
 cp 2
 jr z,early
 ld (0f6d0h),hl
 ld (0f6d2h),de
 ld hl,4
 add hl,sp
 ld c,(hl)
 inc hl
 ld b,(hl)
 ld (0f6d4h),bc
 push ix
 ld hl,-32
 add hl,sp
 ld sp,hl
 push hl
 pop ix
 ex de,hl
 ld hl,legacy_thunk
 ld bc,legacy_end-legacy_thunk
 ldir
 ld bc,(0f6d4h)
 push bc
 ld hl,legacy_return
 push hl
 ld hl,(0f6d0h)
 ld de,(0f6d2h)
 jp (ix)
legacy_return:
 inc sp
 inc sp
 ld hl,32
 add hl,sp
 ld sp,hl
 pop ix
 ret
legacy_thunk:
 ld a,201
 ld (06000h),a
 call 06000h
 ld a,211
 ld (06000h),a
 ret
legacy_end:
early:
'''
 cache=oldasm[oldasm.index('band:\n'):oldasm.index(' ld l,a\n ld h,0\n',oldasm.index('cache_ordered:'))]
 cache=cache.replace('add a,52\n srl a\n srl a\n srl a','add a,56\n srl a\n srl a\n srl a\n srl a')
 cache=cache.replace(' ld c,a\n ld a,(0dbeah)',f' ld c,a\n ld a,({S["_scene_target"]})\n cp 2\n ld a,c\n jr nz,key_ready\n add a,7\nkey_ready:\n ld c,a\n ld a,(0dbeah)')
 cache=cache.replace('jr z,clip_band','jp z,clip_band')
 upload=f''' push ix
 ld hl,07500h
 ld de,78
 ld b,c
 ld a,b
 or a
 jr z,table_ready
table_step:
 add hl,de
 djnz table_step
table_ready:
 push hl
 pop ix
 call {S['_gfx_wait']}
 ld a,11
 out ({control}),a
 ld a,08eh
 out ({control}),a
 ld b,26
upload_row:
 push bc
 ld a,(ix+0)
 ld l,(ix+1)
 ld h,(ix+2)
 inc ix
 inc ix
 inc ix
 call 07000h
 pop bc
 push bc
 ld a,26
 sub b
 add a,34
 ld d,a
 xor a
 out ({control}),a
 ld a,d
 or 040h
 out ({control}),a
 ld hl,0f400h
 ld bc,{72*256+vram}
 otir
 call {S['_bgm_poll']}
 pop bc
 djnz upload_row
 pop ix
'''
 tail=oldasm[oldasm.index('clip_band:\n'):oldasm.index('colors:')]
 tail=tail.replace('ld hl,240','ld hl,244').replace('ld b,32','ld b,24').replace('ld a,32','ld a,24').replace('cp 225','cp 233').replace('add a,192','add a,0').replace('ld de,39','ld de,26').replace('ld hl,39','ld hl,26').replace('ld de,650','ld de,738').replace('add a,32','add a,24')
 tail=tail.replace(' jp draw_half\ndraw_half:', ''' call draw_half
 ld hl,(0f6d2h)
 ld de,26
 add hl,de
 ld (0f6d2h),hl
 ld a,(0f6d9h)
 add a,24
 ld (0f6d9h),a
 jp draw_half
draw_half:''')
 asm=fallback+head+cache+upload+tail
 (out/'render.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'render.asm'),str(out/'render.bin'),str(out/'render.sym')],check=True)
 code=(out/'render.bin').read_bytes();assert len(code)<=1024
 at=211*16384+8192+0x1100;assert old[at:at+len(code)]==b'\xff'*len(code);rom[at:at+len(code)]=code
 hook=3*16384+8192+0x1bda;assert old[hook:hook+16]==bytes.fromhex('3ec9320060cd00603efc320060e1c1e9');rom[hook+1]=211;rom[hook+7]=0x71
 assert len(rom)==4194304
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps({'bytes':len(rom),'helper_bytes':len(code),'sha256':hashlib.sha256(rom).hexdigest(),'scope':'Early two transitions only. Native render validation pending.'},indent=2));print(suffix,len(code))
