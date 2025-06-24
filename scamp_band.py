# scamp_band.py: a collection of scamp instruments, with some
# awareness of the practical range of the instrument. This
# just uses the standard scamp soundfont for now.

import queue
import random

from scamp_instruments import PITCHED_PERCUSSIVE_INSTRUMENT_NAMES
from scamp_instruments import SUSTAIN_INSTRUMENT_NAMES

class ScampPlayer:
    def __init__(self, session, instrument_name):
        self._session = session
        self._instrument = self._session.new_part(instrument_name)

    def play_note(self, note, volume=1.0, duration=1.0):
        self._instrument.end_all_notes()
        self._instrument.play_note(note, volume, duration, blocking=False)
        #self._session.wait(0.001)  #  XXX why?

    def end_all_notes(self):
        self._instrument.end_all_notes()


class ScampBand:
    def __init__(self, session):
        self._session = session
        self._percussive_instruments = []
        self._sustain_instruments = []
        self._play_count = 0

    def start(self):
        for instrument_name in PITCHED_PERCUSSIVE_INSTRUMENT_NAMES:
            self._percussive_instruments.append(ScampPlayer(self._session, instrument_name))
        for instrument_name in SUSTAIN_INSTRUMENT_NAMES[:10]:
            self._sustain_instruments.append(ScampPlayer(self._session, instrument_name))

    def play_all_percussion(self, note):
        i = 0
        for instrument in self._percussive_instruments:
            print("%d: %s" % (i, instrument))
            i += 1
            instrument.play_note(note, 1.0, 0.5)
            self._session.wait(0.5)

    def play_random_percussion(self, note, volume=1.0, duration=0.001):
        inst = random.choice(self._percussive_instruments)
        # Turn off any playing note, to avoid stuck notes
        inst.end_all_notes()
        inst.play_note(note, volume, duration)
        #self._session.wait(0.1)
        self._play_count += 1
        #print("play_count: %d" % self._play_count)

    def play_random_sustained(self, note, volume=1.0, duration=1.0):
        inst = random.choice(self._sustain_instruments)
        # Turn off any playing note, to avoid stuck notes
        inst.end_all_notes()
        inst.play_note(note, volume, duration)

if __name__ == "__main__":
    from scamp import Session
    band = ScampBand(Session())
    band.start()
    band.play_all_percussion(48)
    while True:
        band.play_random_percussion(60)
        band._session.wait(1.0)
