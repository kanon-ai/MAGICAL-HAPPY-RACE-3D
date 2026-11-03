"""Pack unchanged transition rows across banks, reclaim two halfbanks."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
for suf,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-snow-connected'+suf);out=R/('outputs/six-route-snow-packed'+suf);out.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 asm=(R/('outputs/six-route-forest-snow-taper'+suf)/'bridge.asm').read_text().split('pointers:')[0]
 needle=' ld (06000h),a\n ex de,hl';assert asm.count(needle)==1
 asm=asm.replace(needle,' ld (0f6ech),a\n'+needle)
 needle=' otir\n call ';assert asm.count(needle)==1
 asm=asm.replace(needle,''' otir
 ; Forty complete 192-byte rows fit each bank after the helper.
 bit 7,h
 jr z,row_ready
 ld a,(0f6ech)
 inc a
 ld (0f6ech),a
 ld (06000h),a
 ld hl,06200h
row_ready:
 call ''')
 asm+='pointers:\n'
 for n in range(7):
  row=n*26;asm+=f' db {201+row//40}\n dw {0x6200+(row%40)*192}\n'
 (out/'bridge.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'bridge.asm'),str(out/'bridge.bin')],check=True)
 code=(out/'bridge.bin').read_bytes();assert len(code)<=512
 data=b''.join(before[b*16384+8192+512:b*16384+8192+512+4992] for b in range(201,208));assert len(data)==34944
 for b in range(201,208):rom[b*16384+8192:b*16384+16384]=b'\xff'*8192
 for n,b in enumerate(range(201,206)):
  payload=data[n*7680:(n+1)*7680];block=code+b'\xff'*(512-len(code))+payload
  rom[b*16384+8192:b*16384+16384]=block+b'\xff'*(8192-len(block))
 restored=b''.join(rom[b*16384+8192+512:b*16384+16384] for b in range(201,206))[:len(data)]
 assert restored==data
 assert all(i//16384 in range(201,208) and i%16384>=8192 for i,(a,b) in enumerate(zip(before,rom)) if a!=b)
 assert len(rom)==4194304;(out/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),helper_bytes=len(code),image_bytes=len(data),reserved_bytes=5*8192,reserved_upper_halfbanks=list(range(201,206)),released_upper_halfbanks=[206,207],scratch_byte='F6EC',reclaimed_bytes=16384,images_exact=True,runtime_verified=False),indent=2))
 print(suf,len(code))
