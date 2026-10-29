#pragma once
#include <ArduinoJson.h>
#include <cstdint>
#include <cstring>

enum class State { Idle, Working, NeedsInput, Message, Finished, Error, Interrupted, Disconnected };
inline const char* stateName(State state) {
    static const char* names[]={"idle","working","needs_input","message","finished","error","interrupted","disconnected"};
    return names[static_cast<int>(state)];
}

class Receiver {
    bool connected=false, haveFrame=false, notification=false;
    uint32_t seenAt=0, sequence=0;
    char boot[41]{};
    State shown=State::Disconnected;
public:
    bool accept(const char* line, uint32_t now) {
        StaticJsonDocument<1024> doc;
        if (deserializeJson(doc, line)) return false;
        if (!doc["v"].is<unsigned>() || doc["v"].as<unsigned>()!=1 || doc["v"].is<bool>()) return false;
        if (!doc["seq"].is<uint32_t>() || doc["seq"].is<bool>() || !doc["notify"].is<bool>()) return false;
        if (!doc["epoch"].is<const char*>() || !doc["state"].is<const char*>() || !doc["session"].is<const char*>()) return false;
        const char* epoch=doc["epoch"], *name=doc["state"], *session=doc["session"];
        if (!*epoch || strlen(epoch)>40 || strlen(session)>64) return false;
        int index=-1;
        for (int i=0; i<8; ++i) if (!strcmp(name, stateName(static_cast<State>(i)))) index=i;
        if (index<0) return false;
        uint32_t seq=doc["seq"];
        bool sameEpoch=haveFrame && !strcmp(epoch, boot);
        if (sameEpoch && seq<sequence) return false;
        if (sameEpoch && seq==sequence && static_cast<State>(index)!=shown) return false;
        expired(now);
        bool changed=!sameEpoch || seq!=sequence;
        notification=connected && changed && doc["notify"].as<bool>();
        strcpy(boot, epoch); sequence=seq; shown=static_cast<State>(index);
        connected=haveFrame=true; seenAt=now;
        return true;
    }
    bool expired(uint32_t now) {
        if (connected && uint32_t(now-seenAt)>=5000) connected=false;
        return !connected;
    }
    State state() const { return shown; }
    bool cue() const { return notification; }
    uint32_t seq() const { return sequence; }
    const char* epoch() const { return boot; }
};
