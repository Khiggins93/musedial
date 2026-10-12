#pragma once
#include <stdint.h>

// No allocations or persistent writes; elapsed arithmetic survives millis wrap.
struct Companion {
    enum Gesture { Idle, Smile, Cuddle, Hug, Tickle };
    Gesture gesture = Idle;
    bool touching = false, history = false;
    uint8_t affection = 0, taps = 0;
    int gazeX = 0, gazeY = 0;
    uint32_t downAt = 0, endedAt = 0, gestureAt = 0, tapAt = 0;
    void clear() { *this = Companion(); }
    static int axis(int coordinate, int current) {
        if(coordinate < 72 || (current == -1 && coordinate < 88)) return -1;
        if(coordinate > 168 || (current == 1 && coordinate > 152)) return 1;
        return 0;
    }
    void move(int x, int y) {
        gazeX = axis(x,gazeX); gazeY = axis(y,gazeY);
    }
    void down(uint32_t now, int x, int y) {
        if(touching) { move(x,y); return; }
        if(!history || uint32_t(now-endedAt)>6000) affection=0;
        touching=true; downAt=now; gesture=Idle; move(x,y);
    }
    void up(uint32_t now) {
        if(!touching)return;
        touching=false;
        uint32_t held=now-downAt;
        taps=held>=450 ? 0 : history && uint32_t(now-tapAt)<=650 ? taps+1 : 1;
        tapAt=now; endedAt=now; history=true;
        if(affection<3)++affection;
        gesture=held>=2000 ? Hug : taps>=3 ? Tickle : affection==1 ? Smile : affection==2 ? Cuddle : Hug;
        if(gesture==Tickle)taps=0;
        gestureAt=now;
    }
    void pet(uint32_t now) { down(now,120,120); up(now); }
    uint32_t duration() const { return gesture==Hug ? 2000 : 1600; }
    void update(uint32_t now) {
        if(gesture!=Idle && uint32_t(now-gestureAt)>=duration())gesture=Idle;
        if(history && !touching && uint32_t(now-endedAt)>6000) { affection=0; taps=0; history=false; }
    }
    bool active() const { return touching || gesture!=Idle; }
    const char* label() const {
        return touching ? "MIRADA" : gesture==Smile ? "SONRISA" : gesture==Cuddle ? "CARINO" : gesture==Hug ? "ABRAZO" : gesture==Tickle ? "COSQUILLAS" : "NINGUNO";
    }
    int frame(uint32_t now) const {
        if(touching)return (gazeY+1)*3+gazeX+1;
        int start=gesture==Smile ? 9 : gesture==Cuddle ? 41 : gesture==Hug ? 73 : 113;
        uint32_t f=(now-gestureAt)/50, count=gesture==Hug ? 40 : 32;
        return start+(f<count ? f : count-1);
    }
};

inline bool testCompanion() {
    Companion c;
    c.pet(100); if(c.gesture!=Companion::Smile)return false;
    c.pet(900); if(c.gesture!=Companion::Cuddle)return false;
    c.pet(1700); if(c.gesture!=Companion::Hug)return false;
    c.update(3699);if(!c.active())return false;
    c.update(3700);if(c.active())return false;
    c.update(7701);c.pet(7800);if(c.gesture!=Companion::Smile)return false;
    c.clear();c.pet(10);c.pet(200);c.pet(400);if(c.gesture!=Companion::Tickle)return false;
    c.clear();c.down(10,0,239);if(c.frame(10)!=6)return false;
    c.move(239,0);if(c.frame(11)!=2)return false;
    c.up(2009);if(c.gesture==Companion::Hug)return false;
    c.down(3000,120,120);c.up(5000);if(c.gesture!=Companion::Hug)return false;
    c.pet(5200);c.pet(5400);if(c.gesture==Companion::Tickle)return false;
    c.clear();c.down(10,120,120);c.down(1900,20,20);c.up(2010);
    if(c.gesture!=Companion::Hug)return false; // Moving never restarts hold timing.
    c.clear();c.down(0xfffffff0u,120,120);c.up(0x7c0);if(c.gesture!=Companion::Hug)return false;
    c.clear();if(c.active() || c.affection)return false;
    return true;
}
