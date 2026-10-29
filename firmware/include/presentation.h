#pragma once
#include <cstdint>
#include "protocol.h"

class Presentation {
    State current=State::Disconnected;
    bool muted=false;
    uint32_t entered=0, rendered=0, cueStarted=0, lastCue=0;
    uint8_t notes=0;
    uint8_t playingNote=255;
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
