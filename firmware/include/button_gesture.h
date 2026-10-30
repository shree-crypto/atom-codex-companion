#pragma once
#include <cstdint>
enum class ButtonAction { None, ToggleMute, NextTheme };
class ButtonGesture {
    uint32_t began=0;
    bool active=false, consumed=false;
public:
    ButtonAction update(bool pressed,bool down,bool released,uint32_t now) {
        if(pressed){began=now;active=true;consumed=false;}
        if(active&&!consumed&&(down||released)&&uint32_t(now-began)>=1000){
            consumed=true;if(released)active=false;return ButtonAction::NextTheme;
        }
        if(released&&active){active=false;if(!consumed)return ButtonAction::ToggleMute;}
        return ButtonAction::None;
    }
};
