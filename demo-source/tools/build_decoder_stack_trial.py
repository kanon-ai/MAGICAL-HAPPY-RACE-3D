from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1]
for suffix,name,expected in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom','d1aa7954d3507ef3a6ed1217f574395bbe63aee4a5997abfe4d91fd7b4064bf1'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom','735f0555a6f659b77f8d25300e325cf417682d3d9178e3e888f04549e248497e')]:
 source=R/f'outputs/six-route-building-vertices{suffix}';O=R/f'outputs/six-route-decoder-stack{suffix}';O.mkdir(exist_ok=True)
 rom=bytearray((source/name).read_bytes());assert hashlib.sha256(rom).hexdigest()==expected
 asm="""org 0f126h
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
 ld a,(0f1bch)
 call 0f159h
 pop hl
 pop bc
 add a,b
 jp 0f144h
"""
 (O/'stack.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'stack.asm'),str(O/'stack.bin')],check=True)
 code=(O/'stack.bin').read_bytes();assert len(code)<=30,len(code)
 old=(R/'outputs/six-route-trial/decoder.bin').read_bytes()[0x126:0x144];at=8192+0x126;assert rom[at:at+30]==old
 rom[at:at+30]=code+bytes(30-len(code));(O/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((source/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=expected,sha256=hashlib.sha256(rom).hexdigest(),patch_bytes=30,stack_extra_bytes=2,scope='Variable descriptor base stored on stack instead of RAM. Native verification pending.'),indent=2));print(O)
