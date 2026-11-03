"""Unadopted render-only ROM trial; exact source bytes and placements guarded."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
    w=R/('work/traffic-near-render'+suffix)
    out=R/('outputs/six-route-traffic-near-clip-v2'+suffix);out.mkdir(exist_ok=True)
    entry=int(re.search(r'([0-9A-F]{8})\s+_draw_near_car\s',(w/'render.map').read_text())[1],16)
    # Entry hook saves original AF. HL contains clip in L and must survive guards.
    asm=f'''org 07800h
 push hl
 ld a,(60249)
 cp 254
 jr z,ordinary
 ld a,(60246)
 or a
 jr nz,ordinary
 ld hl,(60628)
 bit 7,h
 jr nz,near
 ld a,h
 or a
 jr nz,ordinary
 ld a,l
 cp 13
 jr nc,ordinary
near:
 pop hl
 pop af
 call {entry}
 jp 0dac9h
ordinary:
 pop hl
 pop af
 ; Resident return restores the mapping after original renderer completes.
 push hl
 ld hl,0dac9h
 ex (sp),hl
 ; Replay exact displaced prologue, then continue at VIEWRAM2A6A.
 db 0ddh,0e5h,0ddh,021h,0,0,0ddh,039h,0f5h,0ddh,077h,0ffh
 jp 02a6ah
'''
    (out/'gate.asm').write_text(asm)
    subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'gate.asm'),str(out/'gate.bin')],check=True)
    gate=(out/'gate.bin').read_bytes();assert len(gate)<0x100
    path=next((R/('outputs/six-route-snow-roadside-depth'+suffix)).glob('*.rom'))
    old=path.read_bytes();assert old[64201:64207]==bytes.fromhex("3efc320060c9");rom=bytearray(old);bank=206*16384+8192;written=set()
    def put(a,data):
        for i,v in enumerate(data):
            at=bank+a-0x6000+i
            assert 0x6900<=a+i<0x8000 and old[at]==255 and at not in written
            written.add(at);rom[at]=v
    for line in (w/'render.ihx').read_text().splitlines():
        b=bytes.fromhex(line[1:]);assert sum(b)%256==0
        if b[3]==0:put(int.from_bytes(b[1:3],'big'),b[4:-1])
    put(0x7800,gate)
    hook=214*16384+8192+0x65e
    assert old[hook:hook+12]==bytes.fromhex('dde5dd210000dd39f5dd77ff')
    rom[hook:hook+12]=bytes.fromhex('f53ece320060c30078000000')
    assert len(rom)==4194304
    assert all(i in written or hook<=i<hook+12 for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
    (out/path.name).write_bytes(rom)
    for p in path.parent.glob('*.bin'):(out/p.name).write_bytes(p.read_bytes())
    report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),code_and_data_bytes=len(written),
                runtime_verified=False,adopted=False,scope='Render-only candidate. Near cockpit traffic only; original prologue replayed otherwise. Mapper252 restoration, transient GPU workspace, stack, pixels and cost require native proof.')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
