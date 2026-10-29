#pragma once
#include <cstdint>
#include <cmath>
#include <algorithm>

struct AxisCalibration { bool enabled=false; uint16_t low=0, neutral=0, high=0; };
struct Calibration { bool confirmed=false; AxisCalibration axis[2]{}; };
struct Pose { float pan=0, tilt=0; };

class Gesture {
public:
    enum Kind { None, Nod, Glance };
private:
    Kind kind=None;
    uint32_t began=0;
public:
    void start(Kind wanted, bool notify, uint32_t now) { kind=notify ? wanted : None; began=now; }
    Pose pose(uint32_t now) const {
        uint32_t age=now-began;
        if (kind==Nod && age<1400) return {0,0.25f*std::sin(age*0.0045f)};
        if (kind==Glance && age<1000) return {0.2f,0};
        return {};
    }
};

class Motion {
    Calibration calibration{};
    float current[2]{}, target[2]{};
    bool enabled=false, clockStarted=false;
    uint32_t last=0;
public:
    bool configure(const Calibration& c) {
        disable();
        bool any=false;
        if (!c.confirmed) return false;
        for (const auto& a : c.axis) {
            if (!a.enabled) continue;
            any=true;
            if (a.low < 800 || a.high > 2200 || a.low >= a.neutral || a.neutral >= a.high) return false;
        }
        if (!any) return false;
        calibration=c;
        for (int i=0; i<2; ++i) current[i]=target[i]=c.axis[i].neutral;
        enabled=true;
        return true;
    }
    void disable() { enabled=false; clockStarted=false; }
    bool active() const { return enabled; }
    bool axisEnabled(int i) const { return enabled && i>=0 && i<2 && calibration.axis[i].enabled; }
    void setPose(Pose pose) {
        if (!enabled) return;
        float values[2]={pose.pan, pose.tilt};
        for (int i=0; i<2; ++i) {
            if (!std::isfinite(values[i])) { disable(); return; }
            float v=std::max(-1.0f, std::min(1.0f, values[i]));
            const auto& a=calibration.axis[i];
            target[i]=a.neutral + v*(v<0 ? a.neutral-a.low : a.high-a.neutral);
        }
    }
    void tick(uint32_t now) {
        if (!enabled) return;
        if (!clockStarted) { last=now; clockStarted=true; return; }
        uint32_t elapsed=now-last; last=now;
        float step=std::min(uint32_t(50), elapsed)*0.5f;
        for (int i=0; i<2; ++i) {
            float delta=target[i]-current[i];
            current[i]+=std::max(-step, std::min(step, delta));
        }
    }
    uint16_t pulse(int i) const { return (i>=0 && i<2) ? uint16_t(current[i]+0.5f) : 0; }
};
