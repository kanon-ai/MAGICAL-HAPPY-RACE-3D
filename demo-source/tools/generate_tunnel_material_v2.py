"""Material-specific neutral lighting/palette conversion; original AI asset preserved."""
from pathlib import Path
import re,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'assets/tunnel-material-v2';O.mkdir(exist_ok=True)
source=R/'assets/tunnel-material-v1/concrete-source.png'
a=np.asarray(Image.open(source).convert('RGB').resize((64,14),Image.Resampling.LANCZOS),dtype=float)
luma=a@np.array([.2126,.7152,.0722]);target=np.clip(70+(luma-luma.mean())*.65,58,82)
pal=[round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
indices=np.array([200,198,190,188]);levels=np.array([58,66,74,82])
idx=indices[np.argmin(abs(target[:,:,None]-levels),axis=2)].astype('uint8')
im=Image.fromarray(idx);im.putpalette(pal);im.save(O/'concrete-64x14.png');(O/'concrete-64x14.bin').write_bytes(idx.tobytes())
(O/'conversion.json').write_text(json.dumps(dict(source=str(source),size=[64,14],palette_indices=indices.tolist(),lighting_mean=70,contrast=.65,no_dither=True),indent=2))
