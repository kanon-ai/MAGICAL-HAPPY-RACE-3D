from pathlib import Path
p=Path(__file__).with_name('prepare_forest_grove_art.py')
s=p.read_text().replace('forest-grove-art-v1','forest-grove-understory-v2')
exec(compile(s,str(p),'exec'))
