# scamp_band.py: a collection of scamp instruments, with some
# awareness of the practical range of the instrument. This
# just uses the standard scamp soundfont for now.

import random

from scamp_instruments import PITCHED_PERCUSSIVE_INSTRUMENT_NAMES

class ScampBand:
    def __init__(self, session):
        self._session = session
        self._percussive_instruments = []
        self._sustain_instruments = []
        self._play_count = 0

    def start(self):
        for instrument_name in PITCHED_PERCUSSIVE_INSTRUMENT_NAMES:
            self._percussive_instruments.append(self._session.new_part(instrument_name))

    def play_all_percussion(self, note):
        i = 0
        for instrument in random.sample(self._percussive_instruments, 32):
            print("%d: %s" % (i, instrument))
            i += 1
            instrument.play_note(note, 1.0, 0.5)
            self._session.wait(0.5)

    def play_random_percussion(self, note, volume=1.0, duration=1.0):
        inst = random.choice(self._percussive_instruments)
        print("play count: %d %s" % (self._play_count, inst))
        self._play_count += 1
        inst.play_note(note, volume, duration, blocking=False)

if __name__ == "__main__":
    from scamp import Session
    band = ScampBand(Session())
    band.start()
    while True:
        band.play_random_percussion(60)
