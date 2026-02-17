# CLAUDE.md

## Project Overview

**SynthwaveMidiGenerator** — A Python project that generates synthwave-style MIDI files from text-based note input. It parses note names (e.g. `C4`, `D#5`, `Bb3`), applies customizable rhythm patterns, detects scales/vibes, and outputs `.mid` files with accompanying `.log` analysis files.

## Repository Structure

```
my-midi-generator/
├── src/
│   ├── __init__.py                    # Package init
│   ├── multi_track_midi_generator.py  # Multi-track generator ← active development
│   ├── midi_generator.py              # Original single-track generator
│   ├── midi gen 2.py                  # Standalone bass line generator (uses midiutil)
│   └── midi gen grok.py              # Standalone melodic lead generator (uses midiutil)
├── backup/
│   └── note01.py                      # Earlier standalone nightrun melody generator (uses mido)
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

The multi-track generator. Builds on all features of `midi_generator.py` and adds:
- Multiple tracks in a single MIDI file (lead, bass, pad, etc.)
- Per-track settings: name, program (instrument), channel, velocity
- Configurable tempo via `--tempo` flag
- Auto-assigns MIDI channels to avoid conflicts (skips channel 9/drums)
- Backward compatible — works with single input files too

### Original: `src/midi_generator.py`

The original single-track generator. It:
- Reads notes from a text file (4 notes per bar, minimum 4 bars)
- Supports an optional `rhythm:` line for custom rhythm patterns
- Converts note names to MIDI numbers
- Detects scale (major, minor, dorian, etc.) and mood/vibe
- Outputs a `.mid` file and a `.log` file to `output/`

### Standalone scripts (`src/midi gen 2.py`, `src/midi gen grok.py`, `backup/note01.py`)

Earlier experiments with hardcoded note sequences. They use either `mido` or `midiutil` directly and don't read from text files.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Multi-track generator (active development)
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt example_pad.txt -o my_song.mid
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt --tempo 120
python src/multi_track_midi_generator.py example_input.txt                # single-track mode

# Original single-track generator
python src/midi_generator.py
python src/midi_generator.py path/to/input.txt
python src/midi_generator.py path/to/input.txt my_song.mid
```

## Dependencies

- **mido** (`>=1.2.10`) — used by `src/midi_generator.py` and `backup/note01.py`
- **midiutil** — used by the standalone scripts in `src/midi gen 2.py` and `src/midi gen grok.py` (not in requirements.txt)

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

## Development Workflow

- **Branch strategy**: Feature branches prefixed with `claude/` for AI-assisted development.
- **Commits**: Use clear, descriptive commit messages summarizing the "why" not just the "what".
- **IDE**: Originally developed in PyCharm (JetBrains).
- **No tests or linting configured yet.**
