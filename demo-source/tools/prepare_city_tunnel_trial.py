"""Generate isolated boundary tunnel geometry, retaining the forest implementation."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'src/drive_tunnel_depth_fast.c'
s=p.read_text()
needle='void draw_late_tunnel(void){'
assert s.count(needle)==1
extra='''/* Boundary-spanning city tunnel; local road samples bend the lining.
 * This geometry trial does not yet conceal the panorama through its exit. */
static void draw_city_tunnel(void){
 int16_t progress,entrance,exitgap,z,nearz,farz,car_gap;
 uint8_t n,id,valid=0;Plane shared;
 if(PIECE!=39 && PIECE!=40)return;
 if(MODE!=1&&MODE!=2&&MODE!=4)return;
 progress=PIECE==39?(int16_t)DISTANCE-13312:(int16_t)DISTANCE+3072;
 entrance=-progress;exitgap=6144-progress;
 if(entrance>1400 || exitgap<-(CAMERA?60:0))return;
 if(entrance>-(CAMERA?84:24))draw_rock_shell(entrance,24);
 /* World anchored 64-unit cells; only the near road's sampled depth is used. */
 for(n=9;n;){
  --n;z=((progress+32)&63);nearz=((int16_t)n<<6)-z;
  farz=nearz+64;
  if(nearz>512 || farz<entrance || nearz>exitgap)continue;
  if(nearz<entrance)nearz=entrance;
  if(farz>exitgap)farz=exitgap;
  if(farz>512)farz=512;
  if(nearz>=farz)continue;
  valid=draw_lining_slice(nearz,farz,&shared,valid);
 }
 for(n=0;n<5;++n){
  id=((uint8_t *)59555)[n];car_gap=((uint16_t *)59500)[id]&16383;
  if(car_gap&8192)car_gap-=16384;
  if(car_gap<exitgap)((void (*)(uint8_t))11298)(id);
 }
}
'''
s=s.replace(needle,extra+needle+'\n if(PIECE==39 || PIECE==40){draw_city_tunnel();return;}')
out=R/'src/drive_city_tunnel_trial.c';out.write_text(s)
print(out)
