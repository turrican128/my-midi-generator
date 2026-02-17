from midiutil import MIDIFile

track    = 0
channel  = 0
time     = 0          # start at beat 0
tempo    = 118
volume   = 105        # fairly strong but not crushing

MyMIDI = MIDIFile(1)
MyMIDI.addTempo(track, time, tempo)

# 4-bar pattern × 4 = 16 bars total
bass_pattern = [
    # Bar 1 (Cm)
    (36, 1.0),   # C2 long
    (43, 0.5),   # G2
    (48, 0.5),   # C3
    (41, 0.5),   # F2
    (36, 0.5),   # C2 short stab

    # Bar 2 (Ab)
    (44, 1.0),   # Ab2
    (51, 0.5),   # Eb3
    (56, 0.5),   # Ab3
    (39, 0.5),   # Eb2
    (44, 0.5),

    # Bar 3 (Eb)
    (39, 1.0),   # Eb2
    (46, 0.5),   # Bb2
    (51, 0.5),   # Eb3
    (46, 0.5),   # Bb2
    (39, 0.5),

    # Bar 4 (Bb → tension back to Cm)
    (46, 0.75),  # Bb2
    (53, 0.25),  # F3 quick
    (58, 0.5),   # Bb3
    (41, 0.5),   # F2
    (34, 1.0),   # Bb1 low anchor → resolves nicely to C
]

# Build full line: pattern × 3 + slight variation on last repeat
full_bass = bass_pattern * 3

# Last repeat: add some 80s "energy" with faster 16ths at end of bar 4
last_bar_variation = [
    (46, 0.25), (53, 0.25), (58, 0.25), (53, 0.25),   # quick Bb-F-Bb-F
    (51, 0.5),  (48, 0.5),  (46, 0.5),  (43, 0.5),
    (36, 2.0),                                         # long C2 finish
]

full_bass += last_bar_variation

# Write notes
current_time = 0
for pitch, dur in full_bass:
    MyMIDI.addNote(track, channel, pitch, current_time, dur, volume)
    current_time += dur

# Optional: very light extra octave jump at very end (classic 80s flourish)
MyMIDI.addNote(track, channel, 48, current_time - 2, 2.0, 90)  # C3 long on top

with open("80s_synth_bass.mid", "wb") as f:
    MyMIDI.writeFile(f)

print("Created 80s_synth_bass.mid — load it up!")