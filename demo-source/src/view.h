#ifndef ROAD_VIEW_H
#define ROAD_VIEW_H
void car_resident_init(void);
void draw_one_traffic(u8 i);
u16 page_y(void);
void road_word(u8 index,s16 v);
extern volatile u8 car_draw_id;
extern volatile u8 camera_mode;
extern u8 view_bottom;
u8 view_width(u8 width);
s16 view_x(s16 x,u8 width);
s16 view_y(s16 y,u8 width);
void draw_player_car(void);
void road_vertex(s16 x,s16 y);
void draw_sea(void);
void sea_include(s16 center,u8 width);
void advance_simulation(void);
s16 camera_shift(u8 halfwidth);
void draw_road_markers(void);
extern u8 scene_ground;
u8 route_progress(void);
u8 terrain_ground(s16 ahead);
void prepare_terrain_ground(void);
extern u8 terrain_active;
void draw_night_sky_top(u16 mix);
#endif
