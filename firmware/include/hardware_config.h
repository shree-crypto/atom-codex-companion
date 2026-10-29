#pragma once
#include "motion.h"

// Development target: AtomS3 C123 only. Verify the actual label before upload.
// No hardware output until BOTH pins and measured travel are explicitly configured.
constexpr int PAN_PIN = -1;
constexpr int TILT_PIN = -1;
constexpr int PIEZO_PIN = -1;
constexpr bool ENABLE_HARDWARE_OUTPUTS = false;

inline Calibration hardwareCalibration() {
    Calibration c{};
    c.confirmed=false;
    // After physical calibration, enter the measured safe pulse limits here.
    // c.axis[0] = {true, measured_low, measured_neutral, measured_high};
    // c.axis[1] = {true, measured_low, measured_neutral, measured_high};
    return c;
}
