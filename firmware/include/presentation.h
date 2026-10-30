#pragma once
#include <cstdint>
#include <M5Unified.h>
#include "protocol.h"
#include "pokemon_faces.h"

class Presentation {
    M5Canvas canvas{&M5.Display};
    bool buffered=false;
    uint16_t eyeColor=0;
    const char* colorName="orange";
    uint32_t frames=0, longestFrame=0;
    State current=State::Disconnected;
    bool muted=false;
    uint8_t themeIndex=0;
    uint32_t entered=0, rendered=0, repeatAt=0;
    uint8_t repeats=0;
    bool waitingForVoice=false;
    void render(uint32_t now);
    void sound(uint32_t now);
    void ambient();
public:
    void begin(bool soundMuted,uint8_t theme=0);
    void nextTheme(){themeIndex=(themeIndex+1)%FaceThemeCount;}
    uint8_t theme()const{return themeIndex;}
    const char* themeName()const{return FaceThemeNames[themeIndex];}
    void setState(State state, bool notify, uint32_t now);
    void tick(uint32_t now);
    void mute(bool value);
    void acknowledge();
    bool setColor(const char* name);
    const char* color() const { return colorName; }
    bool isBuffered() const { return buffered; }
    uint32_t frameCount() const { return frames; }
    uint32_t maxFrameUs() const { return longestFrame; }
    bool isMuted() const { return muted; }
};
