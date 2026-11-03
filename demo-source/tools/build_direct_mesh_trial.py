from pathlib import Path
import re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text());src=(R/'src/mesh_unpack.c').read_text();offsets=list(map(int,re.findall(r'\d+',src.split('mesh_unpack_offsets[60]={')[1].split('};')[0])));assert len(offsets)==60
asm='org 0d700h\n ld hl,0f500h\n ld de,0100h\n ld bc,480\nobject:\n';cursor=0
for pos in offsets:
 delta=pos-cursor
 if abs(delta)<=3:asm+=(' inc l\n' if delta>0 else ' dec l\n')*abs(delta)
 elif delta:asm+=f' ld a,l\n add a,{delta&255}\n ld l,a\n'
 asm+=' ldi\n';cursor=pos+1
assert cursor==30
asm+=' ld a,b\n or c\n jp nz,object\n ret\n'
out=R/'outputs/six-route-direct-mesh';out.mkdir(exist_ok=True);(out/'mesh.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'mesh.asm'),str(out/'mesh.bin')],check=True);code=(out/'mesh.bin').read_bytes();assert len(code)<=256,len(code)
def code_at(addr):return (1+(addr-0x8000)//8192)*16384+8192+(addr-0x8000)%8192
for suf,n in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 source=R/('outputs/six-route-poll-shared'+suf);o=R/('outputs/six-route-direct-mesh'+suf);o.mkdir(exist_ok=True);rom=bytearray((source/n).read_bytes());at=code_at(0xd700);assert rom[at:at+256]==bytes(256)
 rom[at:at+len(code)]=code;entry=214*16384+8192+S['_expand_course_mesh']-0x2400;assert rom[entry:entry+3]==bytes.fromhex('fde5d9');rom[entry:entry+3]=bytes.fromhex('c300d7');(o/n).write_bytes(rom)
 for asset in ['city-atlas.bin','night-atlas.bin']:(o/asset).write_bytes((source/asset).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),scope='Fixed-order expansion of all compact meshes. No geometry, palette, assets or gameplay change.',runtime_verified=False),indent=2))
print('mesh helper bytes',len(code))
