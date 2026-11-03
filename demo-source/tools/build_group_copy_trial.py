from pathlib import Path
import re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text());base=R/'outputs/six-route-trial-lined-dedup';sym={n:int(v,16) for n,v in re.findall(r'(\w+)\s+EQU\s+0([0-9A-F]+)H',(base/'decoder.sym').read_text())};decoder=(base/'decoder.bin').read_bytes();start=sym['load_group']-0xf000;at=start+decoder[start:start+20].index(bytes.fromhex('110000edb0'));addr=S['_bgm_poll']+3;out=R/'outputs/six-route-group-copy';out.mkdir(exist_ok=True)
asm=f'''org {addr}
 push af
 ld de,0
 ld a,c
 and 7
 jr z,bulk_check
remainder:
 ldi
 dec a
 jr nz,remainder
bulk_check:
 ld a,b
 or c
 jr z,done
bulk:
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 jp pe,bulk
done:
 pop af
 ret
'''
(out/'copy.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'copy.asm'),str(out/'copy.bin')],check=True);code=(out/'copy.bin').read_bytes();assert len(code)<=49
physical=(1+(addr-0x8000)//8192)*16384+8192+(addr-0x8000)%8192
for suf,n in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-poll-shared'+suf);o=R/('outputs/six-route-group-copy'+suf);o.mkdir(exist_ok=True);rom=bytearray((src/n).read_bytes());assert rom[8192:8192+len(decoder)]==decoder;assert rom[physical:physical+49]==bytes(49)
 rom[physical:physical+len(code)]=code;rom[8192+at:8192+at+5]=bytes([0xcd])+addr.to_bytes(2,'little')+bytes(2);(o/n).write_bytes(rom)
 for a in ['city-atlas.bin','night-atlas.bin']:(o/a).write_bytes((src/a).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),runtime_verified=False),indent=2))
print('Helper bytes',len(code))
