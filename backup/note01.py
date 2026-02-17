"""
MIDI Generator - Nightrun Lead Melody

This script generates a MIDI file with a synth-wave style "Nightrun" lead melody.
It creates a 4-bar descending melodic pattern typical of 80s synthwave music,
using a syncopated rhythm that gives it a driving, nostalgic feel.

Features:
- Tempo: 100 BPM
- Time Signature: 4/4
- Rhythm: Syncopated pattern (dotted quarter, eighth, eighth, dotted quarter)
- 4 bars with descending melodic movement:
  * Bar 1: F4, E4, F4, D4 - Starting phrase
  * Bar 2: E4, D4, E4, C4 - Step down
  * Bar 3: D4, C4, D4, Bb3 - Continue descent
  * Bar 4: C4, Bb3, C4, A3 - Resolution

Output: nightrun_lead.mid (saved in the output/ directory)

Requirements:
- mido library (pip install mido)
"""

import os
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

# Get the project root directory (parent of src/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


def create_nightrun_midi():
    # 1. Setup MIDI File
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # 2. Settings
    bpm = 100
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Calculate tempo in microseconds per quarter note
    tempo = mido.bpm2tempo(bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(
        MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8,
                    time=0))
    track.append(MetaMessage('track_name', name='Nightrun Lead', time=0))

    # 3. Define the Rhythm (in beats)
    # Pattern: Dotted Quarter (1.5), Eighth (0.5), Eighth (0.5), Dotted Quarter (1.5)
    # Times are consistent for every bar
    durations = [1.5, 0.5, 0.5, 1.5]

    # Convert beats to ticks
    def beats_to_ticks(beats):
        return int(beats * ticks_per_beat)

    # 4. Define the Notes (MIDI numbers)
    # D4=62, E4=64, F4=65, G4=67, A4=69
    # C4=60, Bb3=58, A3=57

    # Bar 1: F4, E4, F4, D4
    bar1 = [65, 64, 65, 62]
    # Bar 2: E4, D4, E4, C4
    bar2 = [64, 62, 64, 60]
    # Bar 3: D4, C4, D4, Bb3
    bar3 = [62, 60, 62, 58]
    # Bar 4: C4, Bb3, C4, A3
    bar4 = [60, 58, 60, 57]

    all_notes = bar1 + bar2 + bar3 + bar4

    # Flatten the rhythm for the whole loop (4 bars * 4 notes per bar)
    all_durations = durations * 4

    # 5. Write Messages to Track
    velocity = 100

    for note, dur in zip(all_notes, all_durations):
        ticks = beats_to_ticks(dur)

        # Note ON
        track.append(Message('note_on', note=note, velocity=velocity, time=0))

        # Note OFF (after 'ticks' duration)
        # We use a slightly shorter duration for Note Off to create articulation (staccato vs legato)
        # For a lead, let's keep it fairly legato (full duration)
        track.append(Message('note_off', note=note, velocity=0, time=ticks))

    # 6. Save (in the output directory)
    output_filename = os.path.join(OUTPUT_DIR, 'nightrun_lead.mid')
    mid.save(output_filename)
    print(f"Successfully created {output_filename}")


if __name__ == "__main__":
    create_nightrun_midi()