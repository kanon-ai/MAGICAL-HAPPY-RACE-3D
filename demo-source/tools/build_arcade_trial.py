from pathlib import Path
import json,os,subprocess,re,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/arcade-runtime';W.mkdir(parents=True,exist_ok=True)
S=json.loads((R/'outputs/symbols.json').read_text());sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
names={'SIMULATION_TICKS':('simulation_ticks','uint32_t'),'MODE':('mode','uint8_t'),'ROUTE_PIECE':('route_piece','uint8_t'),'STAGE_FINISH_PENDING':('stage_finish_pending','uint8_t'),'SPEED':('speed','uint16_t'),'CHECKPOINT':('checkpoint','uint8_t'),'TIMED_OUT':('timed_out','uint8_t'),'DEADLINE':('deadline','uint16_t'),'REMAINING_SECONDS':('remaining_seconds','uint16_t'),'GRADE':('grade','uint8_t'),'RACE_POSITION':('race_position','uint8_t'),'RIVAL_FINISHED':('rival_finished','uint8_t')}
names.update({'STAGE_ID':('stage_id','uint8_t'),'LAP_CURRENT_TENTHS':('lap_current_tenths','uint32_t')})
(W/'arcade_addresses.h').write_text('\n'.join(f'#define {k} (*(volatile {t} *){S["_"+n]})' for k,(n,t) in names.items()))
with (W/'arcade_addresses.h').open('a') as f:
 f.write(f"\n#define STAGE_LAST ((volatile uint32_t *){S['_stage_last']})\n#define STAGE_LAST_VALID ((volatile uint8_t *){S['_stage_last_valid']})\n")
 f.write('#define GAME_RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)\n#define GAME_TEXT ((void (*)(int16_t,int16_t,const char *))0x888d)\n#define GAME_NUMBER ((void (*)(int16_t,int16_t,uint16_t))0x8975)\n')
env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6000','--data-loc','0xf6da','-Wl-b_HOME=0x7000','-I',str(W),'-I',str(R/'src'),str(R/'src/arcade_runtime.c'),'-o',str(W/'arcade.ihx')],env=env,check=True)
mem={}
for line in (W/'arcade.ihx').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  at=int.from_bytes(b[1:3],'big')
  for i,v in enumerate(b[4:-1]):assert 0x6000<=at+i<0x8000;mem[at+i]=v
maptext=(W/'arcade.map').read_text()
def symbol(name):
 m=re.search(r'([0-9A-F]{8})\s+_'+name+r'\s',maptext);assert m,name;return int(m[1],16)
assert symbol('arcade_notice_tenths')+2<=0xf700
entry={n:symbol(n) for n in ('arcade_runtime_init','arcade_runtime_step','arcade_state','arcade_previous_ticks','arcade_fraction','arcade_previous_mode','arcade_awarded','arcade_notice_tenths','arcade_draw_hud')}
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-integrated'+suffix);O=R/('outputs/six-route-arcade'+suffix);O.mkdir(exist_ok=True)
 b=bytearray((src/name).read_bytes());before=bytes(b);at=200*16384+8192;assert b[at:at+8192]==b'\xff'*8192
 for address,value in mem.items():b[at+address-0x6000]=value
 for ram,fn,hook in [(0xdb52,'arcade_runtime_init',0xbb73),(0xdbed,'arcade_runtime_step',0xbb91)]:
  code=bytes.fromhex('3ec8320060cd')+entry[fn].to_bytes(2,'little')+bytes.fromhex('3efc320060c9')
  pos=3*16384+8192+ram-0xc000;assert b[pos:pos+len(code)]==b'\xff'*len(code);b[pos:pos+len(code)]=code
  pos=(1+(hook-0x8000)//8192)*16384+8192+(hook-0x8000)%8192;b[pos:pos+3]=b'\xc3'+ram.to_bytes(2,'little')
 # Reuse the now-unreachable old journey bodies for conditional result text.
 def physical(addr):return (1+(addr-0x8000)//8192)*16384+8192+(addr-0x8000)%8192
 title_at=before.index(b'DRIVE COMPLETE\x00')
 title_cpu=0x8000+(title_at//16384-1)*8192+(title_at%16384-8192)
 pattern=b'\x21'+title_cpu.to_bytes(2,'little')+b'\xe5\x11\x2f\x00'
 hook=b.find(pattern);assert hook>=0 and b.find(pattern,hook+1)<0
 # HL returns the correct label; A is caller-scratch at the original load.
 label=0xbb76;helper=0xbb94
 b[physical(label):physical(label)+8]=b'TIME UP\x00'
 routine=b'\x21'+title_cpu.to_bytes(2,'little')+b'\x3a'+S['_timed_out'].to_bytes(2,'little')+bytes.fromhex('b7c8')+b'\x21'+label.to_bytes(2,'little')+b'\xc9'
 b[physical(helper):physical(helper)+len(routine)]=routine
 b[hook:hook+3]=b'\xcd'+helper.to_bytes(2,'little')
 # HUD runs at the end of draw_ui, then restores mapper before the panel.
 hud_tramp=0xbb7e
 code=bytes.fromhex('3ec8320060cd')+entry['arcade_draw_hud'].to_bytes(2,'little')+bytes.fromhex('3efc320060c3a7c3')
 assert len(code)==16 and hud_tramp+len(code)<=0xbb91
 b[physical(hud_tramp):physical(hud_tramp)+len(code)]=code
 call=b.find(bytes.fromhex('cda7c3'));assert call>=0 and b.find(bytes.fromhex('cda7c3'),call+1)<0
 b[call:call+3]=b'\xcd'+hud_tramp.to_bytes(2,'little')
 (O/name).write_bytes(b)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 report=dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(before).hexdigest(),entry=entry,bank=200,free_bytes=303104-8192,scope='Checkpoint runtime connected; TIME UP title connected; countdown HUD and checkpoint notice connected; native tests pending')
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
