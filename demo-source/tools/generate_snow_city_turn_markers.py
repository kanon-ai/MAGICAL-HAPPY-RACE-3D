from pathlib import Path
p=Path(__file__).with_name('generate_candidate_markers.py')
s=p.read_text().replace("names=('coast','canyon','forest','snow','city','night')","names=('snow','city')")
s=s.replace('reports=[]',"from study_snow_city_turn import paired_curve\ncurves=lambda name:paired_curve(name,8000)\nWORK=R/'work/snow-city-turn'\nreports=[]")
exec(compile(s,str(p),'exec'))
