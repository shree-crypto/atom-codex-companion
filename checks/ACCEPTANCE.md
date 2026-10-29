# V1 acceptance record — 2026-10-29

Selected: **A Classic, orange bezel + black body**. V1 stationary, no motors. Device-speaker cues use M5Unified's M5.Speaker as requested.

## Completed software proof

- Host Python suite: **30/30 passed**, including real authenticated loopback HTTP, malformed input, duplicate delivery, reversed delivery, same-turn Stop continuation, simultaneous sessions and stale button acknowledgement.
- Native C++ parser assertions: passed using Zig. Historical V2 motion assertions also pass; this is not a hardware motion claim and that driver is not linked into V1.
- ESP32-S3 firmware: **build succeeded**, 480,609 bytes flash (14.4%), 22,468 bytes RAM (6.9%). Target is the labelled AtomS3 C123 development profile.
- GCC 8.4 failed to start on this Windows host with illegal system DLL relocation. The profile pins official Espressif GCC 12.2.0+20230208 instead. Build emits upstream FreeRTOS section-attribute and linker RWX-segment warnings. No OS security settings were changed.
- Firmware source uses nonblocking M5.Speaker tones, persisted mute and local alert acknowledgement; no motors or GPIO servo drivers are active in V1.

## Completed CAD proof

- Three V1 printed parts, each a valid single solid.
- All three face variants checked: no print-part intersections above 0.05 mm³ and no intersections with the nominal board envelope above that tolerance.
- Nominal assembled size: 48 × 38 × 44 mm.
- Actual CAD geometry images produced for green, orange, single-colour and three bezel variants. Native OCCT image readback failed; fallback images use actual tessellated geometry with a CPU depth buffer.
- STEP, STL and 3MF exports written for the main parts and alternative bezels; board-fit coupons exported as STL. Round-trip/export validation is recorded separately in cad/review/exports.json when that check completes.

## Still requires the actual device / print

- Exact board variant and actual serial port confirmation before upload.
- Flashing, visible expression playback, button travel, audible speaker playback and volume.
- Live Codex hook delivery on the user's exact desktop/CLI version. Global hooks are not overwritten; merge example is supplied.
- Actual Atom enclosure fit, USB cable/connector access, speaker grille alignment, snap insertion force, keeper retention and repeated opening/closing in PLA or ABS.
- No physical assembly or print has been performed; exports are prototypes, not a claim of production-ready fit.

Automatic clarification-question, peer-message and approval-dismissal coverage remains unverified; see event-coverage.md. No hidden-state inference or transcript scraping is used.
