#include <M5Unified.h>
#include <Preferences.h>
#include "presentation.h"

Receiver receiver;
Presentation presentation;
Preferences settings;
char line[513]{};
size_t used=0;
bool dropping=false, longPress=false;
uint32_t pressedAt=0, readyAt=0;

void setup() {
    auto config=M5.config();
    config.clear_display=true;
    M5.begin(config);
    M5.Display.setBrightness(100);
    Serial.begin(115200);
    settings.begin("atom-avatar",false);
    presentation.begin(settings.getBool("muted",false));
}

void loop() {
    M5.update();
    uint32_t now=millis();
    for (unsigned budget=0; budget<256 && Serial.available(); ++budget) {
        int value=Serial.read();
        if (value=='\n') {
            if (!dropping && used) {
                line[used]='\0';
                if (receiver.accept(line,now)) presentation.setState(receiver.state(),receiver.cue(),now);
            }
            used=0; dropping=false;
        } else if (!dropping) {
            if (used>=512) { used=0; dropping=true; }
            else line[used++]=char(value);
        }
    }
    if (receiver.expired(now)) {
        presentation.setState(State::Disconnected,false,now);
        if (uint32_t(now-readyAt)>=1000) {
            readyAt=now;
            Serial.printf("{\"v\":1,\"device\":\"atom-companion\",\"kind\":\"ready\",\"audio\":%s}\n",M5.Speaker.isEnabled()?"true":"false");
        }
    }
    if (M5.BtnA.wasPressed()) { pressedAt=now; longPress=false; }
    if (M5.BtnA.isPressed() && !longPress && uint32_t(now-pressedAt)>=900) {
        longPress=true;
        presentation.mute(!presentation.isMuted());
        settings.putBool("muted",presentation.isMuted());
    }
    if (M5.BtnA.wasReleased() && !longPress) {
        Serial.printf("{\"v\":1,\"kind\":\"ack\",\"epoch\":\"%s\",\"seq\":%lu}\n",receiver.epoch(),static_cast<unsigned long>(receiver.seq()));
        // Silence locally even if the host is momentarily absent.
        presentation.acknowledge();
    }
    presentation.tick(now);
    delay(1);
}
