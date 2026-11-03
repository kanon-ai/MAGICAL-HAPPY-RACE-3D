/* Prototype arcade rules. Independent of rendering and the lap-record clock.
 * elapsed_tenths must contain RUNNING time only, supplied by the adapter.
 * Initial balancing values: 160 seconds + 140 at each of five checkpoints.
 */
#ifndef ARCADE_CHECKPOINT_H
#define ARCADE_CHECKPOINT_H
#include <stdint.h>
#define ARCADE_INITIAL_TENTHS 1600U
#define ARCADE_CHECKPOINT_TENTHS 1400U
#define ARCADE_FINISH_PIECE 47U
#define ARCADE_RUNNING 0U
#define ARCADE_TIME_UP 1U
#define ARCADE_CLEARED 2U
struct arcade_checkpoint_state {
 uint16_t remaining_tenths;
 uint8_t checkpoints;
 uint8_t result;
};
static void arcade_checkpoint_reset(struct arcade_checkpoint_state *s){
 s->remaining_tenths=ARCADE_INITIAL_TENTHS;s->checkpoints=0;s->result=ARCADE_RUNNING;
}
/* Returns the number of newly crossed checkpoints, for a separate UI notice.
 * Exact deadline ties expire: a late crossing cannot resurrect a finished run.
 * Repeated frames, pausing, or moving back never award a checkpoint twice.
 */
static uint8_t arcade_checkpoint_step(struct arcade_checkpoint_state *s,
 uint16_t elapsed_tenths,uint8_t route_piece,uint8_t running,uint8_t finished){
 uint8_t reached,awarded=0;
 if(!running||s->result!=ARCADE_RUNNING)return 0;
 if(elapsed_tenths>=s->remaining_tenths){
  s->remaining_tenths=0;s->result=ARCADE_TIME_UP;return 0;
 }
 s->remaining_tenths-=elapsed_tenths;
 reached=route_piece>>3;if(reached>5)reached=5;
 while(s->checkpoints<reached){
  s->remaining_tenths+=ARCADE_CHECKPOINT_TENTHS;
  ++s->checkpoints;++awarded;
 }
 if(finished&&route_piece==ARCADE_FINISH_PIECE)s->result=ARCADE_CLEARED;
 return awarded;
}
#endif
