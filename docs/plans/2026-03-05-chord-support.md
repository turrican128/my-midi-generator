# Chord Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow beats in a bar to contain multiple simultaneous notes (chords) using `[C4 E4 G4]` syntax, while keeping single-note bars fully backward compatible.

**Architecture:** Parse each beat token as either a plain note or a `[...]` bracketed group. Store beats as lists of MIDI numbers internally. Update the MIDI writer to emit simultaneous note_on/note_off messages for chords.

**Tech Stack:** Python 3, mido

---

### Task 1: Update the beat parser in `parse_track_file`

**Files:**
- Modify: `src/multi_track_midi_generator.py` — `parse_track_file` function (lines ~163-178)

**Step 1: Replace the note-bar parsing block**

Find this block in `parse_track_file`:

```python
    # Parse note bars
    for bar_num, line in enumerate(note_lines, 1):
        notes = re.split(r'[,\s]+', line)
        notes = [n for n in notes if n]

        if len(notes) != 4:
            raise ValueError(f"{filepath}, bar {bar_num}: Expected 4 notes, got {len(notes)}")

        track_info['note_names_per_bar'].append(notes)
        for note_str in notes:
            track_info['notes'].append(note_to_midi(note_str))
```

Replace with:

```python
    # Parse note bars
    for bar_num, line in enumerate(note_lines, 1):
        beats = parse_beats(line)

        if len(beats) != 4:
            raise ValueError(f"{filepath}, bar {bar_num}: Expected 4 beats, got {len(beats)}")

        track_info['note_names_per_bar'].append(beats)
        for beat in beats:
            for note_str in beat:
                track_info['notes'].append(note_to_midi(note_str))
        track_info['beats'].append(beats)
```

Also add `'beats': []` to the `track_info` defaults dict (around line 120).

**Step 2: Add the `parse_beats` helper function** above `parse_track_file`:

```python
def parse_beats(line):
    """
    Parse a bar line into a list of 4 beats.
    Each beat is a list of note strings.
    Single note:  'C4'       -> ['C4']
    Chord:        '[C4 E4 G4]' -> ['C4', 'E4', 'G4']

    Example bar: '[C4 E4 G4] B4 A4 [G4 B4 D5]'
    Returns: [['C4','E4','G4'], ['B4'], ['A4'], ['G4','B4','D5']]
    """
    beats = []
    i = 0
    line = line.strip()
    while i < len(line):
        if line[i] == '[':
            end = line.index(']', i)
            chord_str = line[i+1:end].strip()
            notes = chord_str.split()
            beats.append(notes)
            i = end + 1
        elif line[i].isspace() or line[i] == ',':
            i += 1
        else:
            # Read until next whitespace, comma, or bracket
            j = i
            while j < len(line) and line[j] not in (' ', ',', '[', ']'):
                j += 1
            token = line[i:j].strip()
            if token:
                beats.append([token])
            i = j
    return beats
```

**Step 3: Commit**

```bash
git add src/multi_track_midi_generator.py
git commit -m "feat: parse chord beats [C4 E4 G4] syntax in bar lines"
```

---

### Task 2: Update the MIDI writer to emit chords

**Files:**
- Modify: `src/multi_track_midi_generator.py` — `create_multi_track_midi` function (lines ~347-350)

**Step 1: Replace the note-writing loop**

Find this block inside `create_multi_track_midi`:

```python
        # Write notes
        for note, dur in zip(track_info['notes'], all_durations):
            ticks = int(dur * ticks_per_beat)
            track.append(Message('note_on', note=note, velocity=velocity, channel=channel, time=0))
            track.append(Message('note_off', note=note, velocity=0, channel=channel, time=ticks))
```

Replace with:

```python
        # Write notes (supports single notes and chords)
        flat_beats = [note for bar in track_info['beats'] for note in bar]
        for beat_notes_str, dur in zip(flat_beats, all_durations):
            ticks = int(dur * ticks_per_beat)
            midi_notes = [note_to_midi(n) for n in beat_notes_str]
            for note in midi_notes:
                track.append(Message('note_on', note=note, velocity=velocity, channel=channel, time=0))
            for i, note in enumerate(midi_notes):
                track.append(Message('note_off', note=note, velocity=0, channel=channel, time=ticks if i == 0 else 0))
```

**Step 2: Commit**

```bash
git add src/multi_track_midi_generator.py
git commit -m "feat: emit simultaneous note_on/off for chord beats in MIDI output"
```

---

### Task 3: Update HOW_TO_USE.txt

**Files:**
- Modify: `HOW_TO_USE.txt`

**Step 1: Add chord syntax section** after the NOTE FORMAT section:

```
CHORD FORMAT
------------
Wrap multiple notes in square brackets to play them simultaneously:
  [C4 E4 G4]       = C major chord
  [A3 C4 E4]       = A minor chord

Mix chords and single notes freely — each bar still needs 4 beats:
  [C4 E4 G4] B4 A4 G4
  [A3 C4 E4] [G3 B3 D4] F4 E4
```

**Step 2: Commit**

```bash
git add HOW_TO_USE.txt
git commit -m "docs: document chord syntax in HOW_TO_USE.txt"
```

---

### Task 4: Manual verification

Run with a test file that mixes chords and single notes:

```
name: Chord Test
program: 81
[C4 E4 G4] B4 A4 G4
[A3 C4 E4] G3 F3 E3
[F3 A3 C4] D4 C4 B3
[G3 B3 D4] E4 D4 C4
```

```bash
py src/multi_track_midi_generator.py chord_test.txt
```

Expected output:
- No errors
- `output/chord_test.mid` created
- Open in a DAW or MIDI viewer — beat 1 of each bar should show 3 simultaneous notes
