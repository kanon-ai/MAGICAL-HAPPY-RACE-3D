from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-forest-shade'+suffix);out=R/('outputs/six-route-forest-mix'+suffix);out.mkdir(exist_ok=True)
 asm='''org 03880h
 ld a,(ix-8)
 cp 2
 ld a,5
 jr nc,store
 ld l,(ix-12)
 ld h,(ix-11)
 bit 5,(hl)
 ld a,4
 jr z,store
 ld a,5
store:
 ld (ix-8),a
 defs 0389bh-$,0
'''
 (out/'mix.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'mix.asm'),str(out/'mix.bin')],check=True)
 code=(out/'mix.bin').read_bytes();assert len(code)==27
 rom=bytearray((src/name).read_bytes());at=214*16384+8192+0x1480
 assert rom[at:at+5]==bytes.fromhex('dd7ef8d602');rom[at:at+27]=code
 (out/name).write_bytes(rom)
 for a in ['city-atlas.bin','night-atlas.bin']:(out/a).write_bytes((src/a).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),scope='Forest only: world-encoded left-side vegetation uses broadleaf canopy. Object count and placement unchanged.',runtime_verified=False),indent=2))
