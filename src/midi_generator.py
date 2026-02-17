"""
MIDI Generator - Synthwave MIDI Generator

This script generates a MIDI file from a text file containing musical notes.

Features:
- Tempo: 110 BPM
- Customizable rhythm pattern (or default syncopated pattern)
- Supports 4 or more bars, each bar contains 4 notes

Text file format:
- Optional first line: rhythm pattern (4 values in beats)
- Each following line represents one bar (minimum 4 bars)
- Each bar contains 4 notes separated by spaces or commas
- Notes use standard notation: C4, D#5, Bb3, F#4, etc.
- Octave range: 0-9 (C4 = middle C = MIDI 60)

Rhythm values (in beats):
- 1.0 = quarter note (רבע)
- 0.5 = eighth note (שמינית)
- 1.5 = dotted quarter (רבע מנוקדת)
- 2.0 = half note (חצי)

Example text file with custom rhythm:
    rhythm: 1, 1, 1, 1
    C4 E4 G4 B4
    D4 F#4 A4 C5
    E4 G#4 B4 D5
    F4 A4 C5 E5

Example text file with default rhythm (syncopated: 1.5, 0.5, 0.5, 1.5):
    C4 E4 G4 B4
    D4 F#4 A4 C5
    E4 G#4 B4 D5
    F4 A4 C5 E5

Usage:
    python midi_generator.py input.txt          # Reads notes from text file
    python midi_generator.py input.txt out.mid  # Custom output filename

Requirements:
- mido library (pip install mido)
"""

import os
import sys
import re
from collections import Counter
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

# Get the project root directory (parent of src/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


def note_to_midi(note_str):
    """
    Convert a note string (e.g., 'C4', 'D#5', 'Bb3') to MIDI note number.

    Args:
        note_str: Note in format like 'C4', 'D#5', 'Bb3', 'F#4'

    Returns:
        MIDI note number (0-127)

    Examples:
        C4 -> 60 (middle C)
        A4 -> 69
        D#5 -> 75
    """
    note_str = note_str.strip()

    # Note name to semitone offset from C
    note_map = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    }

    # Parse the note string
    match = re.match(r'^([A-Ga-g])([#b]?)(\d)$', note_str)
    if not match:
        raise ValueError(f"Invalid note format: '{note_str}'. Expected format: C4, D#5, Bb3, etc.")

    note_name = match.group(1).upper()
    accidental = match.group(2)
    octave = int(match.group(3))

    # Calculate MIDI note number
    midi_note = (octave + 1) * 12 + note_map[note_name]

    # Apply accidental
    if accidental == '#':
        midi_note += 1
    elif accidental == 'b':
        midi_note -= 1

    return midi_note


def parse_notes_from_file(filepath):
    """
    Read notes and optional rhythm pattern from a text file.

    Expected format:
    - Optional first line: "rhythm: 1.5, 0.5, 0.5, 1.5" (4 values in beats)
    - At least 4 lines for bars (one per bar)
    - Each bar contains 4 notes separated by spaces or commas

    Args:
        filepath: Path to the text file

    Returns:
        Tuple of (list of MIDI note numbers, number of bars, rhythm pattern)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    all_notes = []
    note_names_per_bar = []  # Original note names grouped by bar
    rhythm_pattern = None  # Default will be set later if not specified

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Check if first line is a rhythm definition
    if lines and lines[0].lower().startswith('rhythm:'):
        rhythm_str = lines[0].split(':', 1)[1]
        rhythm_values = re.split(r'[,\s]+', rhythm_str.strip())
        rhythm_values = [v for v in rhythm_values if v]

        if len(rhythm_values) != 4:
            raise ValueError(f"Rhythm pattern must have 4 values, got {len(rhythm_values)}")

        try:
            rhythm_pattern = [float(v) for v in rhythm_values]
        except ValueError:
            raise ValueError(f"Invalid rhythm values. Expected numbers, got: {rhythm_values}")

        lines = lines[1:]  # Remove rhythm line from processing

    if len(lines) < 4:
        raise ValueError(f"Expected at least 4 bars (lines), got {len(lines)}")

    for bar_num, line in enumerate(lines, 1):
        # Split by comma or whitespace
        notes = re.split(r'[,\s]+', line)
        notes = [n for n in notes if n]  # Remove empty strings

        if len(notes) != 4:
            raise ValueError(f"Bar {bar_num}: Expected 4 notes, got {len(notes)}")

        note_names_per_bar.append(notes)

        for note_str in notes:
            midi_note = note_to_midi(note_str)
            all_notes.append(midi_note)

    return all_notes, len(lines), rhythm_pattern, note_names_per_bar


def midi_to_note_name(midi_note):
    """Convert a MIDI note number back to a note name string (e.g., 60 -> 'C4')."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    name = note_names[midi_note % 12]
    return f"{name}{octave}"


def detect_scale(midi_notes):
    """
    Detect the most likely musical scale from a list of MIDI notes.

    Returns:
        Tuple of (root note name, scale type, list of pitch class names)
    """
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Get unique pitch classes (0-11)
    pitch_classes = sorted(set(n % 12 for n in midi_notes))

    # Scale templates (intervals from root)
    scales = {
        'major':          [0, 2, 4, 5, 7, 9, 11],
        'natural minor':  [0, 2, 3, 5, 7, 8, 10],
        'harmonic minor': [0, 2, 3, 5, 7, 8, 11],
        'melodic minor':  [0, 2, 3, 5, 7, 9, 11],
        'dorian':         [0, 2, 3, 5, 7, 9, 10],
        'mixolydian':     [0, 2, 4, 5, 7, 9, 10],
        'pentatonic major': [0, 2, 4, 7, 9],
        'pentatonic minor': [0, 3, 5, 7, 10],
    }

    # Tonal anchors: first note, last note, and most frequent pitch class
    first_pc = midi_notes[0] % 12
    last_pc = midi_notes[-1] % 12
    # First note of each bar (every 4 notes) — strong beats
    bar_starts = [midi_notes[i] % 12 for i in range(0, len(midi_notes), 4)]

    # Count frequency of each pitch class
    pc_counts = Counter(n % 12 for n in midi_notes)
    most_common_pc = pc_counts.most_common(1)[0][0]

    best_root = 0
    best_scale = 'major'
    best_score = -1

    for root in range(12):
        shifted = set((pc - root) % 12 for pc in pitch_classes)
        for scale_name, intervals in scales.items():
            scale_set = set(intervals)
            # Count how many of our notes fit in this scale
            matches = len(shifted & scale_set)
            # Penalize notes that fall outside the scale
            outside = len(shifted - scale_set)
            score = matches - outside * 2

            # Bonus: root matches tonal anchors of the melody
            if root == first_pc:
                score += 3  # melody starts on this root
            if root == last_pc:
                score += 2  # melody resolves to this root
            if root == most_common_pc:
                score += 1  # most used pitch class
            # Bonus for bar downbeats landing on the root
            score += sum(1 for bp in bar_starts if bp == root)

            if score > best_score:
                best_score = score
                best_root = root
                best_scale = scale_name

    root_name = note_names[best_root]
    pitch_class_names = [note_names[pc] for pc in pitch_classes]

    return root_name, best_scale, pitch_class_names


def detect_vibe(midi_notes, scale_type):
    """Detect the vibe/mood based on note range, intervals, and scale type."""
    note_range = max(midi_notes) - min(midi_notes)
    avg_note = sum(midi_notes) / len(midi_notes)

    # Check for large jumps between consecutive notes
    jumps = [abs(midi_notes[i+1] - midi_notes[i]) for i in range(len(midi_notes)-1)]
    avg_jump = sum(jumps) / len(jumps) if jumps else 0

    minor_scales = ['natural minor', 'harmonic minor', 'melodic minor', 'pentatonic minor']
    is_minor = scale_type in minor_scales

    if is_minor and avg_note < 68:
        vibe = "Dark and moody"
    elif is_minor and avg_jump > 5:
        vibe = "Dramatic and intense"
    elif is_minor:
        vibe = "Melancholic and atmospheric"
    elif avg_jump > 5:
        vibe = "Energetic and uplifting"
    elif note_range > 18:
        vibe = "Expansive and cinematic"
    elif avg_note > 74:
        vibe = "Bright and dreamy"
    else:
        vibe = "Warm and groovy"

    return vibe


def write_log(midi_notes, note_names_per_bar, num_bars, output_filename, rhythm_pattern):
    """
    Write a log file with musical analysis alongside the MIDI file.

    The log includes: notes per bar, detected scale, root key, and vibe.
    """
    root, scale_type, pitch_classes = detect_scale(midi_notes)
    vibe = detect_vibe(midi_notes, scale_type)

    log_name = os.path.splitext(output_filename)[0] + '.log'
    log_path = os.path.join(OUTPUT_DIR, log_name)

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"=== Synthwave MIDI Generator - Log ===\n\n")
        f.write(f"Output file : {output_filename}\n")
        f.write(f"Root key    : {root}\n")
        f.write(f"Scale       : {root} {scale_type}\n")
        f.write(f"Vibe        : {vibe}\n")
        f.write(f"Bars        : {num_bars}\n")
        f.write(f"Total notes : {len(midi_notes)}\n")
        f.write(f"Rhythm      : {rhythm_pattern}\n")
        f.write(f"Pitch classes used: {', '.join(pitch_classes)}\n")
        f.write(f"\n--- Notes per bar ---\n")
        for i, bar in enumerate(note_names_per_bar, 1):
            f.write(f"  Bar {i}: {' '.join(bar)}\n")
        f.write(f"\n--- MIDI values ---\n")
        for i in range(num_bars):
            bar_notes = midi_notes[i*4:(i+1)*4]
            f.write(f"  Bar {i+1}: {bar_notes}\n")

    print(f"Log saved: {log_path}")


def create_midi(notes, num_bars, output_filename, rhythm_pattern=None):
    """
    Create a MIDI file with the given notes.

    Args:
        notes: List of MIDI note numbers (num_bars × 4 notes)
        num_bars: Number of bars
        output_filename: Output filename (without path)
        rhythm_pattern: List of 4 duration values in beats (default: [1.5, 0.5, 0.5, 1.5])
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # 1. Settings (110 BPM)
    bpm = 110
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    tempo = mido.bpm2tempo(bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(MetaMessage('track_name', name='Synthwave MIDI', time=0))

    # 2. Define Rhythm
    if rhythm_pattern is None:
        # Default: Syncopated Nightrun
        # 1.5 beats (dotted quarter) -> 0.5 (eighth) -> 0.5 (eighth) -> 1.5 (dotted quarter)
        rhythm_pattern = [1.5, 0.5, 0.5, 1.5]

    all_durations = rhythm_pattern * num_bars

    # 3. Generate Events
    velocity = 95

    for note, dur in zip(notes, all_durations):
        ticks = int(dur * ticks_per_beat)

        # Note ON
        track.append(Message('note_on', note=note, velocity=velocity, time=0))

        # Note OFF
        track.append(Message('note_off', note=note, velocity=0, time=ticks))

    # 4. Save (in the output directory)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    mid.save(output_path)
    print(f"Done. Saved {output_path}")


if __name__ == "__main__":
    # Default input file: example_input.txt in the project root
    default_input = os.path.join(PROJECT_DIR, 'example_input.txt')

    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # If no output filename given, derive from input filename
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}.mid"

    try:
        notes, num_bars, rhythm_pattern, note_names_per_bar = parse_notes_from_file(input_file)
        print(f"Loaded {len(notes)} notes ({num_bars} bars) from {input_file}")
        print(f"Notes (MIDI): {notes}")
        actual_rhythm = rhythm_pattern if rhythm_pattern else [1.5, 0.5, 0.5, 1.5]
        if rhythm_pattern:
            print(f"Rhythm pattern: {rhythm_pattern}")
        else:
            print("Rhythm pattern: default (1.5, 0.5, 0.5, 1.5)")
        create_midi(notes, num_bars, output_file, rhythm_pattern)
        write_log(notes, note_names_per_bar, num_bars, output_file, actual_rhythm)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)