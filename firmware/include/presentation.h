#pragma once
#include <cstdint>
#include "protocol.h"

class Presentation {
    State current=State::Disconnected;
    bool muted=false;
    uint32_t entered=0, rendered=0, repeatAt=0;
    uint8_t repeats=0;
    bool waitingForVoice=false;
    void render(uint32_t now);
    void sound(uint32_t now);
public:
    void begin(bool soundMuted);
    void setState(State state, bool notify, uint32_t now);
    void tick(uint32_t now);
    void mute(bool value);
    void acknowledge();
    bool isMuted() const { return muted; }
};
