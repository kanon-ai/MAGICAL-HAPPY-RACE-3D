/* Isolated clipping kernel; not yet called by the game renderer.
 * Camera-space quad, clockwise or counter-clockwise. A clipped convex quad
 * has at most five vertices. UV coordinates follow the same edge parameter.
 * Input/output must not alias. No scene, collision, mapper or VDP writes.
 */
#include <stdint.h>
typedef struct { int16_t x, y, z, u, v; } ClipVertex;

static int16_t edge_value(int16_t a, int16_t b, int16_t num, int16_t den) {
    return a + (int32_t)(b-a)*num/den;
}

uint8_t traffic_clip_quad(const ClipVertex *input, ClipVertex *output) {
    uint8_t i, count=0;
    const ClipVertex *a=input+3, *b;
    for(i=0;i<4;++i) {
        b=input+i;
        if((a->z>=13)!=(b->z>=13)) {
            int16_t num=13-a->z, den=b->z-a->z;
            ClipVertex *p=output+count++;
            p->x=edge_value(a->x,b->x,num,den);
            p->y=edge_value(a->y,b->y,num,den);
            p->z=13;
            p->u=edge_value(a->u,b->u,num,den);
            p->v=edge_value(a->v,b->v,num,den);
        }
        if(b->z>=13) output[count++]=*b;
        a=b;
    }
    return count;
}

#ifdef CLIP_NATIVE_TEST
/* Dedicated synthetic harness: these addresses are NOT runtime allocations. */
void clip_test_entry(void) {
    *(volatile uint8_t *)0xf180=traffic_clip_quad(
        (const ClipVertex *)0xf000,(ClipVertex *)0xf100);
}
#endif
