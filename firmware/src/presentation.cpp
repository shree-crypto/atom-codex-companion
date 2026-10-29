#include <M5Unified.h>
#include <cmath>
#include <algorithm>
#include "presentation.h"
#include "voice_assets.h"

void Presentation::begin(bool soundMuted) {
    muted=soundMuted;
    canvas.setColorDepth(16);
    canvas.setPsram(false);
    buffered=canvas.createSprite(128,128)!=nullptr;
    setColor("blue");
    M5.Speaker.setVolume(120);
}

bool Presentation::setColor(const char* name) {
    if (!strcmp(name,"blue")) eyeColor=M5.Display.color565(57,125,204);
    else if (!strcmp(name,"green")) eyeColor=M5.Display.color565(46,171,121);
    else if (!strcmp(name,"orange")) eyeColor=M5.Display.color565(237,139,53);
    else return false;
    colorName=!strcmp(name,"blue")?"blue":!strcmp(name,"green")?"green":"orange";
    return true;
}

void Presentation::setState(State state, bool notify, uint32_t now) {
    if (state==current && state==State::Working) return; // Keep the ambience buffer running across heartbeats.
    if (state!=current || notify) {
        acknowledge();
        current=state; entered=now;
        if (state==State::Working) { ambient(); return; }
        if (notify && !muted) {
            repeats=(state==State::NeedsInput || state==State::Error) ? 255 :
                (state==State::Finished || state==State::Message) ? 3 : 0;
            repeatAt=now;
        }
    }
}

void Presentation::ambient() {
    if (!muted && current==State::Working && M5.Speaker.isEnabled())
        M5.Speaker.playWav(VOICE_WORKING,sizeof(VOICE_WORKING),UINT32_MAX,0,true);
}

void Presentation::mute(bool value) { muted=value; if (value) acknowledge(); else ambient(); }

void Presentation::acknowledge() { repeats=0; waitingForVoice=false; M5.Speaker.stop(); }

void Presentation::sound(uint32_t now) {
    if (!M5.Speaker.isEnabled() || !repeats || muted || M5.Speaker.isPlaying()) return;
    if (waitingForVoice) {
        waitingForVoice=false;
        repeatAt=now+((current==State::NeedsInput || current==State::Error)?3000:1200);
        return;
    }
    if (int32_t(now-repeatAt)<0) return;
    const uint8_t* data=nullptr; size_t size=0;
    switch (current) {
        case State::NeedsInput: data=VOICE_NEEDS_INPUT; size=sizeof(VOICE_NEEDS_INPUT); break;
        case State::Message: data=VOICE_MESSAGE; size=sizeof(VOICE_MESSAGE); break;
        case State::Finished: data=VOICE_FINISHED; size=sizeof(VOICE_FINISHED); break;
        case State::Error: data=VOICE_ERROR; size=sizeof(VOICE_ERROR); break;
        default: repeats=0; return;
    }
    if (!M5.Speaker.playWav(data,size,1,0,true)) { repeats=0; return; }
    if (repeats<255) --repeats;
    waitingForVoice=true;
}

void Presentation::render(uint32_t now) {
    const uint32_t began=micros();
    lgfx::LGFXBase& display=buffered?static_cast<lgfx::LGFXBase&>(canvas):static_cast<lgfx::LGFXBase&>(M5.Display);
    const uint16_t bg=display.color565(12,23,29), eye=eyeColor;
    display.startWrite(); display.fillScreen(bg);
    const uint32_t age=now-entered;
    const float motion=age*0.003490659f;
    const uint16_t accent=display.color565(255,207,135);
    uint32_t phase=age%5200;
    bool blink=(phase>5000 && phase<5130) && current!=State::NeedsInput && current!=State::Working;
    int gaze=current==State::Working ? int(9*std::sin(motion)) : current==State::Message ? int(3*std::sin(motion)) : 0;
    int height=current==State::Working ? 18 : current==State::NeedsInput ? 42+int(2*std::sin(motion)) : 35;
    if (blink || current==State::Interrupted) height=7;
    if (current==State::Disconnected) height=5;
    if (current==State::Finished && !blink) {
        // Thick happy arcs, using scan lines rather than tiny text glyphs.
        for (int x=0; x<2; ++x) for (int dx=-11; dx<=11; ++dx) {
            int y=58 + (dx*dx)/12;
            display.fillCircle((x?87:40)+dx,y,3,eye);
        }
    } else {
        for (int x=0; x<2; ++x) {
            int y=64+(current==State::Working ? int(3*std::cos(motion+x*3.14159f)) : 0);
            int h=height+(current==State::Message && !blink ? int((x?-7:3)*std::cos(motion)) : 0);
            h=std::max(3,h);
            display.fillRoundRect((x?77:29)+gaze,y-h/2,22,h,std::min(10,h/2),eye);
        }
    }
    if (current==State::Error) {
        display.drawLine(27,38,53,44,eye); display.drawLine(77,44,103,36,eye);
    }
    display.setTextColor(eye,bg); display.setTextSize(2);
    if (current==State::NeedsInput) {
        int d=2+int(2*std::sin(motion));
        display.fillRoundRect(62,14-d,4,13,2,accent); display.fillCircle(64,33,2,accent);
        display.drawLine(44-d,24,39-d,20,accent); display.drawLine(84+d,24,89+d,20,accent);
    }
    if (current==State::Error) display.drawString("!",59,95);
    if (current==State::Message) {
        int y=15-int(3*std::abs(std::sin(motion)));
        display.drawRoundRect(50,y,28,19,4,accent);
        display.drawLine(51,y+2,64,y+12,accent); display.drawLine(64,y+12,77,y+2,accent);
        display.fillCircle(80,y-1,4,accent);
    }
    if (current==State::Working) for(int i=0;i<5;++i)
        display.fillCircle(44+i*10,101,2+int(1.1f*std::sin(motion-i*.8f)),accent);
    if (current==State::Finished || current==State::Message || current==State::NeedsInput) {
        display.drawLine(58,93,64,96,eye); display.drawLine(64,96,70,93,eye);
    }
    if (current==State::Disconnected) {
        display.drawLine(53,101,61,93,eye); display.drawLine(67,101,75,93,eye);
        display.drawLine(60,99,68,95,eye);
    }
    display.setTextSize(1);
    if (muted) display.drawString("M",115,115);
    display.endWrite();
    if (buffered) canvas.pushSprite(0,0);
    ++frames;
    longestFrame=std::max(longestFrame,uint32_t(micros()-began));
}

void Presentation::tick(uint32_t now) {
    sound(now);
    // A stable cadence; never queue catch-up frames after a slow operation.
    const uint32_t clock=micros(), period=buffered?16667:50000;
    const uint32_t elapsed=clock-rendered;
    if (elapsed>=period) {
        rendered=elapsed>=2*period?clock:rendered+period;
        render(now);
    }
}
