"""
Scale Converter - Synthwave MIDI Generator

Snaps all notes in a MIDI file to the nearest pitch class in a chosen scale.
Useful for transposing a melody to a different key/mode, or fixing out-of-scale notes.

Multi-track MIDI files are flattened to a single track on output.
Timing, velocity, and tempo are preserved exactly.

Usage:
    py src/scale_converter.py lead.mid --scale D minor
    py src/scale_converter.py lead.mid --scale G mixolydian -o output/lead_mix.mid
    py src/scale_converter.py lead.mid --scale A "harmonic minor"
    py src/scale_converter.py lead.mid --scale Bb major

Output:
    output/<input_name>_converted.mid
    output/<input_name>_converted.log
"""

import argparse
import os
import sys
from pathlib import Path

import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')

# ---------------------------------------------------------------------------
# Constants (inline — no shared imports with other scripts)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Scale helpers
# ---------------------------------------------------------------------------

def build_scale(root, scale_type):
    """Return sorted list of pitch classes for the target scale."""
    if root not in NOTE_NAME_TO_PC:
        raise ValueError(f"Unknown root note: '{root}'. Use: C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B")
    if scale_type not in SCALE_INTERVALS:
        raise ValueError(f"Unknown scale type: '{scale_type}'. Use: {', '.join(SCALE_INTERVALS)}")
    root_pc = NOTE_NAME_TO_PC[root]
    return sorted((root_pc + i) % 12 for i in SCALE_INTERVALS[scale_type])


# ---------------------------------------------------------------------------
# Core snapping logic
# ---------------------------------------------------------------------------

def snap_note(note, scale_pcs):
    """
    Snap a MIDI note number to the nearest pitch class in scale_pcs.
    Ties (equidistant) snap UP.
    Result is clamped to [0, 127].
    """
    pc = note % 12

    best_delta = None
    for scale_pc in scale_pcs:
        delta = (scale_pc - pc + 12) % 12   # 0..11 going up
        if delta > 6:
            delta -= 12                       # prefer down when strictly closer

        if best_delta is None:
            best_delta = delta
        elif abs(delta) < abs(best_delta):
            best_delta = delta
        elif abs(delta) == abs(best_delta) and delta > best_delta:
            best_delta = delta               # tie-break: prefer up

    return max(0, min(127, note + best_delta))


# ---------------------------------------------------------------------------
# MIDI I/O
# ---------------------------------------------------------------------------

def read_from_midi(filepath):
    """
    Read a MIDI file and return (events, ticks_per_beat, tempo).
    All tracks are merged and sorted by absolute tick time.
    Events: {'type': 'note_on'|'note_off', 'note': int, 'velocity': int, 'time': int}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    mid = MidiFile(filepath)
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000  # default 120 BPM

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
                events.append({
                    'type': msg.type,
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'time': abs_time,
                })

    events.sort(key=lambda e: e['time'])
    return events, ticks_per_beat, tempo


def write_converted_midi(events, ticks_per_beat, tempo, output_path):
    """Write a type-0 single-track MIDI from absolute-tick events."""
    mid = MidiFile(type=0, ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))

    prev_tick = 0
    for event in events:
        delta = event['time'] - prev_tick
        prev_tick = event['time']
        track.append(Message(
            event['type'],
            note=event['note'],
            velocity=event['velocity'],
            time=delta,
        ))

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    mid.save(output_path)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def convert(input_path, root, scale_type, output_path):
    """
    Build scale → read MIDI → snap all notes → write output.
    Returns (total_notes, changed_notes).
    total_notes counts sounding note_on events (velocity > 0).
    """
    scale_pcs = build_scale(root, scale_type)
    events, ticks_per_beat, tempo = read_from_midi(input_path)

    total_notes = 0
    changed_notes = 0

    for event in events:
        original = event['note']
        snapped = snap_note(original, scale_pcs)
        event['note'] = snapped

        if event['type'] == 'note_on' and event['velocity'] > 0:
            total_notes += 1
            if snapped != original:
                changed_notes += 1

    write_converted_midi(events, ticks_per_beat, tempo, output_path)
    return total_notes, changed_notes


# ---------------------------------------------------------------------------
# Output path & log helpers
# ---------------------------------------------------------------------------

def build_output_path(input_path, output_arg, root=None, scale_type=None):
    """Default: output/<stem>_<root>_<scale>_converted.mid. Returns output_arg if provided."""
    if output_arg:
        return output_arg
    stem = Path(input_path).stem
    if root and scale_type:
        safe_scale = scale_type.replace(' ', '_')
        return os.path.join(OUTPUT_DIR, f'{stem}_{root}_{safe_scale}_converted.mid')
    return os.path.join(OUTPUT_DIR, f'{stem}_converted.mid')


def write_log(log_path, input_path, root, scale_type, total_notes, changed_notes):
    """Write a plain-text conversion summary."""
    lines = [
        'Scale Converter Log',
        '===================',
        f'Input:           {input_path}',
        f'Target scale:    {root} {scale_type}',
        f'Total notes:     {total_notes}',
        f'Notes snapped:   {changed_notes}',
        f'Notes unchanged: {total_notes - changed_notes}',
    ]
    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Snap all notes in a MIDI file to a target scale.',
        epilog=(
            'Examples:\n'
            '  py src/scale_converter.py lead.mid --scale D minor\n'
            '  py src/scale_converter.py lead.mid --scale G mixolydian -o output/lead_mix.mid\n'
            '  py src/scale_converter.py lead.mid --scale A "harmonic minor"\n'
            '  py src/scale_converter.py lead.mid --scale Bb major\n\n'
            'Note: multi-track MIDI files are merged to a single track on output.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('input_file', help='Input MIDI file (.mid)')
    parser.add_argument(
        '--scale', nargs=2, metavar=('ROOT', 'TYPE'), required=True,
        help='Target scale, e.g. --scale D minor  or  --scale A "harmonic minor"',
    )
    parser.add_argument('-o', '--output', default=None, help='Output .mid file path')
    args = parser.parse_args()

    root, scale_type = args.scale

    try:
        build_scale(root, scale_type)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.input_file):
        print(f'Error: input file not found: {args.input_file}', file=sys.stderr)
        sys.exit(1)

    output_path = build_output_path(args.input_file, args.output, root, scale_type)

    try:
        total_notes, changed_notes = convert(args.input_file, root, scale_type, output_path)
    except Exception as e:
        print(f'Error during conversion: {e}', file=sys.stderr)
        sys.exit(1)

    log_path = str(Path(output_path).with_suffix('.log'))
    write_log(log_path, args.input_file, root, scale_type, total_notes, changed_notes)

    print(f'Converted: {output_path} ({changed_notes}/{total_notes} notes snapped to {root} {scale_type})')
