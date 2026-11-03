"""Use the existing degenerate face0 for inland ground beyond the left verge.

No added vertices or face slots. Coast stays degenerate, and restart clears it.
"""
from pathlib import Path
import json,hashlib,subprocess,re
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for external in (False,True):
 suffix='-external-88h' if external else ''
 name='MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom' if external else 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
 source=R/f'outputs/six-route-fast-rock{suffix}'/name;original=source.read_bytes();rom=bytearray(original)
 expected='10c6530f294b1286fddc3e24fdae0b64f584f67be4482be57df671d81286e2f7' if external else 'bc2ba0dbbe0bf20dc614a4704e324bb85e726c09defc4c920907f53b00596277'
 assert hashlib.sha256(original).hexdigest()==expected
 O=R/f'outputs/six-route-inland-ground{suffix}';O.mkdir(exist_ok=True)
 port=0x8d if external else 0x9d
 asm=f"""org 0dac1h
 ; Original cache store, then update the otherwise unused resident face0.
 ld a,(ix-8)
 ld d,a
 ld a,({S['_route_piece']})
 cp 9
 ld a,d
 jr nc,store_cache
 xor 128
store_cache:
 ld (bc),a
 ld a,058h
 out ({port}),a
 ld a,(ix-1)
 add a,a
 add a,a
 add a,a
 out ({port+2}),a
 ld a,052h
 out ({port}),a
 ld a,(ix-9)
 ld e,a
 ld a,({S['_route_piece']})
 cp 9
 jr c,coast
 ld a,e
 out ({port+2}),a
 add a,7
 out ({port+2}),a
 add a,12
 out ({port+2}),a
 sub 7
 out ({port+2}),a
 ld d,(ix-8)
 jr attributes
coast:
 ; Return to exactly the degenerate original face at a new game.
 ld a,e
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 ld d,128
attributes:
 xor a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 out ({port+2}),a
 ld a,d
 out ({port+2}),a
 ret
compare_cache:
 ; Cache high bit distinguishes coast-degenerate and inland-active face0.
 ld a,(hl)
 ld d,a
 ld a,({S['_route_piece']})
 cp 9
 ld a,d
 jr nc,compare_color
 xor 128
compare_color:
 sub (ix-8)
 ret
"""
 (O/'inland-ground.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'inland-ground.asm'),str(O/'inland-ground.bin'),str(O/'inland-ground.sym')],check=True)
 code=(O/'inland-ground.bin').read_bytes();assert len(code)<=168
 helper=3*16384+8192+0x1ac1;assert rom[helper:helper+168]==bytes([255])*168
 patch=16384+8192+0x13ab;assert rom[patch:patch+4]==bytes.fromhex('dd 7e f8 02')
 rom[helper:helper+len(code)]=code;rom[patch:patch+4]=bytes.fromhex('cd c1 da 00')
 sym=(O/'inland-ground.sym').read_text();cmp=int(re.search(r'compare_cache\s+EQU\s+0([0-9A-F]+)H',sym).group(1),16)
 compare_at=16384+8192+0x130d;assert rom[compare_at:compare_at+4]==bytes.fromhex('7e dd 96 f8')
 rom[compare_at:compare_at+4]=bytes([0xcd])+cmp.to_bytes(2,'little')+bytes(1)
 changes=[i for i,(a,b) in enumerate(zip(original,rom)) if a!=b]
 assert all(i in range(helper,helper+len(code)) or i in range(patch,patch+4) or i in range(compare_at,compare_at+4) for i in changes)
 (O/name).write_bytes(rom)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=expected,bytes=len(rom),helper_bytes=len(code),remaining_reclaimed_bytes=168-len(code),scope='Inland left terrain face only; native geometry, coast preservation, restart and FPS validation pending.')
 (O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
