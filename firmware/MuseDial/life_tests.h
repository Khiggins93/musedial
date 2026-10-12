#pragma once
#include "life.h"
#include <initializer_list>

// Identical deterministic checks run on the CI host and on the ESP32.
inline bool testLife() {
    for(unsigned theme=0;theme<2;++theme) {
        for(uint32_t origin : {uint32_t(0), uint32_t(0xfffff000)}) {
            Life l; l.halloween=theme; l.start(origin,0);
            auto at=[origin](uint32_t elapsed) { return uint32_t(origin+elapsed); };
            if(l.tick(at(0),false,0)!=0 || l.tick(at(19999),false,0)!=-1)return false;
            int first=l.tick(at(20000),false,0);
            if(first!=1 || !l.spontaneous || l.tick(at(21999),false,0)!=-1)return false;
            if(l.tick(at(22000),false,0)!=0 || l.spontaneous)return false;
            int second=l.tick(at(40000),false,0);
            if(second==first || second!=2)return false;
            l=Life{}; l.halloween=theme; l.start(at(0),15000);
            if(l.interval!=35000 || l.tick(at(34999),false,0)!=0 || l.spontaneous)return false;
            if(l.tick(at(35000),false,0)!=1)return false;
            l.start(at(0),0); l.tick(at(0),false,0);
            l.tick(at(179999),false,0);
            if(l.state!=Life::Awake)return false;
            if(l.tick(at(180000),false,0)!=0 || l.state!=Life::Relaxed || l.spontaneous)return false;
            if(l.tick(at(299999),false,0)!=-1 || l.state!=Life::Relaxed)return false;
            if(l.tick(at(300000),false,0)!=(theme?11:8) || l.state!=Life::Yawning)return false;
            if(l.tick(at(301999),false,0)!=-1)return false;
            if(l.tick(at(302000),false,0)!=(theme?10:4) || l.state!=Life::Asleep)return false;
            if(l.tick(at(600000),false,0)!=-1 || l.idle(at(600000))!=600000)return false;
            if(!l.down(at(600001),0) || l.state!=Life::Greeting)return false;
            if(l.tick(at(600001),false,0)!=(theme?3:6))return false;
            l.down(at(603000),0); l.tick(at(603000),false,0);
            if(!l.consumeTouch || !l.up(at(604000),0) || l.touching)return false;
            if(l.down(at(604001),0) || l.up(at(606002),0))return false;
            // Busy effects postpone sleep; the complete yawn plays afterwards.
            l.start(at(0),0); l.tick(at(0),false,0);
            if(l.tick(at(400000),true,0)!=-1 || l.state!=Life::Awake)return false;
            if(l.tick(at(400001),false,0)!=(theme?11:8))return false;
            if(l.tick(at(402000),false,0)!=-1)return false;
            if(l.tick(at(402001),false,0)!=(theme?10:4))return false;
            if(!l.interact(at(402002),0) || l.state!=Life::Greeting)return false;
            l.start(at(0),0); l.tick(at(300000),false,0); l.tick(at(302000),false,0);
            if(!l.interact(at(302001),0,false) || l.state!=Life::Awake)return false;
            l.manual(at(302001));
            if(l.tick(at(900000),false,0)!=-1 || l.state!=Life::Manual)return false;
            l.interact(at(900001),0);
            if(l.state!=Life::Manual || l.idle(at(900002))!=1)return false;
            l.halloween=!theme; l.start(at(900003),0);
            if(l.tick(at(900003),false,0)!=0 || l.state!=Life::Awake || l.idle(at(900003)))return false;
            l.down(at(900004),0);
            if(l.tick(at(1300000),false,0)!=-1 || l.state!=Life::Awake)return false;
            l.up(at(1300001),0);
            if(l.idle(at(1300001)))return false;
        }
    }
    return true;
}
