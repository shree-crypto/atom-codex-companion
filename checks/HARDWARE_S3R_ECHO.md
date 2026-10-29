# AtomS3R + Echo Base hardware check — 2026-10-30

Arduino CLI 1.5.1 was installed on the laptop. The official M5Stack 3.3.10 board package was used with M5Unified 0.2.28, M5GFX 0.2.35 and ArduinoJson 6.21.5. Target: `m5stack:esp32:m5stack_atoms3r` with USB CDC enabled, 8 MB flash and octal PSRAM.

The canonical C++ sources were compiled successfully, then uploaded to the identified connected device on COM5. Esptool verified the written data hash and reset the device. Arduino reported 692,151 bytes of program storage (20%) and 30,080 bytes of global RAM (9%). The release application image includes its binary headers/padding; its exact size and SHA-256 are recorded in [hardware-s3r-echo.json](hardware-s3r-echo.json).

Live serial read-back confirmed:

- Firmware `2.0-s3r-echo` running, audio driver enabled and 8,388,608 bytes of PSRAM.
- A 100 ms microphone capture completed with a nonzero signal. The speaker was restored afterward. Raw microphone samples were discarded on the device.
- Idle, Working, Needs input, Message and Finished protocol states were accepted and reported correctly.
- Recorded WAV playback was active for Working, Needs input, Message and Finished, with mute off.

This verifies upload, running firmware, protocol handling, audio-driver playback and microphone capture. Actual display appearance, audible quality and physical button feel require user confirmation. It does not establish live automatic Codex hook coverage. Start the companion and configure trusted hooks using the setup guide. After five seconds without companion heartbeats, the device intentionally shows Disconnected.

The updated enclosure is a 48 × 42 × 44 mm prototype for the S3R + base stack, retaining the Classic orange/black design and three printed parts. All three face variants passed single-solid validity and nominal hardware/printed-part intersection checks. STEP round trips, STL watertight checks and 3MF archive checks passed. Real component fit, connector overlap, button travel, speaker/mic opening alignment and snap forces still need a physical print check.

The older `atom-v1-classic-firmware.bin` is retained as a legacy reference. Use the new `atom-s3r-echo-firmware.bin` and Arduino CLI source/upload instructions for this hardware.
