# Build your Atom companion — step by step

V1 is stationary: orange Classic bezel, black body, pressable colour face and sound. No motors are needed. One colour also works.

## 1. Pick the right download

- `atom-companion-source.zip`: editable firmware, laptop companion, hook example, expression preview, CAD source, tests and this guide.
- `classic-enclosure-models.zip`: body, Classic bezel, rear keeper and fit coupons in STL; main parts also in STEP and 3MF.
- `atom-v1-classic-firmware.bin`: previously compiled application image, provided for reference. It is not a complete flash bundle; use the source build/upload route below, which supplies the bootloader and partition images too.

The website has the latest animated faces and cute browser speech. The device firmware is an earlier baseline with simpler faces and tones. Browser speech is not embedded speech: the new voice and revised animations have not been ported to, flashed onto or tested on the Atom. The files are a prototype kit, with the exact device variant and physical print fit still to be confirmed.

## 2. Check the hardware

Use the label on the board to identify its exact model. The supplied development profile targets AtomS3 C123, using an ESP32-S3 profile with 8 MB flash. Confirm this before uploading; another Atom variant needs its matching profile. Have a USB data cable, the board and a laptop ready. The firmware uses M5Unified's display, button and speaker drivers; confirm audio on your actual board during testing.

## 3. Unzip and install Python tools

Extract the source ZIP and open a terminal inside its `robot-companion` folder. Install Python 3.13 if needed. Choose the commands for your laptop. Internet access is needed to install packages and download the ESP32 toolchain.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m companion.main --init-config
```

macOS Terminal:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
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

## 5. Build and upload firmware

Windows:

```powershell
.venv\Scripts\python.exe -m platformio run -d firmware -e atoms3 -j 2
.venv\Scripts\python.exe -m platformio run -d firmware -e atoms3 -t upload --upload-port COM5
```

macOS:

```sh
.venv/bin/python -m platformio run -d firmware -e atoms3 -j 2
.venv/bin/python -m platformio run -d firmware -e atoms3 -t upload --upload-port /dev/cu.YOUR_PORT
```

The first build downloads the pinned toolchain and libraries. If upload cannot connect, check the cable, selected port and board-specific download-mode instructions. This workspace has compiled the baseline firmware successfully; it has not physically flashed your device. Do not flash the standalone application BIN at a guessed address.

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

## 8. Connect Codex events

Open `hooks/config.example.json`. Replace `ABSOLUTE_PYTHON_PATH` with the full path to this virtual environment's Python and `ABSOLUTE_ROBOT_ROOT` with the extracted project folder. Keep both paths quoted. Merge its event entries into your existing `~/.codex/hooks.json`, or a trusted project's `.codex/hooks.json`. Preserve existing hooks and avoid installing the same entries twice.

Restart the Codex session, open `/hooks` in the CLI, review and trust the new command definitions. New or changed untrusted hooks are skipped. Official configuration and trust instructions: https://learn.chatgpt.com/docs/hooks . Desktop delivery depends on the installed Codex version; use the CLI to inspect hook configuration and confirm delivery before relying on it.

With the companion running, submit a prompt: the robot should show Working. A permission request should show Needs you; a completed turn should show Finished. Do not deliberately authorize a risky action just to test an alert. Incoming peer messages, general clarification questions, failure events and dismissed approvals do not yet have confirmed automatic coverage. See `checks/event-coverage.md`; New message can be previewed on the site or sent manually using the event kinds supported by the companion.

## 9. Print a fit coupon, then the enclosure

Unzip the model pack. Print `STL/fit_coupons.stl` first. Check the board and your printer's fit before committing to the full enclosure. Then print `STL/body.stl`, `STL/bezel.stl` and `STL/keeper.stl`. Start with a 0.4 mm nozzle and 0.2 mm layers; orient flat surfaces on the bed and inspect overhangs in your slicer. Use your printer/material profile for temperatures, cooling, supports and shrinkage.

PLA is suitable for an initial fit prototype; ABS needs its own fit/shrinkage check. Black body + keeper and orange bezel use two separately printed colours. Nominal assembled size is 48 × 38 × 44 mm. The snap fits, speaker grille, USB opening and keeper have not been physically validated on your exact board.

## 10. Assemble and verify

Dry-fit the unpowered board in the body, align the screen and USB opening, fit the rear keeper and gently engage the bezel snaps. Do not force a tight fit. Confirm that the pressable screen moves freely without preload and the USB cable seats fully. Connect USB and retest display, press, mute and speaker before treating assembly as complete.

## Troubleshooting

- No port: try a known USB data cable and another USB port; check the board's USB/download mode.
- Port busy: close serial monitors or stop another companion instance.
- Configuration exists: remove `--init-config` and reuse your existing token file.
- Manual states work but Codex does not: verify absolute hook paths, `/hooks` trust, the running companion and event coverage.
- Silent device: check long-press mute and the actual board's speaker capability/driver. Site speech does not stream to the Atom.
- Silent website: click Sound on, raise the volume, and check browser/OS speech availability. Browser voice quality varies by device.
- Tight print: stop assembly and adjust the fit coupon/clearance for your material before reprinting.

## Edit and verify

Edit `expressions/definitions.json`, then run `python expressions/generate.py` to update the browser table. Firmware presentation remains separately implemented in `firmware/src/presentation.cpp`; generation alone does not port browser speech or animation. Preview the static files with `python -m http.server 8000 --directory preview` and open http://localhost:8000 .

Python checks: `python -m unittest discover -s tests -v`. Browser logic checks require Node: `node --test tests/face.test.mjs tests/audio.test.mjs`. CAD uses Text-to-CAD/Cadgen 0.8.1 and `cad/stationary.py`; see README for regeneration. Earlier motor headers and tests are retained source studies only; V1 has no motor control.
