from pathlib import Path
p=Path(__file__).with_name('build_forest_grove_art.py')
s=p.read_text().replace('forest-grove-art-v1','forest-grove-understory-v2').replace("R/'assets/forest-atlas.bin'","R/'assets/forest-grove-art-v1/forest-atlas.bin'").replace('six-route-forest-groves','six-route-early-seam-taper').replace('six-route-forest-grove-art','six-route-grove-understory')
exec(compile(s,str(p),'exec'))
