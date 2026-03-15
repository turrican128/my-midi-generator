# CLAUDE.md

## Project Overview

**SynthwaveMidiGenerator** — A Python project that generates synthwave-style MIDI files from text-based note input. It parses note names (e.g. `C4`, `D#5`, `Bb3`), applies customizable rhythm patterns, detects scales/vibes, and outputs `.mid` files with accompanying `.log` analysis files.

## Repository Structure

```
my-midi-generator/
├── src/
│   ├── __init__.py                    # Package init
│   ├── multi_track_midi_generator.py  # Multi-track generator ← active development
│   ├── generate_harmony.py            # Harmony generator (diatonic 3rd above)
│   └── scale_converter.py            # Snap MIDI notes to a target scale
├── output/                            # Generated .mid and .log files go here
├── main.py                            # PyCharm placeholder (not used for MIDI generation)
├── example_input.txt                  # Sample input: 8-bar D major melody
├── example_lead.txt                   # Multi-track example: lead synth (C minor)
├── example_bass.txt                   # Multi-track example: synth bass (C minor)
├── example_pad.txt                    # Multi-track example: ambient pad (C minor)
├── requirements.txt                   # Dependencies
└── CLAUDE.md
```

### Key file: `src/multi_track_midi_generator.py`

The main generator. Reads notes from text files and outputs `.mid` + `.log` files:
- Multiple tracks in a single MIDI file (lead, bass, pad, etc.)
- Per-track settings: name, program (instrument), channel, velocity
- Configurable tempo via `--tempo` flag
- Auto-assigns MIDI channels to avoid conflicts (skips channel 9/drums)
- Backward compatible — works with single input files too
- Detects scale (major, minor, dorian, etc.) and mood/vibe per track

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Multi-track generator (active development)
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt example_pad.txt -o my_song.mid
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt --tempo 120
python src/multi_track_midi_generator.py example_input.txt                # single-track mode

```

## Dependencies

- **mido** (`>=1.2.10`) — used by all generators and tools

## Input File Format

Text files with one bar per line, 4 notes per bar (space or comma separated). Optional header lines for track settings:

```
name: Lead Synth
program: 81
channel: 0
velocity: 100
rhythm: 1.5, 0.5, 0.5, 1.5
C4 E4 G4 B4
D4 F#4 A4 C5
E4 G#4 B4 D5
F4 A4 C5 E5
```

All header lines are optional. Defaults: name from filename, program 80, auto channel, velocity 95, rhythm `1.5, 0.5, 0.5, 1.5`. Tempo default is 110 BPM (configurable via `--tempo`).

## Conventions

- Python 3, no type hints used in existing code.
- Keep code simple and avoid over-engineering.
- Prefer editing existing files over creating new ones.
- Do not add unnecessary comments, docstrings, or type annotations to unchanged code.
- Output files go to `output/` directory.
- Note format: standard notation with octave number (e.g. `C4`, `D#5`, `Bb3`). Octave range 0-9.
- Chord format: wrap multiple notes in square brackets to play simultaneously (e.g. `[C4 E4 G4]`). Mix freely with single notes — each bar still needs 4 beats.

## Development Workflow

- **Branch strategy**: Feature branches prefixed with `claude/` for AI-assisted development.
- **Commits**: Use clear, descriptive commit messages summarizing the "why" not just the "what".
- **IDE**: Originally developed in PyCharm (JetBrains).
- **No tests or linting configured yet.**
