"""
Multi-Track MIDI Generator - Synthwave MIDI Generator

Generates a multi-track MIDI file by combining multiple text input files,
each representing a separate instrument/track (e.g. lead, bass, pad).

All features from midi_generator.py are preserved:
- Note parsing (C4, D#5, Bb3, etc.)
- Customizable rhythm patterns per track
- Scale/vibe detection
- Log file output

New features:
- Multiple tracks in a single MIDI file
- Per-track settings: name, program (instrument), channel, velocity
- Global tempo setting

Input file format (per track):
    name: Lead Synth
    program: 81
    channel: 0
    velocity: 100
    rhythm: 1.5, 0.5, 0.5, 1.5
    C4 E4 G4 B4
    D4 F#4 A4 C5
    E4 G#4 B4 D5
    F4 A4 C5 E5

All header lines are optional. Defaults:
    name:     derived from filename
    program:  80 (lead synth)
    channel:  auto-assigned (0, 1, 2, ...)
    velocity: 95
    rhythm:   1.5, 0.5, 0.5, 1.5

Usage:
    # Single track (works like midi_generator.py)
    python multi_track_midi_generator.py lead.txt

    # Multi-track: combine lead + bass + pad into one MIDI
    python multi_track_midi_generator.py lead.txt bass.txt pad.txt

    # Custom output filename
    python multi_track_midi_generator.py lead.txt bass.txt -o my_song.mid

    # Custom tempo (default: 110)
    python multi_track_midi_generator.py lead.txt bass.txt --tempo 120

Requirements:
- mido library (pip install mido)
"""

import os
import sys
import re
from collections import Counter
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


def note_to_midi(note_str):
    """Convert a note string (e.g., 'C4', 'D#5', 'Bb3') to MIDI note number."""
    note_str = note_str.strip()

    note_map = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    }

    match = re.match(r'^([A-Ga-g])([#b]?)(\d)$', note_str)
    if not match:
        raise ValueError(f"Invalid note format: '{note_str}'. Expected format: C4, D#5, Bb3, etc.")

    note_name = match.group(1).upper()
    accidental = match.group(2)
    octave = int(match.group(3))

    midi_note = (octave + 1) * 12 + note_map[note_name]

    if accidental == '#':
        midi_note += 1
    elif accidental == 'b':
        midi_note -= 1

    return midi_note


def midi_to_note_name(midi_note):
    """Convert a MIDI note number back to a note name string (e.g., 60 -> 'C4')."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    name = note_names[midi_note % 12]
    return f"{name}{octave}"


def parse_track_file(filepath, default_channel=0):
    """
    Read a track input file with optional header lines and note bars.

    Header lines (all optional, order doesn't matter):
        name: Lead Synth
        program: 81
        channel: 0
        velocity: 100
        rhythm: 1.5, 0.5, 0.5, 1.5

    Returns a dict with all track data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Defaults
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    track_info = {
        'name': base_name,
        'program': 80,
        'channel': default_channel,
        'velocity': 95,
        'rhythm_pattern': None,
        'notes': [],
        'note_names_per_bar': [],
        'num_bars': 0,
        'source_file': filepath,
    }

    # Parse header lines
    header_keys = {'name', 'program', 'channel', 'velocity', 'rhythm'}
    note_lines = []

    for line in lines:
        # Check if this is a header line (key: value)
        header_match = re.match(r'^(\w+)\s*:\s*(.+)$', line)
        if header_match:
            key = header_match.group(1).lower()
            value = header_match.group(2).strip()

            if key == 'name':
                track_info['name'] = value
            elif key == 'program':
                track_info['program'] = int(value)
            elif key == 'channel':
                track_info['channel'] = int(value)
            elif key == 'velocity':
                track_info['velocity'] = int(value)
            elif key == 'rhythm':
                rhythm_values = re.split(r'[,\s]+', value)
                rhythm_values = [v for v in rhythm_values if v]
                if len(rhythm_values) != 4:
                    raise ValueError(f"Rhythm pattern must have 4 values, got {len(rhythm_values)}")
                track_info['rhythm_pattern'] = [float(v) for v in rhythm_values]
            else:
                # Unknown header — treat as a note line
                note_lines.append(line)
        else:
            note_lines.append(line)

    if len(note_lines) < 4:
        raise ValueError(f"{filepath}: Expected at least 4 bars, got {len(note_lines)}")

    # Parse note bars
    for bar_num, line in enumerate(note_lines, 1):
        notes = re.split(r'[,\s]+', line)
        notes = [n for n in notes if n]

        if len(notes) != 4:
            raise ValueError(f"{filepath}, bar {bar_num}: Expected 4 notes, got {len(notes)}")

        track_info['note_names_per_bar'].append(notes)
        for note_str in notes:
            track_info['notes'].append(note_to_midi(note_str))

    track_info['num_bars'] = len(note_lines)
    return track_info


def detect_scale(midi_notes):
    """Detect the most likely musical scale from a list of MIDI notes."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    pitch_classes = sorted(set(n % 12 for n in midi_notes))

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

    first_pc = midi_notes[0] % 12
    last_pc = midi_notes[-1] % 12
    bar_starts = [midi_notes[i] % 12 for i in range(0, len(midi_notes), 4)]

    pc_counts = Counter(n % 12 for n in midi_notes)
    most_common_pc = pc_counts.most_common(1)[0][0]

    best_root = 0
    best_scale = 'major'
    best_score = -1

    for root in range(12):
        shifted = set((pc - root) % 12 for pc in pitch_classes)
        for scale_name, intervals in scales.items():
            scale_set = set(intervals)
            matches = len(shifted & scale_set)
            outside = len(shifted - scale_set)
            score = matches - outside * 2

            if root == first_pc:
                score += 3
            if root == last_pc:
                score += 2
            if root == most_common_pc:
                score += 1
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


def write_log(tracks, output_filename, tempo):
    """Write a log file with musical analysis for all tracks."""
    # Combine all notes for overall analysis
    all_midi_notes = []
    for t in tracks:
        all_midi_notes.extend(t['notes'])

    root, scale_type, pitch_classes = detect_scale(all_midi_notes)
    vibe = detect_vibe(all_midi_notes, scale_type)

    log_name = os.path.splitext(output_filename)[0] + '.log'
    log_path = os.path.join(OUTPUT_DIR, log_name)

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"=== Synthwave Multi-Track MIDI Generator - Log ===\n\n")
        f.write(f"Output file : {output_filename}\n")
        f.write(f"Tempo       : {tempo} BPM\n")
        f.write(f"Tracks      : {len(tracks)}\n")
        f.write(f"Root key    : {root}\n")
        f.write(f"Scale       : {root} {scale_type}\n")
        f.write(f"Vibe        : {vibe}\n")
        f.write(f"Pitch classes used: {', '.join(pitch_classes)}\n")

        for idx, t in enumerate(tracks):
            actual_rhythm = t['rhythm_pattern'] if t['rhythm_pattern'] else [1.5, 0.5, 0.5, 1.5]
            f.write(f"\n--- Track {idx + 1}: {t['name']} ---\n")
            f.write(f"  Source    : {os.path.basename(t['source_file'])}\n")
            f.write(f"  Program   : {t['program']}\n")
            f.write(f"  Channel   : {t['channel']}\n")
            f.write(f"  Velocity  : {t['velocity']}\n")
            f.write(f"  Bars      : {t['num_bars']}\n")
            f.write(f"  Notes     : {len(t['notes'])}\n")
            f.write(f"  Rhythm    : {actual_rhythm}\n")

            # Per-track scale detection
            t_root, t_scale, _ = detect_scale(t['notes'])
            f.write(f"  Scale     : {t_root} {t_scale}\n")

            f.write(f"  Notes per bar:\n")
            for i, bar in enumerate(t['note_names_per_bar'], 1):
                f.write(f"    Bar {i}: {' '.join(bar)}\n")

    print(f"Log saved: {log_path}")


def create_multi_track_midi(tracks, output_filename, tempo=110):
    """
    Create a multi-track MIDI file.

    Args:
        tracks: List of track info dicts from parse_track_file()
        output_filename: Output filename (without path)
        tempo: BPM (default 110)
    """
    mid = MidiFile()
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    for track_info in tracks:
        track = MidiTrack()
        mid.tracks.append(track)

        # Tempo on first track only
        if track_info is tracks[0]:
            track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

        track.append(MetaMessage('track_name', name=track_info['name'], time=0))

        # Program change (instrument selection)
        channel = track_info['channel']
        track.append(Message('program_change', program=track_info['program'], channel=channel, time=0))

        # Rhythm
        rhythm = track_info['rhythm_pattern']
        if rhythm is None:
            rhythm = [1.5, 0.5, 0.5, 1.5]

        all_durations = rhythm * track_info['num_bars']
        velocity = track_info['velocity']

        # Write notes
        for note, dur in zip(track_info['notes'], all_durations):
            ticks = int(dur * ticks_per_beat)
            track.append(Message('note_on', note=note, velocity=velocity, channel=channel, time=0))
            track.append(Message('note_off', note=note, velocity=0, channel=channel, time=ticks))

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    mid.save(output_path)
    print(f"Done. Saved {output_path}")


def parse_args(argv):
    """Parse command-line arguments."""
    input_files = []
    output_file = None
    tempo = 110

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ('-o', '--output'):
            i += 1
            if i < len(argv):
                output_file = argv[i]
            else:
                print("Error: -o requires a filename")
                sys.exit(1)
        elif arg == '--tempo':
            i += 1
            if i < len(argv):
                tempo = int(argv[i])
            else:
                print("Error: --tempo requires a value")
                sys.exit(1)
        else:
            input_files.append(arg)
        i += 1

    return input_files, output_file, tempo


if __name__ == "__main__":
    if len(sys.argv) < 2:
        default_input = os.path.join(PROJECT_DIR, 'example_input.txt')
        input_files = [default_input]
        output_file = None
        tempo = 110
    else:
        input_files, output_file, tempo = parse_args(sys.argv[1:])

    if not input_files:
        print("Usage: python multi_track_midi_generator.py track1.txt [track2.txt ...] [-o output.mid] [--tempo 120]")
        sys.exit(1)

    # Default output name: derived from first input file
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_files[0]))[0]
        if len(input_files) > 1:
            output_file = f"{base_name}_multitrack.mid"
        else:
            output_file = f"{base_name}.mid"

    try:
        # Parse all track files
        tracks = []
        used_channels = set()

        for idx, filepath in enumerate(input_files):
            track = parse_track_file(filepath, default_channel=idx)

            # Auto-assign channels to avoid conflicts (skip channel 9 — drums)
            if track['channel'] in used_channels:
                for ch in range(16):
                    if ch != 9 and ch not in used_channels:
                        track['channel'] = ch
                        break
            used_channels.add(track['channel'])

            tracks.append(track)
            rhythm_display = track['rhythm_pattern'] if track['rhythm_pattern'] else [1.5, 0.5, 0.5, 1.5]
            print(f"Track {idx + 1}: '{track['name']}' | {len(track['notes'])} notes ({track['num_bars']} bars) "
                  f"| ch:{track['channel']} prog:{track['program']} vel:{track['velocity']} "
                  f"| rhythm: {rhythm_display}")

        print(f"\nTempo: {tempo} BPM | Tracks: {len(tracks)}")
        create_multi_track_midi(tracks, output_file, tempo)
        write_log(tracks, output_file, tempo)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
