# YouTube News Video

A Claude skill that produces a complete **YouTube news episode** in two phases: it researches the day's stories and writes the scripts, then turns your recorded audio into a cinematic, physically lit animated video, plus 2 Shorts and a thumbnail.

## What it does

**Phase 1: research and writing (then it stops and waits for your audio)**
- Researches the latest stories and checks them against sources.
- Writes ElevenLabs voice scripts with set clip names, so the audio drops straight into Phase 2.
- Writes the YouTube title, description, chapters and tags.

**Phase 2: build (when you upload your audio clips)**
- **"Cinematic Desk" look:** each story is a printed news brief lying on a dark desk, under a warm window light whose blind shadows drift slowly across the scene.
- **Type and motion:** kinetic serif headlines with motion trails, keyword checklists that tick on the beat, a slow camera dolly and paper-plane transitions between stories.
- **Category colours:** World, Tech, Business, Sports and Breaking, with a consistent brand (intro sting, outro, sign-on and sign-off lines).
- **Sound and checks:** a sound-design pass, a −14 LUFS mix, and quality checks before delivery.
- **Delivery:** the long-form video, 2 vertical Shorts and a thumbnail.

## What you can build with it

- **Daily or weekly news briefings:** "Today's Briefing", 3-5 stories, 2-5 minutes.
- **Topic roundups:** tech news of the week, sports weekend recap, business headlines.
- **Breaking-news Shorts:** one story, vertical, under 60 s.
- **A regional channel:** stories picked for a specific country or audience, in its own brand colours.

## Installing

This skill relies on **documentary-animation** for its build pipeline (Remotion, Three.js, sound and quality checks), so install that too.

**Claude apps:** zip `skills/youtube-news-video` and upload it under *Customize → Skills* (or add this folder as a plugin).

**Claude Code:**

```bash
cp -R skills/youtube-news-video ~/.claude/skills/
```

## Requirements

- Everything documentary-animation needs: Node.js, Remotion, Three.js, FFmpeg and Python audio tools.
- An ElevenLabs account to record the narration from the scripts.
- Web search, for the research phase.

## How to use it

```text
Make today's news episode: 4 world and tech stories, about 3 minutes.
```

Phase 1 ends with the scripts and metadata. Generate the clips in ElevenLabs with the given names, then:

```text
Here are the audio clips for today's episode. Build the video and the 2 Shorts.
```

## Brand

The brand section in `SKILL.md` has placeholders: the channel name, palette, category accents, fonts, intro/outro, sign-on and sign-off. Fill them in once, and every episode stays consistent.

## Repository layout

```
skills/youtube-news-video/
  SKILL.md    phases, brand, Cinematic Desk motion style, sound design, build and final checks
```
