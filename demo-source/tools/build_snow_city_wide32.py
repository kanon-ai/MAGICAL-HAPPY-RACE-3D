"""Isolated target4 32px feather, retaining original render/decode for other joins."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];W=R/'work/snow-city-wide32';W.mkdir(exist_ok=True)
plan=json.loads((R/'outputs/snow-city-wider-band-plan.json').read_text())
rows=json.loads((R/'assets/snow-city-transition-study/snow-city-32.json').read_text())
data=(R/'assets/snow-city-transition-study/snow-city-32.rle').read_bytes()
raw=(R/'assets/snow-city-transition-study/snow-city-32.raw').read_bytes()
def assemble(name,source):
    p=W/(name+'.asm');p.write_text(source)
    subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(p),str(p.with_suffix('.bin'))],check=True)
    return p.with_suffix('.bin').read_bytes()
decoder=(R/'src/early_seam_decode.asm').read_text().replace('org 07000h','org 07e00h').replace('cp 72','cp 96')
decode=assemble('decode96',decoder);assert len(decode)<=256
for suffix in ('','-external-88h'):
    src=R/('outputs/six-route-snow-city-trees'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=bytearray(len(rom))
    if not suffix:assert hashlib.sha256(old).hexdigest()==plan['source_sha256']
    def at(address):return 211*16384+address-0x4000
    def write(start,blob,expected=None):
        end=start+len(blob);assert not any(written[start:end])
        if expected is not None:assert old[start:end]==expected,(hex(start),'occupied')
        rom[start:end]=blob;written[start:end]=b'\1'*len(blob)
    pointers={}
    for item in plan['widths']['32']['placements']:
        i=item['row'];row=rows[i];blob=data[row['offset']:row['offset']+row['bytes']]
        assert len(blob)==item['bytes'];write(item['at'],blob)
        pointers[i]=bytes([item['at']//16384])+(0x4000+item['at']%16384).to_bytes(2,'little')
    directory=b''.join(pointers[i] for i in range(182));assert len(directory)==546
    write(at(0x7944),directory)
    prior=R/('outputs/six-route-snow-city-feather'+suffix)
    original=(prior/'render.bin').read_bytes();assert old[at(0x7100):at(0x7100)+len(original)]==original
    asm=(prior/'render.asm').read_text()
    prefix='org 07c00h\n ld a,(60649)\n cp 4\n jp nz,07103h\n'
    asm=asm.replace('org 07100h',prefix).replace('call 07000h','call 07e00h').replace('cp 12','cp 16').replace('ld a,12','ld a,16').replace('add a,24','add a,32')
    port=0x88 if suffix else 0x98
    assert f'ld bc,{72*256+port}' in asm
    asm=asm.replace(f'ld bc,{72*256+port}',f'ld bc,{96*256+port}')
    renderer=assemble('render32'+suffix,asm);assert len(renderer)<=512
    write(at(0x7c00),renderer,b'\xff'*len(renderer))
    write(at(0x7e00),decode,b'\xff'*len(decode))
    write(at(0x7100),bytes.fromhex('c3007c'),bytes.fromhex('3ae9ec'))
    # Decode every installed row through actual ROM directory pointers.
    for i in range(182):
        ptr=rom[at(0x7944)+3*i:at(0x7944)+3*i+3];pos=ptr[0]*16384+int.from_bytes(ptr[1:],'little')-0x4000;out=bytearray()
        while len(out)<96:
            token=rom[pos];pos+=1;n=(token&127)+1
            if token&128:out.extend(bytes([rom[pos]])*n);pos+=1
            else:out.extend(rom[pos:pos+n]);pos+=n
        assert out==raw[i*96:(i+1)*96]
    assert len(rom)==4194304 and all(a==b or written[i] for i,(a,b) in enumerate(zip(old,rom)))
    out=R/('outputs/six-route-snow-city-wide32'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
    for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),renderer_bytes=len(renderer),decoder_bytes=len(decode),all182_rows_exact=True,native_verified=False,scope='Target4 only width32; other joins original width24'),indent=2))
    print(out.name,len(renderer),len(decode))
