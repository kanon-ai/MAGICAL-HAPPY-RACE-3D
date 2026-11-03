from pathlib import Path
p=Path(__file__).with_name('build_city_alpine_preview.py')
s=p.read_text().replace('city-alpine-v1','city-alpine-v2').replace('city-alpine-preview','city-alpine-v2-preview')
exec(compile(s,str(p),'exec'))
