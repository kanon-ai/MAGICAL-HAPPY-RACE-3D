"""Offline forest-only lateral depth variant, preserving road/traffic/mirror."""
from pathlib import Path
p=Path(__file__).with_name('generate_forest_groves.py')
s=p.read_text()
s=s.replace("O=R/'work/forest-groves/forest'", "O=R/'work/forest-roadside-depth/forest'")
old='(1600,1900,4200,5000,3200,1800,1600,3800)'
assert s.count(old)==1
s=s.replace(old,'(1100,1600,2800,3400,2300,1400,1200,2600)')
s=s.replace("base=R/'work/lined-route-shapes/forest/assets'", "base=R/'work/forest-groves/forest/assets'")
s=s.replace('Offline lateral forest placement only; not integrated or runtime verified', 'Offline forest roadside depth variant; same world objects, closer alternating setbacks; not integrated or runtime verified')
exec(compile(s,str(p),'exec'),{'__file__':str(p)})
