from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-arcade-title'+suffix);O=R/('outputs/six-route-night-boulevard'+suffix);O.mkdir(exist_ok=True)
 b=bytearray((src/name).read_bytes());old=bytes(b);at=3*16384+8192+0x1bac
 code=bytes(b[at:at+46]);pattern=bytes.fromhex('fe28dd7ef8');assert code.count(pattern)==1
 i=code.index(pattern)+1;b[at+i]=41
 assert sum(x!=y for x,y in zip(b,old))==1
 city=(src/'city-atlas.bin').read_bytes();night=(src/'night-atlas.bin').read_bytes()
 for row in range(128,192):assert city[row*256+192:row*256+256]==night[row*256+192:row*256+256]
 (O/name).write_bytes(b)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),changed_bytes=1,world_piece_tree_limit=41,shared_tree_pixels_exact=True,scope='Retain city identity1 trees into world piece40; no object count/geometry changes; native preview pending'),indent=2))
 print(O)
