#pragma once
#include <stdint.h>

// Fixed-size, wrap-safe interaction state; no allocation or persistent writes.
struct PlayEffects {
    uint8_t charge=0, taps=0;
    bool tickled=false, casting=false;
    uint32_t touchedAt=0, tickledAt=0, chargedAt=0, castAt=0;
    void clear() { *this=PlayEffects{}; }
    void touch(uint32_t now) {
        taps=(taps && uint32_t(now-touchedAt)<=900) ? (taps<3 ? taps+1 : 3) : 1;
        touchedAt=now;
        if(taps>=3) { tickled=true; tickledAt=now; }
    }
    void turn(unsigned steps,uint32_t now) {
        if(casting)return;
        charge=steps>=8-charge ? 8 : charge+steps;
        chargedAt=now;
    }
    bool cast(uint32_t now) {
        if(charge!=8 || casting)return false;
        charge=0; casting=true; castAt=now; tickled=false; taps=0;
        return true;
    }
    void update(uint32_t now) {
        if(charge && uint32_t(now-chargedAt)>=10000)charge=0;
        if(tickled && uint32_t(now-tickledAt)>=5000)tickled=false;
        if(casting && uint32_t(now-castAt)>=6000)casting=false;
    }
};

inline bool testPlayEffects() {
    PlayEffects p;
    p.touch(100);p.touch(500);if(p.tickled)return false;
    p.touch(1400);if(!p.tickled)return false;
    p.update(6399);if(!p.tickled)return false;
    p.update(6400);if(p.tickled)return false;
    p.clear();p.touch(100);p.touch(1001);p.touch(1100);if(p.tickled)return false;
    p.turn(7,2000);if(p.cast(2001))return false;
    p.turn(100,2100);if(p.charge!=8 || !p.cast(2101) || p.cast(2102))return false;
    p.turn(8,2103);if(p.charge)return false;
    p.update(8100);if(!p.casting)return false;
    p.update(8101);if(p.casting)return false;
    p.turn(8,0xfffffff0u);p.update(9983);if(p.charge!=8)return false;
    p.update(9984);if(p.charge)return false;
    p.clear();return !p.charge && !p.casting && !p.tickled && !p.taps;
}
