#ifndef RALLY_HARDWARE_H
#define RALLY_HARDWARE_H
#include "io_ports.h"
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned int u16;
typedef signed int s16;
#define INPUT_LEFT 1
#define INPUT_RIGHT 2
#define INPUT_UP 4
#define INPUT_DOWN 8
#define INPUT_FIRE 16
#define INPUT_BRAKE 32
#define INPUT_PAUSE 64
#define INPUT_VIEW 128
void bgm_poll(void);
void bgm_start(void);
void gfx_init(void);
void gfx_set_palette(const u8 *palette);
void hardware_upload(void);
void gfx_upload_begin(u16 y);
void gfx_upload_road(u8 rows);
void gfx_upload_256(const u8 *data);

void gfx_wait(void);
void gfx_vblank(void);
void gfx_fill(u16 x,u16 y,u16 w,u16 h,u8 color);
void gfx_blit(u16 sx,u16 sy,u16 dx,u16 dy,u16 w,u16 h,u8 transparent);
void gfx_scaled(u8 origin_x,u16 sy,u8 sw,u8 w,u8 h,u16 step,s16 x,s16 y,s16 bottom,u16 page,u8 mirror);
void gfx_texture_window(u16 x,u16 y,u16 ex,u16 ey);
void gfx_flip(u8 page);
u16 gfx_timer(void);
extern u16 span_y;
extern u8 span_height;
void gfx_begin_spans(void);
void gfx_span(s16 left,s16 right,u8 color);
u8 input_read(void);
extern volatile u8 collision_pulse;
void engine_sound(u16 speed,u8 offroad,u8 muted);
#endif
