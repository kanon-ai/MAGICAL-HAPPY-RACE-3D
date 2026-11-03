from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text());out=R/'outputs/six-route-poll-shared';out.mkdir(exist_ok=True)
a=(R/'src/bgm.asm').read_text()
old='''        push af
        ld a,(active)
        or a
        jr z,service_af
        push bc
        push de
        push hl'''
new='''        push af
        push bc
        push de
        push hl
        ld a,(active)
        or a
        jr z,service_done'''
assert old in a;a=a.replace(old,new,1)
needle='service_done:\n'
insert=f'''service_done:
motion_timer_read:
        in a,(0xe7)
        ld b,a
        in a,(0xe6)
        ld c,a
        in a,(0xe7)
        cp b
        jr nz,motion_timer_read
        ld h,b
        ld l,c
        ld de,({S['_simulation_timer_last']})
        ld ({S['_simulation_timer_last']}),hl
        or a
        sbc hl,de
        ld de,({S['_simulation_ticks']})
        add hl,de
        ld ({S['_simulation_ticks']}),hl
        jr nc,motion_timer_done
        ld hl,({S['_simulation_ticks']+2})
        inc hl
        ld ({S['_simulation_ticks']+2}),hl
motion_timer_done:
'''
assert a.count(needle)==1;a=a.replace(needle,insert)
oldfast='        bit 7,h\n        jr nz,service_done'
assert oldfast in a
a=a.replace(oldfast,'        bit 7,h\n        jr z,tick_due\n        add hl,de\n        jp motion_sample\ntick_due:',1)
a=a.replace('        ld de,('+str(S['_simulation_timer_last'])+')','motion_sample:\n        ld de,('+str(S['_simulation_timer_last'])+')',1)
(out/'bgm.asm').write_text(a);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'bgm.asm'),str(out/'bgm.bin'),str(out/'bgm.sym')],cwd=R,check=True)
oldbgm=(R/'work/build/bgm.bin').read_bytes();newbgm=(out/'bgm.bin').read_bytes();assert len(newbgm)==len(oldbgm)
def code_at(addr):return (1+(addr-0x8000)//8192)*16384+8192+(addr-0x8000)%8192
for suf,n in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 o=R/('outputs/six-route-poll-shared'+suf);o.mkdir(exist_ok=True);src=R/('outputs/six-route-inland-uv'+suf);rom=bytearray((src/n).read_bytes());at=code_at(0xd600);assert rom[at:at+len(oldbgm)]==oldbgm;rom[at:at+len(newbgm)]=newbgm
 at=code_at(S['_bgm_poll']);length=S['_bgm_start']-S['_bgm_poll'];assert length==52 and rom[at:at+3]==bytes.fromhex('cd00d6');rom[at:at+length]=bytes.fromhex('c300d6')+bytes(length-3)
 (o/n).write_bytes(rom)
 for asset in ['city-atlas.bin','night-atlas.bin']:(o/asset).write_bytes((src/asset).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),scope='Merge register save/restore around BGM and motion timer; reuse the current timer sample when no music tick is due; reread after actual music update.',runtime_verified=False),indent=2))
