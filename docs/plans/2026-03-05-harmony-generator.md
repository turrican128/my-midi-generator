# Harmony Generator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `src/harmony_generator.py` — reads a MIDI file, generates a diatonic 3rd-above harmony track, and writes it as a new MIDI file.

**Architecture:** New standalone script. Reads note events from an input MIDI using mido, maps each pitch to its scale degree using a `--scale` parameter, shifts up 2 diatonic degrees, and writes a new MIDI with the same timing but harmonized pitches. Notes outside the scale are snapped to the nearest scale note before harmonizing.

**Tech Stack:** Python 3, mido

---

### Task 1: Build scale utilities

**Files:**
- Create: `src/harmony_generator.py`

**Step 1: Create the file with scale lookup tables and two helper functions**

```python
"""
Harmony Generator - Synthwave MIDI Generator

Reads a MIDI file and generates a diatonic 3rd-above harmony track.

Usage:
    py src/harmony_generator.py input.mid --scale A minor
    py src/harmony_generator.py input.mid --scale C major -o harmony.mid

Output:
    output/<input_name>_harmony.mid
"""

import os
import sys
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

NOTE_NAME_TO_PC = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11,
}

SCALE_INTERVALS = {
    'major':          [0, 2, 4, 5, 7, 9, 11],
    'minor':          [0, 2, 3, 5, 7, 8, 10],
    'harmonic minor': [0, 2, 3, 5, 7, 8, 11],
    'dorian':         [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':     [0, 2, 4, 5, 7, 9, 10],
}


def build_scale(root, scale_type):
    """
    Build a sorted list of all MIDI pitch classes in the scale.

    Args:
        root: root note name string, e.g. 'A', 'C#', 'Bb'
        scale_type: scale type string, e.g. 'minor', 'major'

    Returns:
        List of 7 pitch classes (0-11), sorted ascending.

    Example:
        build_scale('A', 'minor') -> [0, 2, 3, 5, 7, 8, 9, 10]
        (A natural minor: A B C D E F G)
    """
    if root not in NOTE_NAME_TO_PC:
        raise ValueError(f"Unknown root note: '{root}'. Use C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B")
    if scale_type not in SCALE_INTERVALS:
        raise ValueError(f"Unknown scale type: '{scale_type}'. Use: {', '.join(SCALE_INTERVALS)}")

    root_pc = NOTE_NAME_TO_PC[root]
    intervals = SCALE_INTERVALS[scale_type]
    return sorted(set((root_pc + interval) % 12 for interval in intervals))


def harmonize_note(midi_note, scale_pcs):
    """
    Return the MIDI note number a diatonic 3rd above midi_note.

    Steps:
    1. Get pitch class of midi_note
    2. Snap to nearest pitch class in scale_pcs if not already in scale
    3. Find index of that pitch class in scale_pcs
    4. Move up 2 scale degrees (diatonic 3rd), wrapping octave if needed
    5. Return new MIDI note number in same octave region

    Args:
        midi_note: int, MIDI note number (0-127)
        scale_pcs: list of pitch classes in the scale (sorted, 0-11)

    Returns:
        int, MIDI note number for the harmony note
    """
    pc = midi_note % 12

    # Snap to nearest scale pitch class if not in scale
    if pc not in scale_pcs:
        pc = min(scale_pcs, key=lambda s: min(abs(s - pc), 12 - abs(s - pc)))

    idx = scale_pcs.index(pc)
    harmony_idx = idx + 2  # diatonic 3rd = 2 scale degrees up

    octave_shift = harmony_idx // len(scale_pcs)
    harmony_pc = scale_pcs[harmony_idx % len(scale_pcs)]

    base_octave = (midi_note // 12) * 12
    harmony_note = base_octave + harmony_pc + (octave_shift * 12)

    # Clamp to valid MIDI range
    harmony_note = max(0, min(127, harmony_note))
    return harmony_note
```

**Step 2: Manually verify scale building** by adding a quick print at the bottom and running:

```bash
py src/harmony_generator.py
```

Expected: no crash, file runs to end (no main block yet, just definitions).

---

### Task 2: Build the MIDI reader

**Files:**
- Modify: `src/harmony_generator.py` — add `read_midi_notes` function

**Step 1: Add function after `harmonize_note`**

```python
def read_midi_notes(midi_path):
    """
    Read all note_on/note_off events from a MIDI file, preserving timing.

    Reads from all tracks combined (merged), returns events in absolute tick order.

    Returns:
        List of dicts: [{'type': 'note_on'|'note_off', 'note': int, 'velocity': int, 'time': int}, ...]
        where 'time' is absolute ticks from start.
        Also returns ticks_per_beat (int) and tempo (int, microseconds per beat).
    """
    mid = MidiFile(midi_path)
    ticks_per_beat = mid.ticks_per_beat

    # Find tempo (default 500000 = 120 BPM)
    tempo = 500000
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break

    # Collect note events with absolute times from all tracks
    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type in ('note_on', 'note_off'):
                events.append({
                    'type': 'note_on' if (msg.type == 'note_on' and msg.velocity > 0) else 'note_off',
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'time': abs_time,
                })

    events.sort(key=lambda e: e['time'])
    return events, ticks_per_beat, tempo
```

**Step 2: Commit**

```bash
git add src/harmony_generator.py
git commit -m "feat: add scale utilities and MIDI reader for harmony generator"
```

---

### Task 3: Build the MIDI writer

**Files:**
- Modify: `src/harmony_generator.py` — add `write_harmony_midi` function

**Step 1: Add function after `read_midi_notes`**

```python
def write_harmony_midi(events, scale_pcs, ticks_per_beat, tempo, output_path):
    """
    Generate a harmony MIDI file from the given note events.

    For each note_on event, computes a diatonic 3rd-above harmony note.
    Preserves exact timing (delta times) from the original.

    Args:
        events: list of event dicts from read_midi_notes()
        scale_pcs: list of pitch classes from build_scale()
        ticks_per_beat: int
        tempo: int (microseconds per beat)
        output_path: str, full path for output file
    """
    mid = MidiFile()
    mid.ticks_per_beat = ticks_per_beat

    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(MetaMessage('track_name', name='Harmony', time=0))

    # Map original note -> harmony note so note_off targets the right pitch
    active_harmony = {}  # original_note -> harmony_note

    prev_abs = 0
    for event in events:
        delta = event['time'] - prev_abs
        prev_abs = event['time']

        if event['type'] == 'note_on':
            harmony_note = harmonize_note(event['note'], scale_pcs)
            active_harmony[event['note']] = harmony_note
            track.append(Message('note_on', note=harmony_note, velocity=event['velocity'], channel=0, time=delta))

        elif event['type'] == 'note_off':
            harmony_note = active_harmony.pop(event['note'], harmonize_note(event['note'], scale_pcs))
            track.append(Message('note_off', note=harmony_note, velocity=0, channel=0, time=delta))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"Done. Saved {output_path}")
```

---

### Task 4: Build the CLI entry point

**Files:**
- Modify: `src/harmony_generator.py` — add `parse_args` and `__main__` block

**Step 1: Add at the bottom of the file**

```python
def parse_args(argv):
    """
    Parse command-line arguments.

    Usage:
        harmony_generator.py input.mid --scale A minor [-o output.mid]

    Returns:
        (input_path, root, scale_type, output_path)
    """
    input_path = None
    output_path = None
    scale_root = None
    scale_type = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--scale':
            if i + 2 >= len(argv):
                print("Error: --scale requires two values, e.g. --scale A minor")
                sys.exit(1)
            scale_root = argv[i + 1]
            scale_type = argv[i + 2]
            i += 3
        elif arg in ('-o', '--output'):
            i += 1
            output_path = argv[i]
            i += 1
        else:
            input_path = arg
            i += 1

    return input_path, scale_root, scale_type, output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: py src/harmony_generator.py input.mid --scale A minor [-o output.mid]")
        sys.exit(1)

    input_path, scale_root, scale_type, output_path = parse_args(sys.argv[1:])

    if not input_path:
        print("Error: no input MIDI file provided")
        sys.exit(1)

    if not scale_root or not scale_type:
        print("Error: --scale is required. Example: --scale A minor")
        sys.exit(1)

    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    if output_path is None:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base}_harmony.mid")

    try:
        scale_pcs = build_scale(scale_root, scale_type)
        print(f"Scale: {scale_root} {scale_type} -> pitch classes {scale_pcs}")

        events, ticks_per_beat, tempo = read_midi_notes(input_path)
        print(f"Read {len([e for e in events if e['type'] == 'note_on'])} notes from {input_path}")

        write_harmony_midi(events, scale_pcs, ticks_per_beat, tempo, output_path)

    except (ValueError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)
```

**Step 2: Commit**

```bash
git add src/harmony_generator.py
git commit -m "feat: add harmony generator CLI - diatonic 3rd-above harmony from MIDI input"
```

---

### Task 5: Manual verification

**Step 1: Generate a test MIDI from an existing text file**

```bash
py src/multi_track_midi_generator.py aminor_lead.txt
```

This produces `output/aminor_lead.mid`.

**Step 2: Run harmony generator on it**

```bash
py src/harmony_generator.py output/aminor_lead.mid --scale A minor
```

Expected output:
```
Scale: A minor -> pitch classes [0, 2, 3, 5, 7, 8, 9, 10]
Read 16 notes from output/aminor_lead.mid
Done. Saved ...\output\aminor_lead_harmony.mid
```

**Step 3: Verify the output**
- Open `output/aminor_lead_harmony.mid` in a DAW or MIDI viewer
- Each note should be a diatonic 3rd above the corresponding melody note
- Timing should match the original exactly

---

### Task 6: Update HOW_TO_USE.txt

**Files:**
- Modify: `HOW_TO_USE.txt`

**Step 1: Add harmony section at the end**

```
HARMONY GENERATOR
-----------------
Generate a diatonic 3rd-above harmony track from an existing MIDI file.
Outputs a NEW midi file with only the harmony — original is untouched.

  py src/harmony_generator.py input.mid --scale A minor
  py src/harmony_generator.py input.mid --scale C major -o my_harmony.mid

Supported scales:
  major, minor, harmonic minor, dorian, mixolydian

Root note examples:
  A, A#, Bb, B, C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab

Output:
  output/<input_name>_harmony.mid
```

**Step 2: Commit**

```bash
git add HOW_TO_USE.txt
git commit -m "docs: document harmony generator in HOW_TO_USE.txt"
```
