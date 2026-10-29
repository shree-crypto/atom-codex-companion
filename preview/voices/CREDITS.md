# Fixed Naruto crew device pack

The user-selected device pack in `naruto-device/` contains four short dialogue samples and original generated working music, converted to 16 kHz mono PCM and balanced to -19 LUFS with a -3 dB true-peak target. They are third-party anime dialogue, **not CC0**. Community upload labels identify the characters; original source links, file hashes and durations are recorded in `expressions/device_voice_pack.json` and the generated `preview/device-voices.mjs`.

- Working — original 66 BPM lo-fi instrumental; generator: `expressions/generate_working_lofi.py`; quiet keys, bass and brushed drums, four-bar loop.
- Needs input — Hinata: https://myinstantplay.com/sound/hinata-naruto-kun
- New message — Kakashi: https://www.myinstants.com/en/instant/kakashi-nani/
- Finished — Naruto: https://myinstantplay.com/sound/narutou002dbelieve-it
- Error — Killer Bee: https://www.myinstants.com/en/instant/bakayaro-konoyaro-killerb-91562/

The firmware embeds the four dialogue clips and generated music locally. Existing broader anime audition packs remain online references.

# Online anime samples

The Naruto, Jujutsu Kaisen and My Hero Academia preview packs use 24 community soundboard references listed in `preview/anime.mjs`. Each entry links to its original page at https://myinstantplay.com/. Playback streams from that host. Anime recordings are not included in this repository, source ZIP, CC0 voice ZIP, and are not covered by the CC0 licenses below. Character labels come from community uploads; recordings can contain edits or background audio. The source link beside the playing phrase opens its original page.

# Recorded voice credits

All bundled recordings are free CC0 assets, downloaded on 2026-10-29. They are stored with the preview; playback does not contact an external audio host or speech service.

## Character recordings

Creator: **cicifyre / Cici Fyre**. Pack: [Female RPG Voice Starter Pack](https://opengameart.org/content/female-rpg-voice-starter-pack). Creator: https://cicifyre.itch.io/ . License: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

The source includes cutesy, medium and mature/tomboyish performances. Cute uses Type 1, Warm uses Type 2, Mature uses Type 3. Bright/anime-like uses the Cute recordings at 1.18× speed with pitch preservation disabled. It is a style variation, not a recording from an anime or an imitation of a named character.

These are short nonverbal character reactions. They do not speak the former custom notification sentences. Original files used: jump1, jump2, jump3, healed1 and damaged1. Changes: trim silence, convert to mono 22.05 kHz 16-bit PCM WAV, normalize peak to 0.8, fade clip edges; combine jump2 and jump1 with a 0.2-second gap for the attention call. Exact source mappings and durations are in manifest.json. Original creator readme: character-pack-readme.txt.

## Spoken announcer

Creator: **Kenney**. Pack: [Voiceover Pack](https://opengameart.org/content/voiceover-pack-40-lines), also at https://kenney.nl/assets/voiceover-pack . License: CC0 1.0; original license is bundled as kenney-license.txt.

Original female voice recordings: go.ogg, ready.ogg, mission_completed.ogg and war_hold.ogg. Stored without audio modification under state-based filenames. Both attention and message use Ready?; this pack has no custom New message line. It is a game announcer option rather than a custom assistant voice.

Credit is appreciated by both creators; CC0 does not require attribution. Their CC0 terms apply to these recordings independently of the project's code, for which no reuse license has been selected.

Rebuild the prepared files with checks/prepare_voice_assets.py --archives PATH after downloading RPG Voice Starter Pack.zip as rpg.zip and Voiceover Pack.zip as kenney-oga.zip into that folder. The conversion script requires NumPy. Keep the raw archives out of Git; the selected, prepared clips are included.
