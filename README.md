# SynthwaveMidiGenerator

A Python tool for generating synthwave-style MIDI files from text-based note input. Write your melodies in plain text, and get `.mid` files ready to load in any DAW.

## Features

- Multi-track MIDI output (lead, bass, pad, etc.) in a single file
- Auto-detects scale and mood/vibe per track
- Chord support — wrap notes in `[]` to play simultaneously
- Configurable tempo, instrument (GM program), velocity, and rhythm patterns
- Harmony generator: adds diatonic 3rds above a melody
- Scale converter: snaps notes to a target scale

## Requirements

- Python 3
- [mido](https://mido.readthedocs.io/) (`pip install mido`)

```bash
pip install -r requirements.txt
```

## Usage

### Multi-track (recommended)

```bash
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt example_pad.txt -o my_song.mid
python src/multi_track_midi_generator.py example_lead.txt example_bass.txt --tempo 120
```

### Single-track

```bash
python src/multi_track_midi_generator.py example_input.txt
```

Output `.mid` and `.log` files are written to the `output/` directory.

## Input File Format

One bar per line, 4 beats per bar (space or comma separated). Optional header lines control per-track settings.

```
name: Lead Synth
program: 81
channel: 0
velocity: 100
rhythm: 1.5, 0.5, 0.5, 1.5
C4 E4 G4 B4
D4 F#4 A4 C5
[C4 E4 G4] B4 D5 F5
```

| Header    | Default              | Description                          |
|-----------|----------------------|--------------------------------------|
| `name`    | filename             | Track name                           |
| `program` | 80                   | GM instrument number (0–127)         |
| `channel` | auto-assigned        | MIDI channel (skips 9/drums)         |
| `velocity`| 95                   | Note velocity (0–127)                |
| `rhythm`  | `1.5, 0.5, 0.5, 1.5` | Beat durations in quarter notes      |

**Note format:** standard notation with octave — `C4`, `D#5`, `Bb3` (octave range 0–9)
**Chord format:** wrap simultaneous notes in square brackets — `[C4 E4 G4]`

**Tempo** default is 110 BPM, override with `--tempo`:

```bash
python src/multi_track_midi_generator.py example_lead.txt --tempo 95
```

## Other Tools

### Harmony generator

Adds a diatonic 3rd above each note in a melody. Scale auto-detected from input.

```bash
python src/generate_harmony.py example_input.txt -o harmony.mid
python src/generate_harmony.py example_input.txt --scale D major
```

### Scale converter

Snaps all notes in a MIDI file to the nearest note in a target scale.

```bash
python src/scale_converter.py input.mid --scale C minor -o output.mid
```

## Project Structure

```
my-midi-generator/
├── src/
│   ├── multi_track_midi_generator.py  # Main generator
│   ├── generate_harmony.py            # Harmony generator
│   └── scale_converter.py             # Scale snapper
├── output/                            # Generated files
├── example_input.txt                  # Single-track example (D major)
├── example_lead.txt                   # Multi-track lead (C minor)
├── example_bass.txt                   # Multi-track bass (C minor)
├── example_pad.txt                    # Multi-track pad (C minor)
└── requirements.txt
```
