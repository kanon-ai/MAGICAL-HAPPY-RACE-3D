/* Isolated coast trial. Private Geo3D V2 vertices192+ and faces912..991.
 * Ground anchors and clipping are the existing scenery projection. The local
 * 3D silhouette has depth-dependent parallax; no screen-slot randomisation.
 */
#include <stdint.h>
#include "io_ports.h"
#include "tree_models.h"
__sfr __at(IO_GEO_INDEX) gi;
__sfr __at(IO_GEO_DATA) gd;
__sfr __at(IO_CONTROL) vc;
__sfr __at(IO_COMMAND) vd;
#define READY (*(volatile uint8_t*)0x38ee)
static void word(uint8_t r,int16_t v){gi=r;gd=v;gd=v>>8;}
static void cw(uint16_t v){vd=v;vd=v>>8;}
void polygon_tree(uint8_t *a){
 uint8_t palm=a[0]==78,h=a[2],i,n,faces,flag=palm?2:1;
 uint16_t first=palm?968:912;
 const uint8_t *model=palm?palm_model:round_model,*p;
 int16_t cx=*(int16_t*)(a+5)+a[1]/2,foot=*(int16_t*)(a+7)+h;
 int16_t clip=*(int16_t*)(a+9),horizon=(*(uint8_t*)60246)?130:78,x,y,z;
 uint16_t page=*(uint16_t*)(a+11);
 n=model[0];faces=model[1];p=model+2+n*3;
 if(!(READY&flag)){
  gi=0x58;gd=first;gi=0x6c;gd=first>>8;gi=0x52;
  for(i=0;i<faces;++i){uint8_t j;for(j=0;j<11;++j)gd=*p++;}
  gi=0x65;gd=first;gi=0x6e;gd=first>>8;gi=0x53;
  for(i=0;i<faces;++i){uint8_t j;for(j=0;j<8;++j)gd=*p++;}
  READY|=flag;
 }
 gi=0x68;gd=0;gi=0x40;gd=192;gi=0x50;p=model+2;
 for(i=0;i<n;++i){
  int16_t vx=(int8_t)*p++,vy=*p++,vz=(int8_t)*p++;
  z=((int16_t)h*vz)>>7;
  x=cx+(((int16_t)h*vx)>>7)-(((cx-128)*z)>>8);
  y=foot-(((int16_t)h*vy)>>7)+(((horizon-foot)*z)>>8);
  gd=x;gd=x>>8;y=-y;gd=y;gd=y>>8;gd=1;gd=0;
 }
 gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;
 vc=51;vc=0x91;cw(80);cw(992);cw(95);cw(1007);
 word(0x60,80);word(0x62,992);gi=0x64;gd=0;
 word(24,1);word(26,0);word(28,0);word(30,1);word(34,clip);
 word(0x54,192);word(0x56,first);gi=0x42;gd=n;gi=0x59;gd=faces;
 gi=0x45;gd=0;word(0x46,page);gi=0x48;gd=7;while(gi&1){}
 word(0x54,0);word(0x56,0);
}
