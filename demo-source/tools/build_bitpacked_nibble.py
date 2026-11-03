from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
for port in ('internal','external'):
 proof=json.loads((R/f'outputs/bitpacked-nibble-native/{port}/validation.json').read_text())
 assert proof['all_samples_exact'] and proof['preserved_registers_and_stack_exact'] and proof['widths']==[4]
p=Path(__file__).with_name('build_bitpacked_reader_v2.py')
s=p.read_text().replace('bitpacked-reader-v2','bitpacked-nibble-reader').replace('tools/bitpacked_sample.asm','tools/bitpacked_sample_nibble.asm')
exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_bitpacked_columns.py')
s=p.read_text().replace('bitpacked-reader-v2','bitpacked-nibble-reader').replace('six-route-bitpacked-columns','six-route-bitpacked-nibble')
s=s.replace('if len(blob)>=n:continue','if len(blob)>=n or blob[0]!=0x84:continue')
exec(compile(s,str(p),'exec'))
