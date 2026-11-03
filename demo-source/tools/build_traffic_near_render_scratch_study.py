"""Compile both I/O variants; check candidate placement, without modifying ROMs."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]
sd=Path('C:/MSX/toolchain-workspace/work/toolchain/sdcc/bin/sdcc.exe')
env=dict(os.environ);env['PATH']=str(sd.parent)+os.pathsep+env.get('PATH','')
models=bytearray();faces=bytearray()
for variant in range(4):
    data=(R/('assets/truck-packets.bin' if variant==3 else 'assets/traffic-packets.bin')).read_bytes()
    start=2048 if variant==3 else 6144+variant*156
    models.extend(data[start:start+156])
    block=(0 if variant==3 else variant*2048)+1024
    count=data[block];assert count==46
    for face in range(0,count,2):
        p=data[block+1+face*11:block+1+(face+1)*11]
        uv=data[block+1+count*11+face*8:block+1+count*11+(face+1)*8]
        faces.extend(p[:4]+uv+p[10:11])
assert len(models)==624 and len(faces)==1196
reports=[]
for suffix in ('','-external-88h'):
    w=R/('work/traffic-near-render-scratch'+suffix);w.mkdir(exist_ok=True)
    (w/'near_car_data.h').write_text('static const uint8_t near_models[]={'+','.join(map(str,models))+'};\nstatic const uint8_t near_faces[]={'+','.join(map(str,faces))+'};\n')
    (w/'gate_addresses.h').write_bytes((R/('work/rock-bore-gpu-ring'+suffix)/'gate_addresses.h').read_bytes())
    subprocess.run([str(sd),'-mz80','--opt-code-size','--no-std-crt0','--code-loc','0x6900','--data-loc','0xf200','-Wl-b_HOME=0x7e00','-I',str(w),str(R/'src/traffic_near_render_scratch.c'),'-o',str(w/'render.ihx')],env=env,check=True)
    mem={}
    for line in (w/'render.ihx').read_text().splitlines():
        b=bytes.fromhex(line[1:]);assert sum(b)%256==0
        if b[3]==0:
            a=int.from_bytes(b[1:3],'big')
            for i,v in enumerate(b[4:-1]):
                assert 0x6900<=a+i<0x8000 and a+i not in mem
                mem[a+i]=v
    rom=next((R/('outputs/six-route-snow-roadside-depth'+suffix)).glob('*.rom')).read_bytes()
    for a in mem:assert rom[206*16384+8192+a-0x6000]==255
    reports.append(dict(port=suffix or 'internal98',code_and_data_bytes=len(mem),lowest=min(mem),highest=max(mem),baseline_sha256=hashlib.sha256(rom).hexdigest(),candidate_bytes_all_ff=True))
out=R/'outputs/traffic-near-render-scratch-study';out.mkdir(exist_ok=True)
(out/'compile-validation.json').write_text(json.dumps(dict(variants=reports,scope='Compile and candidate-byte fit only. No ROM hook, native rendering, scratch ownership, mapper restoration, stack or FPS verification.'),indent=2)+'\n')
print(json.dumps(reports,indent=2))
