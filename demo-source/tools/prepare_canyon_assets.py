"""Stage-specific scenery atlas, preserving player and water texture regions."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import re,json,hashlib
from quantization import indexed
R=Path(__file__).resolve().parents[1]
values=[int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{',1)[1].split('}',1)[0])]
palette=[round(v*255/31) for v in values];excluded={i:1 for i in range(1,256) if (palette[i*3]>palette[i*3+1]*1.6 and palette[i*3]-palette[i*3+1]>64) or (palette[i*3+1]>palette[i*3+2]*3 and palette[i*3+1]>palette[i*3]*.6)}
art=SimpleNamespace(FLAT=palette,CAR_COLORS=excluded)
base=(R/'assets/scaled-atlas.bin').read_bytes()
atlas=Image.frombytes('P',(256,256),base);atlas.putpalette(palette)
facades=Image.open(R/'assets/canyon-source/canyon-rock-v1.png').convert('RGB')
w,h=facades.size;mx=w//2;my=round(h*.475)
boxes=[(0,0,mx,my),(mx,0,w,my),(0,my,mx,h),(mx,my,w,h)]
tiles=[indexed(facades.crop(box).resize((64,64),Image.Resampling.LANCZOS),art,car=False) for box in boxes]
for x,tile in zip((0,64,128,192),tiles):atlas.paste(tile,(x,0))
atlas.paste(tiles[3],(0,64))
data=atlas.tobytes();assert len(data)==65536
for y in range(128,256):
    assert data[y*256+80:y*256+192]==base[y*256+80:y*256+192], 'Player/water texture changed'
(R/'assets/canyon-atlas.bin').write_bytes(data)
atlas.resize((768,768),Image.Resampling.NEAREST).save(R/'assets/canyon-source/canyon-atlas-preview.png')
(R/'assets/canyon-source/atlas-report.json').write_text(json.dumps(dict(
    bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),palette_unchanged=True,
    player_and_water_preserved=True,facade_tiles=4,rock_tiles=4,
    integrated_in_game=False),indent=2))
print('Prepared 64 KiB canyon atlas; player/water unchanged; not yet streamed by game.')
