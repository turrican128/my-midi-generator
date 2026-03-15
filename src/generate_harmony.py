"""
Harmony Generator - Synthwave MIDI Generator

Reads a MIDI file or text file and generates a diatonic 3rd-above harmony track.
Outputs only the harmony as a new MIDI file — the original is untouched.

Usage:
    py src/generate_harmony.py input.mid
    py src/generate_harmony.py input.mid --scale A minor
    py src/generate_harmony.py input.txt --scale C major
    py src/generate_harmony.py input.mid -o my_harmony.mid

Output:
    output/<input_name>_harmony.mid

Supported scales:
    major, minor, harmonic minor, dorian, mixolydian
"""

import os
import sys
import re
import mido
from collections import Counter
from mido import Message, MidiFile, MidiTrack, MetaMessage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')

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
    if root not in NOTE_NAME_TO_PC:
        raise ValueError(f"Unknown root note: '{root}'. Use: C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B")
    if scale_type not in SCALE_INTERVALS:
        raise ValueError(f"Unknown scale type: '{scale_type}'. Use: {', '.join(SCALE_INTERVALS)}")
    root_pc = NOTE_NAME_TO_PC[root]
    return sorted(set((root_pc + i) % 12 for i in SCALE_INTERVALS[scale_type]))


DETECTED_TO_HARMONY_SCALE = {
    'natural minor':    'minor',
    'melodic minor':    'minor',
    'pentatonic major': 'major',
    'pentatonic minor': 'minor',
}


def detect_scale(midi_notes):
    """Detect scale from note list. Returns (root_name, scale_type) mapped to harmony-supported types."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    pitch_classes = sorted(set(n % 12 for n in midi_notes))

    scales = {
        'major':          [0, 2, 4, 5, 7, 9, 11],
        'minor':          [0, 2, 3, 5, 7, 8, 10],
        'harmonic minor': [0, 2, 3, 5, 7, 8, 11],
        'dorian':         [0, 2, 3, 5, 7, 9, 10],
        'mixolydian':     [0, 2, 4, 5, 7, 9, 10],
        'natural minor':  [0, 2, 3, 5, 7, 8, 10],
        'melodic minor':  [0, 2, 3, 5, 7, 9, 11],
        'pentatonic major': [0, 2, 4, 7, 9],
        'pentatonic minor': [0, 3, 5, 7, 10],
    }

    first_pc = midi_notes[0] % 12
    last_pc = midi_notes[-1] % 12
    bar_starts = [midi_notes[i] % 12 for i in range(0, len(midi_notes), 4)]
    pc_counts = Counter(n % 12 for n in midi_notes)
    most_common_pc = pc_counts.most_common(1)[0][0]

    best_root, best_scale, best_score = 0, 'major', -1

    for root in range(12):
        shifted = set((pc - root) % 12 for pc in pitch_classes)
        for scale_name, intervals in scales.items():
            scale_set = set(intervals)
            score = len(shifted & scale_set) - len(shifted - scale_set) * 2
            if root == first_pc: score += 3
            if root == last_pc:  score += 2
            if root == most_common_pc: score += 1
            score += sum(1 for bp in bar_starts if bp == root)
            if score > best_score:
                best_score = score
                best_root = root
                best_scale = scale_name

    root_name = note_names[best_root]
    scale_type = DETECTED_TO_HARMONY_SCALE.get(best_scale, best_scale)
    return root_name, scale_type


def harmonize_note(midi_note, scale_pcs):
    pc = midi_note % 12

    if pc not in scale_pcs:
        pc = min(scale_pcs, key=lambda s: min(abs(s - pc), 12 - abs(s - pc)))

    idx = scale_pcs.index(pc)
    harmony_idx = idx + 2  # diatonic 3rd = 2 scale degrees up

    octave_shift = harmony_idx // len(scale_pcs)
    harmony_pc = scale_pcs[harmony_idx % len(scale_pcs)]

    base_octave = (midi_note // 12) * 12
    harmony_note = base_octave + harmony_pc + (octave_shift * 12)
    return max(0, min(127, harmony_note))


def note_str_to_midi(note_str):
    note_str = note_str.strip()
    match = re.match(r'^([A-Ga-g])([#b]?)(\d)$', note_str)
    if not match:
        raise ValueError(f"Invalid note: '{note_str}'")
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    name = match.group(1).upper()
    acc = match.group(2)
    octave = int(match.group(3))
    midi = (octave + 1) * 12 + note_map[name]
    if acc == '#': midi += 1
    elif acc == 'b': midi -= 1
    return midi


def parse_beats(line):
    """Parse a bar line into a list of 4 beats, each beat a list of note strings."""
    beats = []
    i = 0
    line = line.strip()
    while i < len(line):
        if line[i] == '[':
            end = line.index(']', i)
            notes = line[i+1:end].strip().split()
            beats.append(notes)
            i = end + 1
        elif line[i] in (' ', ','):
            i += 1
        else:
            j = i
            while j < len(line) and line[j] not in (' ', ',', '[', ']'):
                j += 1
            token = line[i:j].strip()
            if token:
                beats.append([token])
            i = j
    return beats


def read_from_text(filepath):
    """
    Parse a text input file and return (events, ticks_per_beat, tempo).
    Events are in the same format as read_from_midi().
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    rhythm_pattern = [1.5, 0.5, 0.5, 1.5]
    bpm = None
    note_lines = []

    for line in lines:
        header_match = re.match(r'^(\w+)\s*:\s*(.+)$', line)
        if header_match:
            key = header_match.group(1).lower()
            value = header_match.group(2).strip()
            if key == 'rhythm':
                vals = re.split(r'[,\s]+', value)
                vals = [v for v in vals if v]
                if len(vals) == 4:
                    rhythm_pattern = [float(v) for v in vals]
            elif key == 'bpm':
                bpm = int(value)
            # all other headers (name, program, channel, velocity, unknown) are ignored
        else:
            note_lines.append(line)

    if len(note_lines) < 4:
        raise ValueError(f"{filepath}: Expected at least 4 bars, got {len(note_lines)}")

    ticks_per_beat = 480
    tempo = mido.bpm2tempo(bpm) if bpm else 500000  # default 120 BPM

    events = []
    abs_time = 0

    for bar_num, line in enumerate(note_lines, 1):
        beats = parse_beats(line)
        if len(beats) != 4:
            raise ValueError(f"{filepath}, bar {bar_num}: Expected 4 beats, got {len(beats)}")

        for beat_idx, beat in enumerate(beats):
            dur = rhythm_pattern[beat_idx]
            ticks = int(dur * ticks_per_beat)
            midi_notes = [note_str_to_midi(n) for n in beat]

            for note in midi_notes:
                events.append({'type': 'note_on', 'note': note, 'velocity': 95, 'time': abs_time})
            abs_time += ticks
            for note in midi_notes:
                events.append({'type': 'note_off', 'note': note, 'velocity': 0, 'time': abs_time})

    return events, ticks_per_beat, tempo


def read_from_midi(filepath):
    """Read note events from a MIDI file. Returns (events, ticks_per_beat, tempo)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    mid = MidiFile(filepath)
    ticks_per_beat = mid.ticks_per_beat

    tempo = 500000
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break

    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type in ('note_on', 'note_off'):
                etype = 'note_on' if (msg.type == 'note_on' and msg.velocity > 0) else 'note_off'
                events.append({'type': etype, 'note': msg.note, 'velocity': msg.velocity, 'time': abs_time})

    events.sort(key=lambda e: e['time'])
    return events, ticks_per_beat, tempo


def write_harmony_midi(events, scale_pcs, ticks_per_beat, tempo, output_path):
    """Write a new MIDI file with all notes harmonized a diatonic 3rd above."""
    mid = MidiFile()
    mid.ticks_per_beat = ticks_per_beat

    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(MetaMessage('track_name', name='Harmony', time=0))

    active_harmony = {}  # original note -> harmony note (to match note_off correctly)
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

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    mid.save(output_path)
    print(f"Done. Saved {output_path}")


def parse_args(argv):
    input_path = None
    output_path = None
    scale_root = None
    scale_type_parts = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--scale':
            i += 1
            if i < len(argv):
                scale_root = argv[i]
            i += 1
            # Collect remaining scale type words (e.g. "harmonic minor" = 2 words)
            while i < len(argv) and not argv[i].startswith('-'):
                scale_type_parts.append(argv[i])
                i += 1
        elif arg in ('-o', '--output'):
            i += 1
            output_path = argv[i]
            i += 1
        else:
            input_path = arg
            i += 1

    scale_type = ' '.join(scale_type_parts) if scale_type_parts else None
    return input_path, scale_root, scale_type, output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: py src/generate_harmony.py input.mid [--scale A minor]")
        print("       py src/generate_harmony.py input.txt [--scale C major]")
        print("       py src/generate_harmony.py input.mid -o harmony.mid")
        sys.exit(1)

    input_path, scale_root, scale_type, output_path = parse_args(sys.argv[1:])

    if not input_path:
        print("Error: no input file provided")
        sys.exit(1)
    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    if output_path is None:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base}_harmony.mid")

    ext = os.path.splitext(input_path)[1].lower()

    try:
        if ext in ('.mid', '.midi'):
            events, ticks_per_beat, tempo = read_from_midi(input_path)
        elif ext == '.txt':
            events, ticks_per_beat, tempo = read_from_text(input_path)
        else:
            print(f"Error: unsupported file type '{ext}'. Use .mid or .txt")
            sys.exit(1)

        if not scale_root or not scale_type:
            note_list = [e['note'] for e in events if e['type'] == 'note_on']
            if not note_list:
                print("Error: no notes found — cannot auto-detect scale. Use --scale.")
                sys.exit(1)
            scale_root, scale_type = detect_scale(note_list)
            print(f"Auto-detected scale: {scale_root} {scale_type}")

        scale_pcs = build_scale(scale_root, scale_type)
        print(f"Scale: {scale_root} {scale_type} -> {scale_pcs}")

        note_count = sum(1 for e in events if e['type'] == 'note_on')
        print(f"Read {note_count} notes from {input_path}")

        write_harmony_midi(events, scale_pcs, ticks_per_beat, tempo, output_path)

    except (ValueError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)
