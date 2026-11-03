#pragma save
#pragma opt_code_speed
/* Ordinary traffic for the continuous journey.
 * Included after the shared drawing helpers; no extra input or camera shake.
 */
#ifndef ALPINE_ENCOUNTERS_H
#define ALPINE_ENCOUNTERS_H
#define TRAFFIC_COUNT 5
#define RIVAL_COUNT 0
#define SAME_DIRECTION_COUNT 5

volatile u16 traffic_z[TRAFFIC_COUNT],passes,hits,event_tick,chain,best_chain,near_passes;
volatile s8 traffic_lane[TRAFFIC_COUNT];
s8 traffic_target[TRAFFIC_COUNT];
volatile u8 traffic_tag[TRAFFIC_COUNT],recovery_timer,traffic_near[TRAFFIC_COUNT];
u16 traffic_gap[TRAFFIC_COUNT],traffic_previous_gap[TRAFFIC_COUNT];
s16 traffic_screen_x[TRAFFIC_COUNT],traffic_screen_y[TRAFFIC_COUNT];
u8 traffic_clip[TRAFFIC_COUNT],traffic_width[TRAFFIC_COUNT],traffic_visible[TRAFFIC_COUNT],traffic_order[TRAFFIC_COUNT];
u8 notice,notice_timer,recovery_speed,contact_side;
volatile u8 traffic_contact[TRAFFIC_COUNT];
volatile u8 collision_pulse;
u16 cached_passes;
u8 traffic_scale_lut[513];
extern volatile u8 simulation_substep;
u8 traffic_step_move[TRAFFIC_COUNT],traffic_move_fraction[TRAFFIC_COUNT];

static void init_encounters(void){
    u8 i;
    u16 gap;
    /* The same nearest-depth choice, calculated once instead of searching
     * sixteen 16-bit depth values for each visible car on every frame. */
    i=0;
    for(gap=0;gap<=512;++gap){
        if(i<15&&gap>((event_depth[i]+event_depth[i+1])>>1))++i;
        traffic_scale_lut[gap]=i;
    }

    for(i=0;i<TRAFFIC_COUNT;++i){
        traffic_z[i]=240+(u16)i*240;
        traffic_lane[i]=-40;traffic_target[i]=traffic_lane[i];traffic_tag[i]=0;traffic_near[i]=0;traffic_contact[i]=0;
        traffic_previous_gap[i]=traffic_z[i];traffic_visible[i]=0;traffic_step_move[i]=traffic_move_fraction[i]=0;
    }
    passes=hits=event_tick=chain=best_chain=near_passes=0;
    recovery_timer=0;notice=0;notice_timer=0;collision_pulse=0;contact_side=0;
    cached_passes=65535;
}
static void prepare_traffic(void){
    u8 i,j,k,t,*p;
    u16 gap,part,span; s16 cx,gy,rw,signed_gap;u8 *q;
    for(i=0;i<TRAFFIC_COUNT;++i){
        bgm_poll();
        traffic_order[i]=i;traffic_visible[i]=0;
        gap=(traffic_z[i]-distance)&16383;traffic_gap[i]=gap;
        /* Chase main view shows traffic ahead of the driver reference only.
         * Rear traffic remains in the simulation and rear mirror. */
        if(!mode||(gap>512&&gap<(camera_mode?16332:16304)))continue;
        signed_gap=gap>8192?(s16)gap-16384:(s16)gap;
        gap=signed_gap<28?28:signed_gap;
        k=traffic_scale_lut[gap];
        p=profile+EVENT_PROJECT_OFFSET+((u16)k<<2);
        if(gap<event_depth[k]&&k)--k;
        p=profile+EVENT_PROJECT_OFFSET+((u16)k<<2);
        cx=(s8)p[0];gy=p[1];rw=p[2];
        if(k<15&&gap>=28){
            q=p+4;part=gap-event_depth[k];span=event_depth[k+1]-event_depth[k];
            cx+=interpolate((s16)(s8)q[0]-cx,(u8)part,(u8)span);
            gy+=interpolate((s16)q[1]-gy,(u8)part,(u8)span);
            rw+=interpolate((s16)q[2]-rw,(u8)part,(u8)span);
        }
        traffic_clip[i]=p[3];
        if(camera_mode){cx=view_x(128+cx,(u8)rw)-128;gy=view_y(gy,(u8)rw);traffic_clip[i]=p[3]>=168?212:view_y(p[3],(u8)rw);rw=view_width((u8)rw);}
        traffic_width[i]=(u8)rw;
        traffic_screen_x[i]=128+cx-camera_shift((u8)rw>>1)+(s16)traffic_lane[i]*rw/64;
        traffic_screen_y[i]=gy;
        traffic_visible[i]=1;
    }
    for(i=0;i<TRAFFIC_COUNT-1;++i)for(j=i+1;j<TRAFFIC_COUNT;++j){
        if((s16)(traffic_gap[traffic_order[i]]<<2)<(s16)(traffic_gap[traffic_order[j]]<<2)){
            t=traffic_order[i];traffic_order[i]=traffic_order[j];traffic_order[j]=t;
        }
    }
}

void step_encounters(void){
    u8 i,j,move,limit,blocked_left,blocked_right;
    s16 dx;
    s8 target;
    u16 gap,spawn;
    if(mode==1){
        if(!simulation_substep){
        ++event_tick;
        if(notice_timer)--notice_timer;
        if(collision_pulse)--collision_pulse;
        if(recovery_timer){--recovery_timer;if(speed>recovery_speed)speed=recovery_speed;}
        }
        for(i=0;i<TRAFFIC_COUNT;++i){
            traffic_previous_gap[i]=(traffic_z[i]-distance)&16383;
            if(!simulation_substep){
            target=-40;
            {
                /* Change lanes only with a car-length clearance in both directions. */
                if(i==1&&traffic_lane[i]==traffic_target[i]){
                blocked_left=blocked_right=0;
                for(j=0;j<TRAFFIC_COUNT;++j){
                    if(i==j)continue;
                    dx=(s16)((traffic_z[j]-traffic_z[i])<<2)/4;
                    if(dx<=-120||dx>=240)continue;
                    if(traffic_lane[j]<16)blocked_left=1;
                    if(traffic_lane[j]>-16)blocked_right=1;
                }
                dx=(s16)((distance-traffic_z[i])<<2)/4;
                if(dx>-120&&dx<240){if(player_x<16)blocked_left=1;if(player_x>-16)blocked_right=1;}
                if(blocked_left)target=blocked_right?traffic_lane[i]:40;
                traffic_target[i]=target;
                }
                target=traffic_target[i];
                if(traffic_lane[i]<target)traffic_lane[i]+=2;
                if(traffic_lane[i]>target)traffic_lane[i]-=2;
                move=4+(i%3);if(i==1&&traffic_lane[i]>-20)move=7;
            }
            {
            /* A following car brakes instead of passing through a lead car. */
            for(j=0;j<TRAFFIC_COUNT;++j){
                if(i==j)continue;
                dx=traffic_lane[i]-traffic_lane[j];if(dx<0)dx=-dx;
                gap=(traffic_z[j]-traffic_z[i])&16383;
                if(dx<34&&gap<104){limit=gap>96?gap-96:0;if(move>limit)move=limit;}
            }
            {
                dx=traffic_lane[i]-player_x;if(dx<0)dx=-dx;
                gap=(distance-traffic_z[i])&16383;
                if(dx<34&&gap<104){limit=gap>96?gap-96:0;if(move>limit)move=limit;}
                traffic_step_move[i]=move;
            }
            }
            }
            traffic_move_fraction[i]+=traffic_step_move[i];
            move=traffic_move_fraction[i]>>1;traffic_move_fraction[i]&=1;
            traffic_z[i]=(traffic_z[i]+move)&16383;
            gap=(traffic_z[i]-distance)&16383;traffic_gap[i]=gap;

            if(gap<=12||(gap>8192&&(traffic_tag[i]==2||traffic_previous_gap[i]<128))){
                /* A vehicle coming from behind is not an earned overtake. */
                if(!traffic_tag[i]&&traffic_previous_gap[i]<128){
                    if(passes<999)++passes;
                    if(chain<999)++chain;if(chain>best_chain)best_chain=chain;
                    if(traffic_near[i])++near_passes;
                    if(notice!=2||!notice_timer){notice=1;notice_timer=36;}
                }

                if(gap<=12||traffic_tag[i]!=2){traffic_tag[i]=2;continue;}
                if(gap>15872)continue; /* Retain actual traffic within the rear mirror range. */
                spawn=(distance+1000+(u16)i*240)&16383;
                for(j=0;j<TRAFFIC_COUNT;++j){
                    if(j==i)continue;
                    gap=(traffic_z[j]-spawn)&16383;
                    if(gap<180||gap>16204){spawn=(spawn+240)&16383;j=255;}
                }
                traffic_z[i]=spawn;traffic_gap[i]=(spawn-distance)&16383;
                traffic_lane[i]=-40;traffic_target[i]=traffic_lane[i];traffic_tag[i]=0;traffic_near[i]=0;traffic_contact[i]=0;traffic_move_fraction[i]=0;
            }
        }

    }
    /* Each movement above already stores its collision gap; project once per frame. */
    if(mode!=1||recovery_timer)return;
    for(i=0;i<TRAFFIC_COUNT;++i){
        if(traffic_tag[i]==2)continue;
        dx=player_x-traffic_lane[i];if(dx<0)dx=-dx;
        /* Eye-to-front distance is about 1000 world units, not 1800.
         * The forgiving lateral hull is smaller than the visible body.
         * One impact per overlap; re-arm only after genuine separation. */
        if(traffic_contact[i]){
            if(traffic_gap[i]>56||dx>=34)traffic_contact[i]=0;
            continue;
        }
        if(traffic_gap[i]>40||traffic_gap[i]<16)continue;
        if(dx<28){
            traffic_contact[i]=1;traffic_tag[i]=1;++hits;chain=0;recovery_speed=40;if(speed>recovery_speed)speed=recovery_speed;
            recovery_timer=20;notice=2;notice_timer=30;collision_pulse=6;
            contact_side=traffic_lane[i]<player_x-8?1:(traffic_lane[i]>player_x+8?2:0);
        }else if(dx<42)traffic_near[i]=1;
    }
}
static void build_encounter_ui(void){}
#endif

#pragma restore
