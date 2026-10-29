# Build your Atom companion — step by step

V1 is stationary: orange Classic bezel, black body, pressable colour face and sound. No motors are needed. One colour also works.

## 1. Pick the right download

- `atom-companion-source.zip`: editable firmware, laptop companion, hook example, expression preview, CAD source, tests and this guide.
- `classic-enclosure-models.zip`: body, Classic bezel, rear keeper and fit coupons in STL; main parts also in STEP and 3MF.
- `atom-s3r-echo-firmware.bin`: AtomS3R + Echo Base application image, provided for reference. It is not a complete flash bundle; use the source build/upload route below, which supplies the bootloader and partition images too.

The website offers five recorded voice styles. The S3R + Echo Base firmware embeds the default Cute recordings and updated Working, Needs you and New message visuals. Hardware build/flash results are recorded separately; physical print fit and subjective sound/display quality require confirmation. Browser voice selection does not remotely configure the device.

## 2. Check the hardware

The current target is **AtomS3R C126 + Atomic Echo Base A149** (called Atomic Voice Base in current M5Stack documentation). Attach the base underneath the S3R. It supplies the speaker and microphone. The S3R itself has a 128 x 128 colour screen, pressable face, 8 MB flash and 8 MB PSRAM. Use a USB data cable from the S3R to the laptop.

The old AtomS3 C123 profile and old compiled application image are legacy artifacts. Use the S3R Arduino CLI route below for this hardware. Do not flash an older board-specific application BIN at a guessed address.

## 3. Unzip and install Python tools

Extract the source ZIP and open a terminal inside its `robot-companion` folder. Install Python 3.13 if needed. Choose the commands for your laptop. Internet access is needed to install packages and download the ESP32 toolchain.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m companion.main --init-config
```

macOS Terminal:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m companion.main --init-config
```

Run `--init-config` once. If the configuration already exists, reuse it. It contains a private local token at `~/.atom-companion/config.json`; keep it on your laptop, out of uploads and shared ZIPs.

## 4. Find the USB port

Connect the Atom with a data cable. List ports:

Windows:

```powershell
.venv\Scripts\python.exe -m serial.tools.list_ports
```

macOS:

```sh
.venv/bin/python -m serial.tools.list_ports
```

Use the actual port shown, such as `COM5` or `/dev/cu.usbmodem…`. The examples below use placeholders; substitute your port. Close serial monitors before uploading or running the companion.

## 5. Build and upload firmware with Arduino CLI

Install Arduino CLI. On Windows: `winget install --id ArduinoSA.CLI --exact --source winget`. Open a new terminal after installation if the command is not on PATH. For macOS, follow the official Arduino CLI installation guide linked in `firmware/ARDUINO.md`.

Install the official M5Stack board package and libraries:

```sh
arduino-cli core update-index --additional-urls https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
arduino-cli core install m5stack:esp32@3.3.10 --additional-urls https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
arduino-cli lib install M5Unified@0.2.28 M5GFX@0.2.35 ArduinoJson@6.21.5
```

From the project root, build first, then upload to the actual port:

```sh
python checks/arduino_build.py
python checks/arduino_build.py --upload --port COM5
```

Use the virtual environment Python from step 3 if `python` resolves to another interpreter. On macOS replace COM5 with the actual `/dev/cu.*` port. The helper uses `m5stack:esp32:m5stack_atoms3r` and stages the canonical firmware source into an ignored Arduino sketch. Pass `--cli PATH` if the CLI is not on PATH.

If automatic reset fails, hold the S3R reset button for about two seconds until its green LED lights, release, and retry using the listed download-mode port. Do not erase the entire flash or upload a standalone application BIN at a guessed address.

Before starting the companion, use the virtual environment Python from step 3 to run `checks/device_check.py --port COM5` (substitute your actual port). This briefly cycles the faces and voice clips, checks PSRAM and the speaker driver, and takes a 100 ms local microphone sample. It reports levels and discards the raw audio. Close serial monitors first. This is a manual hardware check; automatic Codex events are configured in step 8.

Detailed device behavior and microphone diagnostics: `firmware/ARDUINO.md`. The selected Cute character recordings are embedded in the new S3R firmware; browser style selection does not remotely change the device voice. Microphone use is an explicit local diagnostic, not an always-on cloud assistant.

## 6. Start the laptop companion

Keep this terminal running while you use Codex.

Windows:

```powershell
.venv\Scripts\python.exe -m companion.main --port COM5
```

macOS:

```sh
.venv/bin/python -m companion.main --port /dev/cu.YOUR_PORT
```

Use `--dry-run` instead of `--port …` to inspect events without a device. Stop with Ctrl+C. Only one application can own the serial port.

## 7. Test states before connecting Codex

In a second terminal, in the same folder, run these one at a time. On macOS replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

```powershell
.venv\Scripts\python.exe -m companion.main --emit start
.venv\Scripts\python.exe -m companion.main --emit needs_input
.venv\Scripts\python.exe -m companion.main --emit finished
```

Check the display and speaker. Short press acknowledges the local alert; long press toggles persisted mute. Acknowledging the robot never approves a Codex operation. These manual events verify the connection, not automatic Codex integration.

## 8. Connect Codex automatically

On Windows, use the included installer after Codex CLI and Python dependencies are installed. Close any manual serial monitor or foreground companion first. From the source folder:

```powershell
$codexExe = (Get-ChildItem "$env:APPDATA\npm\node_modules\@openai\codex" -Recurse -Filter codex.exe | Select-Object -First 1).FullName
.venv\Scripts\python.exe checks/install_windows.py --port COM5 --codex-exe "$codexExe"
```

Substitute your device's actual port and installed native Codex executable. The installer starts a hidden background companion, adds the current user's Windows sign-in startup entry, preserves existing hooks, and registers five silent native hooks through Codex's own configuration API. The generated token stays in a restricted local file. Re-running setup preserves its token and avoids duplicate hooks or background instances.

The companion follows new structured lifecycle records in this user's local `~/.codex/sessions` directory: turn starts/tools show Working, assistant progress messages show New message briefly, structured user-input tools show Needs you, answers clear their matching request, and completed turns show Finished when no higher-priority work or input remains. It observes all local chats by default. Historical alerts are not replayed on startup. Remote/cloud-only chats or another CODEX_HOME are not included automatically.

Native UserPromptSubmit, PreToolUse, Stop, PermissionRequest and PostToolUse hooks cover starts, activity, completion and permission waiting/resolution. The structured record observer fills in new messages and explicit question/answer events and provides immediate compatibility for already-running chats. Their exact observer definitions are reviewed and trusted through the installed Codex API; unrelated hooks are preserved. If your Codex installation lacks that API, use `/hooks` to review only the observer commands. Already-running Codex sessions may need a new session before newly added native hooks load; the local lifecycle observer works immediately. Dismissed approval dialogs without a matching tool-resolution event remain an unverified edge case.

To run in the foreground instead, on Windows or macOS:

```text
python -m companion.main --port YOUR_PORT --codex-events
```

Install the `requirements.txt` dependencies into that Python environment first. A private configuration must exist (`python -m companion.main --init-config`). The background installer creates it automatically. Add `--thread THREAD_UUID` to observe only one chat.

The observer reads records locally and forwards only state identifiers and hashed IDs to the M5. It never forwards prompts, answers, source code or reasoning content. The authenticated status endpoint is local to 127.0.0.1. Pressing the M5 face only silences notifications; it never approves a tool action.

Windows startup can be disabled by removing only `AtomCodexCompanion` from `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. Its installation receipt and state-only log are in `%LOCALAPPDATA%\AtomCodexCompanion`. Hook backups are stored there too. Stop the exact companion process before flashing or opening a serial monitor.

## 9. Print a fit coupon, then the enclosure

Unzip the model pack. Print `STL/fit_coupons.stl` first. Check the board and your printer's fit before committing to the full enclosure. Then print `STL/body.stl`, `STL/bezel.stl` and `STL/keeper.stl`. Start with a 0.4 mm nozzle and 0.2 mm layers; orient flat surfaces on the bed and inspect overhangs in your slicer. Use your printer/material profile for temperatures, cooling, supports and shrinkage.

PLA is suitable for an initial fit prototype; ABS needs its own fit/shrinkage check. Black body + keeper and orange bezel use two separately printed colours. Nominal assembled size is 48 × 42 × 44 mm. The snap fits, speaker grille, USB opening and keeper have not been physically validated on your exact board.

## 10. Assemble and verify

Dry-fit the unpowered board in the body, align the screen and USB opening, fit the rear keeper and gently engage the bezel snaps. Do not force a tight fit. Confirm that the pressable screen moves freely without preload and the USB cable seats fully. Connect USB and retest display, press, mute and speaker before treating assembly as complete.

## Troubleshooting

- No port: try a known USB data cable and another USB port; check the board's USB/download mode.
- Port busy: close serial monitors or stop another companion instance.
- Configuration exists: remove `--init-config` and reuse your existing token file.
- Manual states work but Codex does not: verify absolute hook paths, `/hooks` trust, the running companion and event coverage.
- Silent device: check long-press mute and the actual board's speaker capability/driver. Site recordings do not stream to the Atom.
- Silent website: click Sound on, raise the volume, and check browser audio settings. Use the Voice style selector and Hear attention sample to compare the five recorded options.
- Tight print: stop assembly and adjust the fit coupon/clearance for your material before reprinting.

## Edit and verify

Edit `expressions/definitions.json`, then run `python expressions/generate.py` to update the browser table. Firmware presentation remains separately implemented in `firmware/src/presentation.cpp`; generation alone does not port browser recordings or animation. Preview the static files with `python -m http.server 8000 --directory preview` and open http://localhost:8000 .

Python checks: `python -m unittest discover -s tests -v`. Browser logic checks require Node: `node --test tests/face.test.mjs tests/audio.test.mjs`. CAD uses Text-to-CAD/Cadgen 0.8.1 and `cad/stationary.py`; see README for regeneration. Earlier motor headers and tests are retained source studies only; V1 has no motor control.

Recorded voice assets are bundled under `preview/voices/` and in the source download. Choose Cute, Bright/anime-like, Warm, Mature or Spoken announcer. Character styles are short vocal reactions rather than full notification sentences. Credits and CC0 source links are in `preview/voices/CREDITS.md`. The voice ZIP on the site includes the selected recordings and credit files.

## Eye colours and smooth animation

Firmware 2.1 draws into a 128 × 128 offscreen buffer and transfers each complete frame at a target of 60 fps. If buffer allocation fails, it falls back to direct drawing at 20 fps; `STATUS` reports `buffered`, cumulative `frames`, and `max_frame_us` for diagnosis.

The browser preview follows your display refresh rate. Its Eye colour selector compares Deep blue (#397dcc), Forest green (#2eab79), and Orange (#ed8b35), with the existing voice controls.

On the device, send one newline-terminated command over the same USB serial connection:

```text
COLOR blue
COLOR green
COLOR orange
STATUS
```

Send only the desired COLOR line. The selected colour persists across restart. Invalid names are rejected without changing the colour. Close the laptop companion before using a serial terminal, and close the terminal before restarting the companion. Colour changes do not acknowledge or approve a Codex request.

## Audition anime character lines

The browser preview also has Naruto (9 clips), Jujutsu Kaisen (10 clips), and My Hero Academia (5 clips) packs. Select a pack, choose an expression, and enable sound. The Phrase selector lets you audition any line in that pack. Rotate through phrases changes the line each time, including repeated alerts; Try another phrase plays one sample. Sound off cancels playback and pending repeats.

Anime samples stream from their original community soundboard host and need an internet connection. Open original soundboard clip shows the source of the current recording. These references are for auditioning; the flashed firmware now uses the fixed Naruto crew set described below.

## Fixed Naruto crew on the M5

Firmware 2.4 uses continuous quiet slow lo-fi music while working and a fixed dialogue clip for each alert state:

- Working: quiet slow lo-fi music, looped locally until the state changes or you mute it.
- Needs input: Hinata — “Naruto-kun!”
- New message: Kakashi — “Nani?!”
- Finished: Naruto — “Believe it!”
- Error/blocked: Killer Bee — “Bakayaro, konoyaro!”

Idle, paused and disconnected retain their quiet faces. Working ambience loops continuously; message and completion repeat three times. Input/error cues repeat after the recording finishes and a three-second gap until acknowledged or the state changes. Short-press the display to silence a cue; long-press to mute persistently. A press never approves a Codex action.

Select **Naruto crew · M5 fixed set** in the browser to audition the same files. The four voice cues and generated music WAV are bundled in `preview/voices/naruto-device/`: 16 kHz, mono, 16-bit PCM. They play without Wi-Fi or an online speech service on the M5. Original community soundboard links and processed-file SHA-256 hashes are in `expressions/device_voice_pack.json`; anime dialogue is third-party material, separate from the CC0 packs.

To regenerate the firmware audio header and matching browser metadata after editing those WAVs and their manifest:

```text
python expressions/generate_device_audio.py
```

Then follow the Arduino build/upload instructions above. The generator checks each file's hash and WAV format before embedding it.

To regenerate the original lo-fi working loop before rebuilding its embedded header, install the optional generation dependencies (`python -m pip install -r requirements-render.txt`):

```text
python expressions/generate_working_lofi.py
python expressions/generate_device_audio.py
```
