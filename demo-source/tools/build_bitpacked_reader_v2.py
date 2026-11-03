"""Relocate the entire legacy loop, including its internal branch targets."""
from pathlib import Path
p=Path(__file__).with_name('build_bitpacked_reader.py')
s=p.read_text().replace('work/bitpacked-reader','work/bitpacked-reader-v2').replace('six-route-bitpacked-reader','six-route-bitpacked-reader-v2')
start=s.index("reader='''");end=s.index("(W/'reader.asm')",start)
s=s[:start]+'''legacy=next((R/'outputs/six-route-snow-city-ground').glob('*.rom')).read_bytes()[8192+0x166:8192+0x1bc]
assert len(legacy)==86 and legacy[:3]==bytes.fromhex('4f237e')
# Original token loop branches back to F168, inside the three-byte hook.
# Copy the complete original loop so every relative jump keeps its target.
reader="org 01f00h\\n bit 7,(hl)\\n jp nz,bitpacked_sample\\n db "+','.join(map(str,legacy))+"\\n"+(R/'tools/bitpacked_sample.asm').read_text()
'''+s[end:]
s=s.replace("old=p.read_bytes();rom=bytearray(old);allowed=set()","old=p.read_bytes();assert old[8192+0x166:8192+0x1bc]==legacy;rom=bytearray(old);allowed=set()")
exec(compile(s,str(p),'exec'))
