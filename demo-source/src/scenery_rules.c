#include "hardware.h"
#include "route_config.h"
extern volatile u8 route_piece;
extern volatile u16 distance;
extern u16 atlas_rows;
extern u8 profile[256];
void apply_harbor_appearance(u16 phase){
 u8 i,j,keep=255,*p=profile+128,*m,kind;
 s16 *top,*bottom;u16 height;
 if((route_piece&7)==7&&route_piece<ROUTE_LAST_PIECE){
  *((volatile u8*)0x6000)=250;keep=*((const u8*)(0x6400+phase));
 }else if(atlas_rows<256||(((route_piece&7)==0)&&distance<2048))keep=0;
 else if((route_piece&7)==0){*((volatile u8*)0x6000)=255;keep=*((const u8*)(0x6800+phase));}
 for(i=0;i<8;++i,p+=8,keep>>=1){
  if((route_piece<8||route_piece>=14)&&((p[5]&7)==5||(p[5]&7)==7))continue;
  if(!(keep&1)){p[7]=0;continue;}
  if(!p[7]||route_piece==7||route_piece>=14)continue;
  kind=(p[5]>>3)&3;
  kind=kind==0?0:(kind==2?2:6);
  p[5]=(p[5]&248)|kind;
  if(kind==4)continue;
  m=(u8*)(0x0100+(u16)i*60);
  /* Four roof corners descend towards their own ground corner; no levitation. */
  for(j=0;j<8;++j){
   if((j&3)<2)continue;
   top=(s16*)(m+(u16)j*5+2);bottom=(s16*)(m+(u16)(j^3)*5+2);
   height=m[(u16)j*5+4];height+=kind==6?height/2:height;
   if(j>=6)height-=height/4;
   /* Inset the top silhouette inside the unchanged ground footprint. */
   *((s16*)(m+(u16)j*5))+=(j==3||j==7)?m[(u16)j*5+4]/4:-(s16)(m[(u16)j*5+4]/4);
   *top=*bottom-height;
  }
 }
}
