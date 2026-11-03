"""Unadopted render-only ROM trial; exact source bytes and placements guarded."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
    w=R/('work/traffic-near-render-indexed'+suffix)
    out=R/('outputs/six-route-traffic-near-caller-restore'+suffix);out.mkdir(exist_ok=True)
    entry=int(re.search(r'([0-9A-F]{8})\s+_draw_near_car\s',(w/'render.map').read_text())[1],16)
    # Entry hook saves original AF. HL contains clip in L and must survive guards.
    asm=f'''org 07800h
 ; Hook saved original AF, HL and the mapped bank's first word.
 pop de
 pop hl
 pop bc
 ; Bank 210 contains a renderer that calls the resident car routine.
 ; Other observed callers return to resident code and used bank252 before.
 ld a,252
 push hl
 ld hl,04b42h
 or a
 sbc hl,de
 pop hl
 jr nz,return_selected
 ld a,210
return_selected:
 push af
 ld de,02a6ch
 push de
 push hl
 push bc
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
 pop af
 pop hl
 jp {entry}
ordinary:
 pop af
 pop hl
 ; Replay all19 displaced bytes, including horizon condition flags.
 db 0ddh,0e5h,0ddh,021h,0,0,0ddh,039h,0f5h,0ddh,077h,0ffh
 db 0ddh,075h,0feh,03ah,056h,0ebh,0b7h
 jp 02a71h
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
    assert old[hook:hook+19]==bytes.fromhex('dde5dd210000dd39f5dd77ffdd75fe3a56ebb7')
    signature=bytes.fromhex('424b')
    assert [i for i in range(256) if old[i*16384+8192:i*16384+8194]==signature]==[210]
    rom[hook:hook+19]=bytes.fromhex('f5e52a0060e53ece320060c30078f1320060c9')
    assert len(rom)==4194304
    assert all(i in written or hook<=i<hook+19 for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
    (out/path.name).write_bytes(rom)
    for p in path.parent.glob('*.bin'):(out/p.name).write_bytes(p.read_bytes())
    report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),code_and_data_bytes=len(written),
                runtime_verified=False,adopted=False,scope='Render-only candidate. Near cockpit traffic only; original prologue replayed otherwise. Bank210 renderer caller restored through resident stack-return stub; resident/data callers retain previous bank252 behavior. Requires normal-drive and both-port proof.')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
