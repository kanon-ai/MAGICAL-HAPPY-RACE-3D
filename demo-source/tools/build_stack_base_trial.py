from pathlib import Path
import re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];base=R/'outputs/six-route-trial-lined-dedup';sym={n:int(v,16) for n,v in re.findall(r'(\w+)\s+EQU\s+0([0-9A-F]+)H',(base/'decoder.sym').read_text())};out=R/'outputs/six-route-stack-base';out.mkdir(exist_ok=True)
asm=f'''org {sym['variable']}
 ex af,af'
 ld a,(hl)
 inc hl
 push af
 ld a,(hl)
 inc hl
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 push hl
 ld h,b
 ld l,c
 ld (06000h),a
 ld a,({sym['sample_phase']})
 call {sym['sample']}
 pop hl
 pop bc
 add a,b
 jr store
 defs {sym['store']}-$,0
store:
'''
(out/'base.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'base.asm'),str(out/'base.bin')],check=True);patch=(out/'base.bin').read_bytes();assert len(patch)==sym['store']-sym['variable'];decoder=(base/'decoder.bin').read_bytes();offset=sym['variable']-0xf000
for suf,n in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-poll-shared'+suf);o=R/('outputs/six-route-stack-base'+suf);o.mkdir(exist_ok=True);rom=bytearray((src/n).read_bytes());assert rom[8192:8192+len(decoder)]==decoder
 rom[8192+offset:8192+offset+len(patch)]=patch;(o/n).write_bytes(rom)
 for a in ['city-atlas.bin','night-atlas.bin']:(o/a).write_bytes((src/a).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),changed_region=[sym['variable'],sym['store']],runtime_verified=False),indent=2))
