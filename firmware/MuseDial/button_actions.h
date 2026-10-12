#pragma once
#include <stdint.h>
// Pure state machine shared by physical polling and boundary self-tests.
enum class ButtonAction { None, Wake, Click, Sleep, Theme };
struct ButtonActions {
  uint32_t since=0;
  bool down=false, consumed=false, woke=false;
  ButtonAction update(bool pressed, uint32_t now, bool sleeping) {
    if (pressed && !down) {
      down=true; consumed=false; woke=sleeping; since=now;
      if (sleeping) return ButtonAction::Wake;
    }
    if (pressed && down && !consumed && uint32_t(now-since)>3000) {
      consumed=true; return ButtonAction::Theme;
    }
    if (!pressed && down) {
      down=false;
      if (consumed) return ButtonAction::None;
      if (uint32_t(now-since)>3000) return ButtonAction::Theme;
      if (uint32_t(now-since)>=1000) return ButtonAction::Sleep;
      if (!woke) return ButtonAction::Click;
    }
    return ButtonAction::None;
  }
};
inline bool testButtonActions() {
  const uint32_t times[]={900,999,1000,1100,2900,3000,3001,3100,6000};
  for (auto duration:times) {
    ButtonActions b;
    if (b.update(true,100,false)!=ButtonAction::None) return false;
    auto held=b.update(true,100+duration,false);
    auto release=b.update(false,101+duration,false);
    if (duration>3000) {
      if (held!=ButtonAction::Theme || release!=ButtonAction::None) return false;
    } else if (duration==3000) {
      if (held!=ButtonAction::None || release!=ButtonAction::Theme) return false;
    } else if (held!=ButtonAction::None || release!=(duration>=999?ButtonAction::Sleep:ButtonAction::Click)) return false;
  }
  ButtonActions b;
  if (b.update(true,0,true)!=ButtonAction::Wake || b.update(false,100,false)!=ButtonAction::None) return false;
  b=ButtonActions{};
  b.update(true,0,false);
  if(b.update(true,3001,false)!=ButtonAction::Theme || b.update(true,9000,false)!=ButtonAction::None || b.update(false,9001,false)!=ButtonAction::None) return false;
  b=ButtonActions{}; b.update(true,UINT32_MAX-1000,false);
  return b.update(true,2500,false)==ButtonAction::Theme;
}
