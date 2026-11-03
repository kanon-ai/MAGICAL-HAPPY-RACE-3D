from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
for port in ('internal','external'):
 proof=json.loads((R/f'outputs/bitpacked-mask-native/{port}/validation.json').read_text())
 assert proof['all_samples_exact'] and proof['preserved_registers_and_stack_exact']
p=Path(__file__).with_name('build_bitpacked_reader_v2.py')
s=p.read_text().replace('bitpacked-reader-v2','bitpacked-mask-reader').replace('tools/bitpacked_sample.asm','tools/bitpacked_sample_mask.asm')
exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_bitpacked_columns.py')
s=p.read_text().replace('bitpacked-reader-v2','bitpacked-mask-reader').replace('six-route-bitpacked-columns','six-route-bitpacked-mask')
exec(compile(s,str(p),'exec'))
