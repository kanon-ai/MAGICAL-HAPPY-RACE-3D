"""Convert generated city art to the existing, unchanged SCREEN8 palette."""
from pathlib import Path
from types import SimpleNamespace
import re,json,hashlib
from PIL import Image,ImageChops
from quantization import indexed
R=Path(__file__).resolve().parents[1]
source=R/'assets/city-source/city-panorama-v3.png'
values=[int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{',1)[1].split('}',1)[0])]
assert len(values)==768
palette=[round(v*255/31) for v in values]
original=Image.open(source).convert('RGB')
native=original.resize((256,78),Image.Resampling.LANCZOS)
# Restore horizontal origin after center-seam image generation.
native=ImageChops.offset(native,128,0)
# Match the extended chase sky at the top edge without changing its palette.
pixels=native.load();sky=tuple(palette[158*3:158*3+3])
for y in range(16):
    t=y/15
    for x in range(256):pixels[x,y]=tuple(round(sky[k]*(1-t)+pixels[x,y][k]*t) for k in range(3))
native=indexed(native,SimpleNamespace(FLAT=palette,CAR_COLORS={}),car=True)
out=R/'assets/city-sky.bin';out.write_bytes(native.tobytes())
assert len(out.read_bytes())==19968
native.save(R/'assets/city-source/city-native.png')
native.resize((1024,312),Image.Resampling.NEAREST).save(R/'assets/city-source/city-preview.png')
report=dict(source=source.name,native_size=[256,78],rom_bytes=19968,
            palette_unchanged=True,quantizer='Oklab nearest existing RGB555 palette',
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            data_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),integrated_in_game=False)
(R/'assets/city-source/conversion.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
