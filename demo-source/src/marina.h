/* Left-side piers attach to the quay, with a deck, fascia, support piles,
 * canopy or harbor lights. Six world-space anchors per structure come from ROM. */
static s16 marina_x[16],marina_y[16];
static void draw_marina(void){
 u8 i,j,kind,*p,*base;u16 front,back; s16 rise,thick;
 for(i=0;i<4;++i){
  base=(u8*)(0x0400+(u16)i*32);kind=base[30];
  for(j=0;j<6;++j){
   p=base+(u16)j*5;
   marina_x[j]=(s16)((u16)p[0]|((u16)p[1]<<8))-camera_shift(p[4]>>1);
   marina_y[j]=(s16)((u16)p[2]|((u16)p[3]<<8));
  }
  if(marina_x[0]<-20&&marina_x[3]<-20)continue;
  if(marina_y[0]-80>168)continue;
  front=base[4];back=base[14];if(!front)front=1;
  rise=marina_y[0]-marina_y[4];
  /* Four roof corners, two already projected and two at the rear depth. */
  marina_x[8]=marina_x[0];marina_y[8]=marina_y[4];
  marina_x[9]=marina_x[1];marina_y[9]=marina_y[5];
  marina_x[10]=marina_x[2];marina_y[10]=marina_y[2]-rise*back/front;
  marina_x[11]=marina_x[3];marina_y[11]=marina_y[3]-rise*back/front;
  for(j=0;j<4;++j){
   thick=1+(base[j*5+4]>>5);
   marina_x[j+4]=marina_x[j];marina_y[j+4]=marina_y[j]+thick;
   marina_x[j+12]=marina_x[j];marina_y[j+12]=marina_y[j]+2+(base[j*5+4]>>3);
  }
  gfx_wait();road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(34,168);
  road_index=0x40;road_data=0;road_index=0x50;
  for(j=0;j<16;++j)road_vertex(marina_x[j],marina_y[j]);
  road_index=0x42;road_data=16;road_index=0x58;road_data=0;road_index=0x52;
  road_face(0,1,2,3,COL_MOUNTAIN);road_face(3,2,1,0,COL_MOUNTAIN);
  road_face(0,4,5,1,COL_DARK);road_face(1,5,6,2,COL_DARK);
  if(kind!=1){
   road_face(8,9,10,11,kind?COL_SKY_LIGHT:COL_VERGE);
   road_face(11,10,9,8,kind?COL_SKY_LIGHT:COL_VERGE);
  }
  road_index=0x59;road_data=kind==1?4:6;road_index=0x45;road_data=0;road_word(0x46,page_y());
  road_index=0x48;road_data=3;while(road_index&1){}gfx_wait();
  road_index=0x41;road_data=0;road_index=0x51;
  for(j=0;j<4;++j){road_data=j+12;road_data=j+8;}
  for(j=0;j<4;++j){road_data=j+8;road_data=8+((j+1)&3);}
  for(j=0;j<4;++j){road_data=j;road_data=(j+1)&3;}
  road_index=0x43;road_data=12;road_index=0x44;road_data=COL_METAL;
  road_index=0x48;road_data=1;while(road_index&1){}gfx_wait();
  if(kind==1){
   for(j=0;j<2;++j)rect(marina_x[8+j]-2,marina_y[8+j],5,2,COL_WHITE);
  }
 }
 road_word(24,120);road_word(26,128);road_word(28,91);road_word(30,32);road_word(34,212);
}
