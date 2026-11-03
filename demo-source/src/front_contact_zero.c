/* Bounded 30 Hz recovery overlay. Existing collision hulls/clock remain intact.
 * Main mapper page-0 tail, after BOTH 468-byte model blocks: 3FD8..3FF7.
 * The cache bootstrap initializes this area; event_tick==0 resets new games.
 */
#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define I16(a) (*(volatile int16_t *)(a))
#define MODE U8(57921)
#define SPEED U16(57929)
#define X I16(57939)
#define STEER I16(57945)
#define FRACTION I16(57947)
#define STEPS U16(57950)
#define HITS U16(59469)
#define EVENT U16(59471)
#define RECOVERY U8(59494)
#define LIMIT U8(59562)
#define SIDE U8(59563)
#define CONTACT ((volatile uint8_t *)59564)
#define PULSE U8(59569)
struct recovery_state {
 uint8_t magic,locked,immune,deep,kind,effect;
 uint16_t hits,pre_speed;
 int16_t anchor;
 uint8_t reserved[20];
};
#define C (*(volatile struct recovery_state *)0x3fd8)
static void clear_contacts(void) {
 uint8_t i; for(i=0;i<5;++i)CONTACT[i]=0;
}
static void reset(void) {
 uint8_t i;for(i=0;i<sizeof(C);++i)((volatile uint8_t *)&C)[i]=0;
 C.magic=0xC7;C.hits=HITS;
}
/* Choose the best unoccupied lateral slot. Center remains a valid escape.
 * Traffic uses the same wrapped longitudinal coordinate as the existing game.
 * Do not teleport forward or award checkpoints during recovery.
 */
static int16_t safe_x(void) {
 int16_t candidate,best=0,dx,gap;
 uint16_t clearance,best_clearance=0,d;
 uint8_t i;
 for(candidate=-48;candidate<=48;candidate+=16) {
  clearance=4096;
  for(i=0;i<5;++i) {
   gap=(((volatile uint16_t *)59457)[i]-U16(57927))&16383;
   if(gap>8191)gap-=16384;
   dx=candidate-((volatile int8_t *)59479)[i];if(dx<0)dx=-dx;
   /* Leave body width plus a margin; central squeeze still available. */
   if(dx<24) {
    d=gap<0?-gap:gap;
    if(d<clearance)clearance=d;
   }
  }
  if(clearance>best_clearance){best_clearance=clearance;best=candidate;}
 }
 C.reserved[1]=best_clearance>=80;
 return best;
}
static void place_safely(void) {
 uint8_t tries=0,back=U16(57927)>=1536;
 X=safe_x();
 /* Rare completely blocked road: search bounded positions within this piece.
  * Never cross a stage/checkpoint boundary or move another vehicle. */
 while(!C.reserved[1] && tries<12) {
  if(back)U16(57927)-=128;else U16(57927)+=128;
  ++tries;X=safe_x();
 }
}
uint8_t crash_pre(void) {
 uint8_t i;
 if(C.magic!=0xC7 || EVENT==0)reset();
 C.pre_speed=SPEED;
 for(i=0;i<5;++i)((volatile uint16_t *)&C.reserved[0])[i]=(((volatile uint16_t *)59457)[i]-U16(57927))&16383;
 *((volatile uint16_t *)&C.reserved[10])=U16(59467);
 *((volatile uint16_t *)&C.reserved[12])=U16(59475);
 *((volatile uint16_t *)&C.reserved[14])=U16(59477);
 if(MODE!=1)return 0;
 if(C.locked) {
  SPEED=0;FRACTION=0;
  /* Existing closed player poses: controlled skid, no untextured underside. */
  STEER=(C.locked&8)?40:-40;
  RECOVERY=2;LIMIT=128;clear_contacts();
  return 1;
 }
 if(C.immune){RECOVERY=2;LIMIT=128;clear_contacts();}
 return 0;
}
void crash_post(void) {
 uint8_t i;int16_t gap,prior,dx;
 ++STEPS;
 if(MODE!=1){C.locked=C.immune=C.deep=0;return;}
 if(C.locked) {
  --C.locked;SPEED=0;C.hits=HITS;
  /* Last half second brings the car back smoothly, rather than a cut. */
  if(C.locked<15) {
   C.anchor=safe_x();
   if(X<C.anchor){X+=8;if(X>C.anchor)X=C.anchor;}
   if(X>C.anchor){X-=8;if(X<C.anchor)X=C.anchor;}
  }
  if(!C.locked) {
   place_safely();STEER=FRACTION=0;SPEED=48; /* 90 km/h */
   C.immune=60;RECOVERY=2;LIMIT=128;C.deep=0;
   clear_contacts();U8(57923)=0;
  }
  return;
 }
 if(C.immune) {
  --C.immune;C.hits=HITS;C.deep=0;
  if(!C.immune){RECOVERY=0;STEER=FRACTION=0;}
  return;
 }
 if(C.effect)--C.effect;
 /* Player front is road distance +40 (1000 model units). Traffic Z is its rear bumper.
  * Sweep the relative nose/rear crossing; ignore screen-space overlap. */
 for(i=0;i<5;++i) {
  if(CONTACT[i])continue;
  prior=((volatile uint16_t *)&C.reserved[0])[i];
  gap=(((volatile uint16_t *)59457)[i]-U16(57927))&16383;
  if(gap>8191)gap-=16384;
  dx=X-((volatile int8_t *)59479)[i];if(dx<0)dx=-dx;
  if(prior>=0 && prior<=120 && gap<=0 && gap>=-36 && dx<28) {
   if(U16(57927)<(uint16_t)(0-gap) && U8(57935))--U8(57935);
   U16(57927)=(((volatile uint16_t *)59457)[i])&16383;
   U16(59467)=*((volatile uint16_t *)&C.reserved[10]);
   U16(59475)=*((volatile uint16_t *)&C.reserved[12]);
   U16(59477)=*((volatile uint16_t *)&C.reserved[14]);
   U16(59473)=0;
   CONTACT[i]=1;U8(59489+i)=1;++HITS;
   SIDE=((volatile int8_t *)59479)[i]<X-8?1:((volatile int8_t *)59479)[i]>X+8?2:0;
   U8(59560)=2;U8(59561)=30;PULSE=6;
   break;
  }
 }
 if(HITS!=C.hits) {
  C.hits=HITS;C.deep=0;
  if(SIDE || C.pre_speed<56) {
   /* Scrape: keep steering and most speed. Existing contact gap still holds. */
   SPEED=C.pre_speed>12?C.pre_speed-12:0;
   LIMIT=SPEED;RECOVERY=4;C.kind=1;C.effect=8;PULSE=4;
  } else {
   SPEED=C.pre_speed>96?40:32;LIMIT=SPEED;RECOVERY=6;
   C.kind=2;C.effect=12;PULSE=6;
  }
 }
 /* Deep excursion only: ordinary shoulder driving remains controllable.
  * Right boundary follows the existing widening lane (0..32 extra halfwidth).
  */
 if(U8(57923) && (X< -90 || X>90+U8(0xf6f5)) && C.pre_speed>=56) {
  if(C.deep<6)++C.deep;
 } else C.deep=0;
 if(C.deep>=6) {
  C.locked=45;C.kind=3;C.effect=0;C.anchor=X;SPEED=0;
  STEER=40;FRACTION=0;RECOVERY=2;LIMIT=128;
  ++HITS;C.hits=HITS;U16(59473)=0;clear_contacts();PULSE=6;
 }
}
