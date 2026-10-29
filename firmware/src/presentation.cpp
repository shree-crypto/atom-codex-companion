#include <M5Unified.h>
#include <cmath>
#include "presentation.h"

void Presentation::begin(bool soundMuted) {
    muted=soundMuted;
    M5.Speaker.setVolume(48);
}

void Presentation::setState(State state, bool notify, uint32_t now) {
    if (state!=current || notify) {
        current=state; entered=now;
    }
    if (state==State::Disconnected || state==State::Interrupted) {
        notes=0;
        M5.Speaker.stop();
    }
    if (notify && !muted && (lastCue==0 || uint32_t(now-lastCue)>=2500)) {
        notes=(state==State::Finished ? 3 : (state==State::NeedsInput || state==State::Error ? 2 : 1));
        cueStarted=now; lastCue=now; playingNote=255;
    }
}

void Presentation::mute(bool value) { muted=value; if (value) acknowledge(); }

void Presentation::acknowledge() { notes=0; playingNote=255; M5.Speaker.stop(); }

void Presentation::sound(uint32_t now) {
    if (!M5.Speaker.isEnabled()) return;
    if (!notes || muted) return;
    uint32_t age=now-cueStarted;
    unsigned note=age/180;
    if (note>=notes) { notes=0; M5.Speaker.stop(); return; }
    unsigned frequency=(current==State::Error ? 440-note*80 : 880+note*220);
    if (playingNote!=note) { playingNote=note; M5.Speaker.tone(frequency,100); }
}

void Presentation::render(uint32_t now) {
    auto& display=M5.Display;
    const uint16_t bg=display.color565(12,23,29), eye=display.color565(157,244,200);
    display.startWrite(); display.fillScreen(bg);
    uint32_t phase=now%5200;
    bool blink=(phase<130) && current!=State::NeedsInput;
    int gaze=current==State::Working ? int(4*std::sin(now*0.0009f)) : current==State::Message ? 6 : 0;
    int height=current==State::Working ? 27 : current==State::NeedsInput ? 43 : 36;
    if (blink || current==State::Interrupted) height=7;
    if (current==State::Disconnected) height=5;
    if (current==State::Finished && !blink) {
        // Thick happy arcs, using scan lines rather than tiny text glyphs.
        for (int x=0; x<2; ++x) for (int dx=-11; dx<=11; ++dx) {
            int y=58 + (dx*dx)/12;
            display.fillCircle((x?87:40)+dx,y,3,eye);
        }
    } else {
        for (int x=0; x<2; ++x)
            display.fillRoundRect((x?77:29)+gaze,64-height/2,22,height,std::min(10,height/2),eye);
    }
    if (current==State::Error) {
        display.drawLine(27,38,53,44,eye); display.drawLine(77,44,103,36,eye);
    }
    display.setTextColor(eye,bg); display.setTextSize(2);
    if (current==State::NeedsInput) display.drawString("?",59,12);
    if (current==State::Error) display.drawString("!",59,95);
    if (current==State::Message) display.fillCircle(28,27,4,eye);
    if (current==State::Disconnected) {
        display.drawLine(53,101,61,93,eye); display.drawLine(67,101,75,93,eye);
        display.drawLine(60,99,68,95,eye);
    }
    display.setTextSize(1);
    if (muted) display.drawString("M",115,115);
    display.endWrite();
}

void Presentation::tick(uint32_t now) {
    sound(now);
    if (uint32_t(now-rendered)>=50) { rendered=now; render(now); }
}
