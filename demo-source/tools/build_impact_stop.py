from pathlib import Path
import os,re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/impact-stop';W.mkdir(exist_ok=True)
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe');env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
def compile(name,address):
 subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc',hex(address),'--data-loc','0x3fd8','-Wl-b_HOME=0x7ff0',str(R/f'src/{name}.c'),'-o',str(W/f'{name}.ihx')],env=env,check=True)
def symbols(name,fn):return int(re.search(r'([0-9A-F]{8})\s+_'+fn+r'\s',(W/f'{name}.map').read_text())[1],16)
def mem(path):
 d={}
 for line in path.read_text().splitlines():
  b=bytes.fromhex(line[1:]);assert sum(b)%256==0
  if b[3]==0:
   at=int.from_bytes(b[1:3],'big');d.update({at+i:v for i,v in enumerate(b[4:-1])})
 return d
compile('impact_stop',0x6840);compile('impact_stop_hud',0x6b10);compile('impact_engine',0x7300)
pre=symbols('impact_stop','crash_pre');post=symbols('impact_stop','crash_post');hud=symbols('impact_stop_hud','crash_hud');engine=symbols('impact_engine','impact_engine')
def asm(name,source):
 (W/f'{name}.asm').write_text(source);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/f'{name}.asm'),str(W/f'{name}.bin')],check=True);return (W/f'{name}.bin').read_bytes()
engine_gate=asm('engine_gate',f'''org 0d5aah
 push ix
 ld ix,0
 add ix,sp
 ld a,(ix+5)
 push af
 inc sp
 ld a,(ix+4)
 push af
 inc sp
 ld a,187
 ld (06000h),a
 call {engine}
 ld a,252
 ld (06000h),a
 pop ix
 pop hl
 pop af
 jp (hl)
''');assert len(engine_gate)<=86
near_gate_address=0xd5aa+len(engine_gate)
near_return=asm('near_return',f'org {near_gate_address}\n ld a,187\n ld (06000h),a\n call 07800h\n ld a,252\n ld (06000h),a\n ld a,(ix-11)\n ret\n')
assert len(engine_gate)+len(near_return)<=86
near=asm('cockpit_near',f'''org 07800h
 push hl
 push bc
 push de
 ld a,(60246)
 or a
 jr nz,done
 ld a,(60249)
 cp 254
 jr z,done
 ld hl,(60628)
 bit 7,h
 jr nz,done
 ld de,400
 or a
 sbc hl,de
 jr nc,done
 add hl,de
 ld b,h
 ld c,l
 add hl,hl
 add hl,bc
 add hl,de
 srl h
 rr l
 srl h
 rr l
 ld (60628),hl
done:
 pop de
 pop bc
 pop hl
 ret
''')
phys=lambda a:(1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/title-art'+suffix);f=next(src.glob('*.rom'));old=f.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 rom=bytearray(old);allowed=set()
 def put(at,data,expected=None):
  if expected is not None:assert old[at:at+len(data)]==expected,(hex(at),old[at:at+len(data)].hex())
  rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 for name,bank,lo,hi,empty in [('impact_stop',188,0x6840,0x7400,False),('impact_stop_hud',200,0x6b10,0x7000,False),('impact_engine',187,0x7300,0x8000,True)]:
  data=mem(W/f'{name}.ihx')
  for a,v in data.items():
   assert lo<=a<hi,(name,hex(a));put(bank*16384+a-0x4000,bytes([v]),b'\xff' if empty else None)
 put(195*16384+0x3bad,b'\xcd'+pre.to_bytes(2,'little'))
 put(188*16384+0x2800,b'\xcd'+post.to_bytes(2,'little'))
 put(200*16384+0x2403,b'\xc3'+hud.to_bytes(2,'little'),bytes.fromhex('c3106b'))
 put(phys(0xd5aa),engine_gate,b'\xff'*len(engine_gate))
 put(phys(near_gate_address),near_return,b'\xff'*len(near_return))
 put(187*16384+0x3800,near,b'\xff'*len(near))
 put(214*16384+8192+0xada,b'\xcd'+near_gate_address.to_bytes(2,'little'),bytes.fromhex('dd7ef5'))
 put(phys(0xd170),bytes.fromhex('c3aad5'),bytes.fromhex('dde5dd'))
 # Stop the initial BGM before title; start only once the title is dismissed.
 at=old.find(bytes.fromhex('cdffca'),phys(0xc800),phys(0xca00));assert at>=0
 put(at,bytes.fromhex('cd06d6'),bytes.fromhex('cdffca'))
 hooks=(src/'hooks.asm').read_text().replace(' call 0c18ah',' call 0c18ah\n call 0d603h')
 code=asm('title_hooks'+suffix,hooks);assert len(code)<=140
 put(phys(0xb174),code)
 # Insertion shifts panel_hook; use assembler symbol output to update its entry.
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/('title_hooks'+suffix+'.asm')),str(W/('title_hooks'+suffix+'.bin')),str(W/('title_hooks'+suffix+'.sym'))],check=True)
 sy=(W/('title_hooks'+suffix+'.sym')).read_text();panel=int(re.search(r'panel_hook\s+EQU\s+0([0-9A-F]+)H',sy)[1],16)
 put(phys(0xc3a7),b'\xc3'+panel.to_bytes(2,'little'))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 out=R/('outputs/impact-stop'+suffix);out.mkdir(exist_ok=True);(out/f.name).write_bytes(rom)
 (out/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),crash_pre=pre,crash_post=post,lock_ticks=45,tick_hz=30,front_threshold=0,lateral=28,scope='Collision feedback, 1.5-second stop, cockpit particles, silent title. Existing collision acceptance/camera/course unchanged.',verified=False),indent=2))
 print(out)
