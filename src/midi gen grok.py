from midiutil import MIDIFile

degrees  = [60, 62, 63, 65, 67, 68, 70, 72]  # MIDI notes: C4 D4 Eb4 F4 G4 Ab4 Bb4 C5 etc.
track    = 0
channel  = 0
time     = 0    # In beats
duration = 0.5  # In beats (8th notes mostly)
tempo    = 120  # In BPM
volume   = 100  # 0-127, as per the MIDI standard

MyMIDI = MIDIFile(1)  # One track
MyMIDI.addTempo(track, time, tempo)

# Simple 80s-style melodic lead (repeating 8-bar phrase ×2)
melody_notes = [
    # Bar 1-2 (over Cm)
    60, 63, 67, 72,  67, 63, 60, 63,
    65, 68, 72, 75,  72, 68, 65, 60,
    # Bar 3-4 (over Ab)
    68, 72, 75, 80,  75, 72, 68, 65,
    63, 67, 70, 75,  70, 67, 63, 60,
    # Bar 5-6 (over Eb)
    63, 67, 70, 75,  70, 67, 63, 67,
    65, 68, 72, 77,  72, 68, 65, 60,
    # Bar 7-8 (over Bb → back to Cm)
    70, 74, 77, 82,  77, 74, 70, 65,
    67, 70, 74, 79,  74, 70, 67, 63,
]

# Repeat the phrase once (16 bars total)
melody_notes = melody_notes + melody_notes

for i, pitch in enumerate(melody_notes):
    MyMIDI.addNote(track, channel, pitch, time + i*0.5, duration, volume)

# A tiny bit of variation at the end (classic 80s "big note" finish)
MyMIDI.addNote(track, channel, 79, time + len(melody_notes)*0.5, 2.0, 110)     # long G5
MyMIDI.addNote(track, channel, 82, time + len(melody_notes)*0.5 + 2, 2.0, 100) # long Bb5

with open("80s_melodic_lead.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)

print("Created 80s_melodic_lead.mid — enjoy!")