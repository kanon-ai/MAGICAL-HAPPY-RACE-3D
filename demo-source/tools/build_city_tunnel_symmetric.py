"""Evaluate shared symmetric inner-ring projection without reducing geometry."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_fastcoord.c').read_text()
a=t.index('static void lining_ring(');b=t.index('static void terrain_ring(',a)
replacement='''static void lining_ring(Plane *p) __z88dk_fastcall {
 static const int16_t xx[4]={96,89,68,37};
 static const int16_t yy[4]={0,38,71,92};
 int16_t dx[4],sy[4];uint8_t i;
 for(i=0;i<4;++i){dx[i]=arch_coord(xx[i],p->w);sy[i]=p->y-arch_coord(yy[i],p->w);}
 for(i=0;i<4;++i)vertex(p->x-dx[i],sy[i]);
 vertex(p->x,p->y-arch_coord(100,p->w));
 for(i=4;i;){--i;vertex(p->x+dx[i],sy[i]);}
}
'''
t=t[:a]+replacement+t[b:]
(R/'src/drive_city_tunnel_symmetric.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_symmetric.c').replace('city-tunnel-trial','city-tunnel-symmetric').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
