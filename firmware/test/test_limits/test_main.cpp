#include <cassert>
#include <cstdint>
#include "motion.h"
#include "protocol.h"

int main() {
    Motion motion;
    Calibration uncalibrated{};
    assert(!motion.configure(uncalibrated));
    assert(!motion.active());

    Gesture gesture;
    gesture.start(Gesture::Nod, true, 0);
    assert(gesture.pose(200).tilt != 0);
    gesture.start(Gesture::Nod, false, 300);
    assert(gesture.pose(500).tilt == 0);
    Calibration valid{};
    valid.confirmed = true;
    valid.axis[0] = {true, 1200, 1500, 1800};
    valid.axis[1] = {true, 1300, 1500, 1700};
    assert(motion.configure(valid));
    motion.setPose({99.0f, -99.0f});
    motion.tick(0xFFFFFFF0u);
    motion.tick(0x00000020u);
    assert(motion.pulse(0) >= 1200 && motion.pulse(0) <= 1500 + 50);
    assert(motion.pulse(1) >= 1450 && motion.pulse(1) <= 1700);
    for (uint32_t t=100; t<2000; t+=20) motion.tick(t);
    assert(motion.pulse(0) == 1800);
    assert(motion.pulse(1) == 1300);
    valid.axis[0] = {true, 1800, 1500, 1200};
    assert(!motion.configure(valid));
    assert(!motion.active());

    Receiver rx;
    const char* good = "{\"v\":1,\"epoch\":\"a\",\"seq\":1,\"state\":\"finished\",\"session\":\"s\",\"notify\":true}";
    assert(rx.accept(good, 0xFFFFFF00u));
    assert(!rx.cue()); // initial sync never chimes
    assert(rx.accept(good, 0xFFFFFF10u));
    assert(!rx.cue());
    assert(!rx.expired(0x00000010u));
    assert(rx.expired(0x00002000u));
    assert(rx.accept(good, 0x00002001u));
    assert(!rx.cue()); // reconnect cannot replay
    assert(!rx.accept("{\"v\":2}", 9000));
    assert(!rx.accept("{\"v\":1,\"epoch\":\"a\",\"seq\":0,\"state\":\"working\",\"session\":\"s\",\"notify\":false}", 9001));
    assert(rx.accept("{\"v\":1,\"epoch\":\"b\",\"seq\":0,\"state\":\"working\",\"session\":\"s\",\"notify\":false}", 9002));
    assert(rx.state() == State::Working);
    assert(!rx.accept("{\"v\":1,\"epoch\":\"a\",\"seq\":true,\"state\":\"working\",\"session\":\"s\",\"notify\":false}", 9003));
    return 0;
}
