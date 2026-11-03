from pathlib import Path
p=Path(__file__).with_name('build_snow_city_turn.py')
s=p.read_text().replace('outputs/six-route-snow-city-turn','outputs/six-route-snow-city-turn-upper-markers')
exec(compile(s,str(p),'exec'))
