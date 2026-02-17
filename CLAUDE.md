# CLAUDE.md

## Project Overview

**SynthwaveMidiGenerator** — A Python project that generates synthwave-style MIDI files from text-based note input. It parses note names (e.g. `C4`, `D#5`, `Bb3`), applies customizable rhythm patterns, detects scales/vibes, and outputs `.mid` files with accompanying `.log` analysis files.

## Repository Structure

```
my-midi-generator/
├── src/
│   ├── __init__.py              # Package init
│   ├── midi_generator.py        # Main generator (text file → MIDI) ← primary source file
│   ├── midi gen 2.py            # Standalone bass line generator (uses midiutil)
│   └── midi gen grok.py         # Standalone melodic lead generator (uses midiutil)
├── backup/
│   └── note01.py                # Earlier standalone nightrun melody generator (uses mido)
├── output/                      # Generated .mid and .log files go here
├── main.py                      # PyCharm placeholder (not used for MIDI generation)
├── example_input.txt            # Sample input: 8-bar D major melody
├── requirements.txt             # Dependencies
└── CLAUDE.md
```

### Key file: `src/midi_generator.py`

This is the main and most developed script. It:
- Reads notes from a text file (4 notes per bar, minimum 4 bars)
- Supports an optional `rhythm:` line for custom rhythm patterns
- Converts note names to MIDI numbers
- Detects scale (major, minor, dorian, etc.) and mood/vibe
- Outputs a `.mid` file and a `.log` file to `output/`

### Standalone scripts (`src/midi gen 2.py`, `src/midi gen grok.py`, `backup/note01.py`)

These are earlier experiments with hardcoded note sequences. They use either `mido` or `midiutil` directly and don't read from text files.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main generator (uses example_input.txt by default)
python src/midi_generator.py

# Run with a specific input file
python src/midi_generator.py path/to/input.txt

# Run with a specific input and output filename
python src/midi_generator.py path/to/input.txt my_song.mid
```

## Dependencies

- **mido** (`>=1.2.10`) — used by `src/midi_generator.py` and `backup/note01.py`
- **midiutil** — used by the standalone scripts in `src/midi gen 2.py` and `src/midi gen grok.py` (not in requirements.txt)

## Input File Format

Text files with one bar per line, 4 notes per bar (space or comma separated). Optional first line for rhythm:

```
rhythm: 1, 1, 1, 1
C4 E4 G4 B4
D4 F#4 A4 C5
E4 G#4 B4 D5
F4 A4 C5 E5
```

Default rhythm if omitted: `1.5, 0.5, 0.5, 1.5` (syncopated pattern). Tempo is hardcoded at 110 BPM.

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
