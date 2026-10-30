# AtomS3R + Atomic Echo Base

The current hardware target is **AtomS3R C126 with Atomic Echo Base A149**, now called Atomic Voice Base in M5Stack's documentation. The base supplies the speaker and microphone. The AtomS3R display and pressable face stay in use. No motors are connected or driven.

## Arduino CLI setup

Windows installation:

```powershell
winget install --id ArduinoSA.CLI --exact --source winget
```

Open a new terminal if `arduino-cli` is not found on PATH after installation. On other systems, follow the [official Arduino CLI installation guide](https://arduino.github.io/arduino-cli/latest/installation/).

Install the official board package and libraries:

```sh
arduino-cli core update-index --additional-urls https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
arduino-cli core install m5stack:esp32@3.3.10 --additional-urls https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
arduino-cli lib install M5Unified@0.2.28 M5GFX@0.2.35 ArduinoJson@6.21.5
arduino-cli board list
arduino-cli board listall M5AtomS3R
```

The board identifier is `m5stack:esp32:m5stack_atoms3r`. Use a current M5Unified library with S3R support; the earlier project's 0.2.7 baseline is insufficient for this target. M5Unified owns the Echo Base codec, I2S pins, microphone and speaker configuration through `config.external_speaker.atomic_echo=true`.

## Compile, then explicitly upload

From the repository root, with Python and the host requirements installed:

```sh
python expressions/generate_device_audio.py
python checks/arduino_build.py
python checks/arduino_build.py --upload --port COM5
```

Replace COM5 with the actual device port; on macOS this is typically a `/dev/cu.*` path. `--cli` can supply the full executable path if needed. The helper copies canonical `firmware/src` and `firmware/include` files into an ignored temporary Arduino sketch, so no duplicate firmware source needs editing. It writes build outputs under `outputs/atoms3r-echo/`. Upload is never automatic without `--upload` and an explicit port.

If automatic reset cannot enter download mode, follow [M5Stack's S3R upload instructions](https://docs.m5stack.com/en/arduino/m5atoms3r/program): hold the reset button for about two seconds until the green LED lights, release, and use the port shown in download mode.

## Device behavior

- Working has continuously moving eyes and an activity trail.
- Needs you pulses; New message has a bouncing envelope.
- The original 66 BPM lo-fi working loop and fixed Hinata, Kakashi, Naruto and Killer Bee alert recordings are embedded in flash. Input/error calls repeat while active; message/completion repeat three times. No cloud speech service is used.
- Short press acknowledges the local alert. It never approves an operation in Codex.
- Long press toggles persisted mute.
- The microphone is not continuously recording. Speaker and microphone use the shared audio hardware at different times.
- Without companion heartbeats, the device shows Disconnected after five seconds. Start the companion on the actual port to keep it connected.

## Local hardware diagnostics

Close serial monitors and the companion before running:

```sh
python checks/device_check.py --port COM5 --output .runtime/arduino/device-check.json
```

The diagnostic first checks the expected firmware, audio driver and PSRAM. It requests a 100 ms microphone sample, computes signal levels on the device, discards the samples, and restores the speaker. It then sends real protocol state frames and reads the device's reported state. It does not save or transmit raw microphone audio.

Serial commands `MIC_TEST` and `STATUS`, each followed by a newline, are also available for local checks. Audible quality, actual display appearance and button feel require user confirmation; a successful software status report alone cannot prove those.

## Enclosure

`cad/stationary.py` now allows for the S3R + base stack. Manufacturer envelopes are 24 × 24 × 12.9 mm and 24 × 24 × 14.14 mm. The summed depth is conservative because actual connector overlap must be measured. The keeper leaves the centre of the speaker face open, with rear grille and side vents. Physical fit, acoustic alignment and snap force remain prototype checks before full printing.

Hardware sources: [AtomS3R](https://docs.m5stack.com/en/core/AtomS3R), [Atomic Voice/Echo Base](https://docs.m5stack.com/en/atom/Atomic_Voice_Base), [M5Stack Echo Base Arduino example](https://docs.m5stack.com/en/arduino/projects/atomic/atomic_echo_base). Audio licenses and source attribution: [CC0 voice credits](../preview/voices/CREDITS.md).
