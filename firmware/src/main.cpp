#include <M5Unified.h>
#include <Preferences.h>
#include <algorithm>
#include <cmath>
#include "presentation.h"

Receiver receiver;
Presentation presentation;
Preferences settings;
char line[513]{};
size_t used=0;
bool dropping=false, longPress=false;
uint32_t pressedAt=0, readyAt=0;

// Local, explicitly requested diagnostic: keep raw microphone samples in RAM only.
void microphoneTest() {
    presentation.acknowledge();
    M5.Speaker.end();
    static int16_t samples[1600];
    memset(samples,0,sizeof(samples));
    bool started=M5.Mic.begin();
    bool recorded=started && M5.Mic.record(samples,1600,16000);
    uint32_t began=millis();
    while (recorded && M5.Mic.isRecording() && uint32_t(millis()-began)<1000) delay(1);
    recorded=recorded && !M5.Mic.isRecording();
    M5.Mic.end();
    double mean=0, energy=0; int peak=0;
    for (int value:samples) mean+=value;
    mean/=1600;
    for (int value:samples) {
        const double centered=value-mean;
        energy+=centered*centered;
        peak=std::max(peak,int(std::abs(centered)));
    }
    memset(samples,0,sizeof(samples));
    bool speaker=M5.Speaker.begin();
    Serial.printf("{\"v\":1,\"kind\":\"mic_test\",\"recorded\":%s,\"rms\":%.2f,\"peak\":%d,\"speaker_restored\":%s}\n",
        recorded?"true":"false",std::sqrt(energy/1600),peak,speaker?"true":"false");
}

void setup() {
    auto config=M5.config();
    config.clear_display=true;
    config.external_speaker.atomic_echo=true;
    config.internal_mic=true;
    config.internal_imu=false;
    config.internal_rtc=false;
    M5.begin(config);
    M5.Mic.end(); // Capture is enabled only by the explicit MIC_TEST diagnostic.
    M5.Speaker.begin();
    M5.Display.setBrightness(100);
    Serial.begin(115200);
    settings.begin("atom-avatar",false);
    presentation.begin(settings.getBool("muted",false));
    presentation.setColor(settings.getString("color","blue").c_str());
}

void loop() {
    M5.update();
    uint32_t now=millis();
    for (unsigned budget=0; budget<256 && Serial.available(); ++budget) {
        int value=Serial.read();
        if (value=='\n') {
            if (!dropping && used) {
                if (line[used-1]=='\r') --used;
                line[used]='\0';
                if (!strcmp(line,"MIC_TEST")) microphoneTest();
                else if (!strncmp(line,"COLOR ",6)) {
                    const bool accepted=presentation.setColor(line+6);
                    if (accepted) settings.putString("color",presentation.color());
                    Serial.printf("{\"v\":1,\"kind\":\"color\",\"accepted\":%s,\"color\":\"%s\"}\n",accepted?"true":"false",presentation.color());
                }
                else if (!strcmp(line,"STATUS")) {
                    State visible=receiver.expired(now)?State::Disconnected:receiver.state();
                    Serial.printf("{\"v\":1,\"kind\":\"status\",\"state\":\"%s\",\"muted\":%s,\"audio_playing\":%s,\"audio_enabled\":%s,\"buffered\":%s,\"color\":\"%s\",\"frames\":%lu,\"max_frame_us\":%lu}\n",
                        stateName(visible),presentation.isMuted()?"true":"false",M5.Speaker.isPlaying()?"true":"false",M5.Speaker.isEnabled()?"true":"false",presentation.isBuffered()?"true":"false",presentation.color(),static_cast<unsigned long>(presentation.frameCount()),static_cast<unsigned long>(presentation.maxFrameUs()));
                }
                else if (receiver.accept(line,now)) presentation.setState(receiver.state(),receiver.cue(),now);
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
            Serial.printf("{\"v\":1,\"device\":\"atom-companion\",\"kind\":\"ready\",\"firmware\":\"2.4-s3r-lofi\",\"audio\":%s,\"psram_bytes\":%u,\"board_id\":%u}\n",
                M5.Speaker.isEnabled()?"true":"false",unsigned(ESP.getPsramSize()),unsigned(M5.getBoard()));
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
