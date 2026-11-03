/* Runtime adapter for the checkpoint prototype. The lap-record clock is untouched. */
#include "arcade_checkpoint.h"
#include "arcade_addresses.h"
struct arcade_checkpoint_state arcade_state;
uint32_t arcade_previous_ticks,arcade_fraction;
uint8_t arcade_previous_mode,arcade_awarded;
uint16_t arcade_notice_tenths;
void arcade_runtime_init(void){
 arcade_checkpoint_reset(&arcade_state);
 arcade_previous_ticks=SIMULATION_TICKS;arcade_fraction=0;arcade_previous_mode=0;arcade_awarded=0;
 arcade_notice_tenths=0;
 CHECKPOINT=0;TIMED_OUT=0;DEADLINE=ARCADE_INITIAL_TENTHS;REMAINING_SECONDS=160;
 GRADE=0;RACE_POSITION=1;RIVAL_FINISHED=0;
}
void arcade_runtime_step(void){
 uint32_t now=SIMULATION_TICKS,elapsed=now-arcade_previous_ticks;
 uint16_t tenths=0;
 uint8_t current=MODE,running=current==1||arcade_previous_mode==1||STAGE_FINISH_PENDING;
 arcade_previous_ticks=now;
 if(arcade_previous_mode==1){
  arcade_fraction+=elapsed*140UL;
  while(arcade_fraction>=3579545UL){arcade_fraction-=3579545UL;++tenths;}
 }
 arcade_previous_mode=current;
 arcade_awarded=arcade_checkpoint_step(&arcade_state,tenths,ROUTE_PIECE,
   running,STAGE_FINISH_PENDING);
 if(tenths>=arcade_notice_tenths)arcade_notice_tenths=0;else arcade_notice_tenths-=tenths;
 if(arcade_awarded)arcade_notice_tenths=25;
 CHECKPOINT=arcade_state.checkpoints;
 DEADLINE=arcade_state.remaining_tenths;
 REMAINING_SECONDS=(arcade_state.remaining_tenths+9)/10;
 if(arcade_state.result==ARCADE_TIME_UP){
  if(!TIMED_OUT){STAGE_LAST[STAGE_ID]=LAP_CURRENT_TENTHS;STAGE_LAST_VALID[STAGE_ID]=1;}
  TIMED_OUT=1;STAGE_FINISH_PENDING=0;MODE=3;SPEED=0;}
}

void arcade_draw_hud(void){
 if(MODE!=1&&MODE!=2)return;
 GAME_RECT(4,4,66,12,12);
 GAME_TEXT(7,6,"TIME");GAME_NUMBER(37,6,REMAINING_SECONDS);
 if(arcade_notice_tenths){
  GAME_RECT(4,22,122,12,12);GAME_TEXT(10,24,"CHECKPOINT +140");
 }
}
