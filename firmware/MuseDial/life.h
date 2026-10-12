#pragma once
#include <stdint.h>

// Pure controller: the caller supplies a clock and random words. No IO or heap.
struct Life {
    enum State { Manual, Awake, Relaxed, Yawning, Asleep, Greeting };
    State state = Awake;
    bool halloween = false, spontaneous = false, touching = false, consumeTouch = false;
    uint32_t lastInteraction = 0, scheduledAt = 0, interval = 20000, actionAt = 0;
    int previous = -1, pending = 0;

    bool asleep() const { return state == Asleep || state == Yawning; }
    uint32_t idle(uint32_t now) const { return uint32_t(now - lastInteraction); }
    const char* label(bool screenOff) const {
        static const char* names[] = {"manual", "awake", "relaxed", "yawning", "asleep", "greeting"};
        return screenOff ? "screen_off" : names[state];
    }
    void schedule(uint32_t now, uint32_t random) {
        scheduledAt = now; interval = 20000 + random % 15001;
    }
    void start(uint32_t now, uint32_t random) {
        state = Awake; spontaneous = false; pending = 0;
        lastInteraction = now; schedule(now, random);
    }
    void manual(uint32_t now) {
        state = Manual; spontaneous = false; pending = -1; lastInteraction = now;
    }
    // Return true only when this interaction wakes the character.
    bool interact(uint32_t now, uint32_t random, bool greet = true) {
        bool woke = asleep();
        lastInteraction = now;
        if(state == Manual) return false;
        spontaneous = false; schedule(now, random);
        if(woke && greet) {
            state = Greeting; actionAt = now; pending = halloween ? 3 : 6;
        } else if(state != Greeting || !greet) { state = Awake; pending = 0; }
        return woke;
    }
    bool down(uint32_t now, uint32_t random) {
        if(!touching) {
            touching = true;
            consumeTouch = interact(now, random);
        } else lastInteraction = now;
        return consumeTouch;
    }
    bool up(uint32_t now, uint32_t random) {
        bool consumed = consumeTouch;
        touching = consumeTouch = false;
        interact(now, random);
        return consumed;
    }
    // Return a new base clip or -1. Effects remain owned by the caller.
    int tick(uint32_t now, bool busy, uint32_t random) {
        if(state == Manual || busy || (touching && !consumeTouch)) return -1;
        if(state == Greeting && uint32_t(now-actionAt) >= 2000) {
            state = Awake; pending = 0; schedule(now, random);
        } else if(state == Yawning && uint32_t(now-actionAt) >= 2000) {
            state = Asleep; pending = halloween ? 10 : 4;
        } else if(state == Awake || state == Relaxed) {
            if(idle(now) >= 300000) {
                state = Yawning; actionAt = now; spontaneous = false;
                pending = halloween ? 11 : 8;
            } else if(idle(now) >= 180000) {
                if(state != Relaxed) pending = 0;
                state = Relaxed; spontaneous = false;
            } else if(spontaneous && uint32_t(now-actionAt) >= 2000) {
                spontaneous = false; pending = 0;
            } else if(!spontaneous && uint32_t(now-scheduledAt) >= interval) {
                int choice = random % (previous < 0 ? 4 : 3);
                if(previous >= 0 && choice >= previous) ++choice;
                previous = choice;
                static const int normal[] = {1, 2, 5, 6};
                static const int spooky[] = {1, 2, 4, 3};
                pending = halloween ? spooky[choice] : normal[choice];
                spontaneous = true; actionAt = now;
                schedule(now, random);
            }
        }
        int result = pending; pending = -1; return result;
    }
};
