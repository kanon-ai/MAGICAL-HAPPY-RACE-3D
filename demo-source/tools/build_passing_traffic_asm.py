"""Isolated third-lane traffic admission, early merge, and blocked-merge hold."""
from pathlib import Path
import os,subprocess,json,re,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/passing-traffic-asm';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6500','--data-loc','0xf6fb','-Wl-b_HOME=0x7800',str(R/'src/passing_traffic.c'),'-o',str(W/'traffic.ihx')],env=env,check=True)
mem={}
for line in (W/'traffic.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  a=int.from_bytes(b[1:3],'big')
  for i,v in enumerate(b[4:-1]):assert 0x6500<=a+i<0x8000;mem[a+i]=v
entry=int(re.search(r'([0-9A-F]{8})\s+_passing_traffic\s',(W/'traffic.map').read_text())[1],16)
original_entry=entry
entry=0x6800
fast=f'''org 06800h
 ld c,a
 ld a,(57935)
 and 7
 dec a
 cp 3
 jr c,full
 ld b,0
 ld hl,59479
 add hl,bc
 ld a,(hl)
 add a,128
 cp 169
 jr nc,full
 ld hl,59484
 add hl,bc
 ld a,(hl)
 add a,128
 cp 169
 jr nc,full
 ld hl,0f6fbh
 add hl,bc
 xor a
 ld (hl),a
 ret
full:
 ld a,c
 jp {original_entry}
'''
gate=f'''org 06400h
 push bc
 push de
 push hl
 push ix
 push iy
 ld a,(ix-4)
 call {entry}
 pop iy
 pop ix
 pop hl
 pop de
 pop bc
 or a
 jp z,06100h
 inc sp
 inc sp
 jp 0a1a2h
'''
hold='''org 0b100h
 push hl
 push de
 ld l,(ix-4)
 ld h,0
 ld de,0f6fbh
 add hl,de
 ld a,(hl)
 pop de
 pop hl
 or a
 jr nz,stopped
 ld a,(ix-11)
 ret
stopped:
 xor a
 ret
'''
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-mirror-lines-v2'+suffix);out=R/('outputs/six-route-passing-traffic-asm'+suffix);out.mkdir(exist_ok=True)
 def assemble(name,text):
  (out/(name+'.asm')).write_text(text);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/(name+'.asm')),str(out/(name+'.bin'))],check=True);return (out/(name+'.bin')).read_bytes()
 f=assemble('policy-fast-path',fast);assert max(mem)<0x6800;rom_fast=f
 g=assemble('traffic-gate',gate);h=assemble('merge-hold',hold);assert len(g)<256 and len(h)<80
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old);bank=206*16384+8192
 assert old[bank+0x400:bank+0x2000]==b'\xff'*(0x2000-0x400)
 for a,v in mem.items():rom[bank+a-0x6000]=v
 rom[bank+0x400:bank+0x400+len(g)]=g
 rom[bank+0x800:bank+0x800+len(rom_fast)]=rom_fast
 at=off(0xd7ee);assert old[at:at+8]==bytes.fromhex('3ece320060c30061');rom[at+6:at+8]=(0x6400).to_bytes(2,'little')
 at=off(0xa475);assert old[at:at+3]==bytes.fromhex('dd7ef5');rom[at:at+3]=bytes.fromhex('cd00b1')
 assert old[off(0xb02c):off(0xb02c)+3]==bytes.fromhex('c335a9')
 rom[off(0xb100):off(0xb100)+len(h)]=h
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),policy_bytes=len(mem),entry=entry,playable_adoption=False,native_validation=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
