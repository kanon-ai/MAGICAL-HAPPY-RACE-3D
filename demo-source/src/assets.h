typedef struct { unsigned int x,y; unsigned char w,h; } Sprite;
#define SKY_Y 512
#define SKY_H 128
Sprite font[96];
static const Sprite rocks[6]={{0,0,0,0}},bushes[6]={{0,0,0,0}};
static const Sprite race_positions[4]={{0,642,84,8},{128,642,84,8},{0,652,84,8},{128,652,84,8}};
