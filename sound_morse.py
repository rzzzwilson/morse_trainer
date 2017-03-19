#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to make morse sounds from English characters.  We use a state
machine to send well-formed morse code.

morse = SoundMorse()

morse.set_speeds(chars_per_minute, words_per_minute)
(cwpm, wpm) = morse.get_speeds()

morse.set_volumes(signal, noise)
morse.set_frequency(frequency)

morse.close()
-------------

"""

import sys
import math
import audioop
import pyaudio
from random import randint

from noise_data import NoiseData

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class SoundMorse:
    """Send well-formed morse code to the speakers."""

    # the default settings
    DefaultCWPM = 10            # character speed (characters per minute)
    DefaultWPM = 5              # word speed (words per minute)
    DefaultSignal = 0.3         # in range [0.0, 1.0]
    DefaultNoise = 0.0          # in range [0.0, 1.0]
    DefaultFrequency = 700      # hertz

    # internal settings
    SampleRate = 14400          # samples per second
    Format = pyaudio.paInt8     # 8 bit audio

    # Words/minute below which we use the Farnsworth timing method
    FarnsworthThreshold = 18


    def __init__(self, signal=DefaultSignal, noise=DefaultNoise,
                       frequency=DefaultFrequency,
                       cwpm=DefaultCWPM, wpm=DefaultWPM):
        """Prepare the SoundMorse object."""

        # set send params to defaults
        self.cwpm = cwpm            # the character word speed
        self.wpm = wpm              # the word speed
        self.signal = signal        # signal volume (fraction)
        self.noise = 0.0            # noise volume (fraction)
        self.frequency = frequency  # audio frequency

        # prepare variables for created sound bites
        self.dot_sound = None
        self.dash_sound = None
        self.inter_element_silence = None
        self.inter_char_silence = None
        self.inter_word_silence = None

        # create sounds at default speeds
        self.create_sounds()

        # prepare the audio device
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(format=SoundMorse.Format,
                                        channels=1,
                                        rate=SoundMorse.SampleRate,
                                        output=True)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()

    def make_tone(self, duration, signal, noise=0.0):
        """Create a bytes sequence full of sinewave data.

        duration  time duration of string
        signal    volume of morse sound
        noise     volume of noise sound

        Result is a string of byte data.
        """

        MaxValue = 2**7 // 2
        LeadInOutCycles = 3

        # get number of samples in one tone cycle, create one cycle of sound
        num_cycle_samples = SoundMorse.SampleRate // self.frequency
        cycle = []
        for n in range(num_cycle_samples):
            value = int((math.sin(2*math.pi*n/num_cycle_samples)*MaxValue
                                  + MaxValue) * signal)
            cycle.append(value)

        # make complete tone
        data = []
        num_cycles = int(self.frequency * duration)
        for _ in range(num_cycles):
            data.extend(cycle)

        # add lead-in and lead-out
        lead_samples = num_cycle_samples*LeadInOutCycles
        for i in range(lead_samples):
            data[i] = int(data[i] * i/lead_samples)
            data[-i] = int(data[-i] * i/lead_samples)

        # make noise samples of same duration, add to morse signal
        if noise > 0.0:
            rand_offset = randint(100, 10000)
            num_samples = num_cycle_samples * num_cycles // 2
            noise_data = [int((nd * noise)/2) for nd in NoiseData[rand_offset:num_samples+rand_offset]]
            noise_sample = list(noise_data)
            noise_data.reverse()
            noise_sample += noise_data
            new_data = [int((d+n)/2) for (d, n) in zip(data, noise_data)]
            data = new_data

        return bytes(data)

    def create_sounds(self):
        """Create morse sounds from state variables.

        We use the ARRL documentation to set various timings.  Look in
        "Morse_Farnsworth.pdf" for the details.  NOTE: didn't actually
        use the data in that document as I couldn't make it work.  The
        spacing is calculated from first principles below.

        The input variables are:
            self.cwpm
            self.wpm
            self.signal
            self.noise
            self.frequency
            SoundMorse.SampleRate
        """

        # calculate dot and dash times, normal and Farnsworth
        (dot_time, dot_time_f) = utils.farnsworth_times(self.cwpm, self.wpm)

        dash_time = 3 * dot_time
        inter_elem_time = dot_time
        inter_char_time = 3 * dot_time
        inter_word_time = 7 * dot_time

        if self.wpm < SoundMorse.FarnsworthThreshold:
            # if using Farnsworth, stretch inter char/word times
            inter_char_time = 3 * dot_time_f
            inter_word_time = 7 * dot_time_f

        self.dot_sound = self.make_tone(dot_time, signal=self.signal, noise=self.noise)
        self.dash_sound = self.make_tone(dash_time, signal=self.signal, noise=self.noise)
        self.inter_element_silence = self.make_tone(inter_elem_time, signal=0.0, noise=self.noise)
        self.inter_char_silence = self.make_tone(inter_char_time, signal=0.0, noise=self.noise)
        self.inter_word_silence = self.make_tone(inter_word_time, signal=0.0, noise=self.noise)

    def set_speeds(self, cwpm=None, wpm=None):
        """Set morse speeds."""

        if cwpm or wpm:
            self.cwpm = cwpm
            self.wpm = wpm
            self.create_sounds()

    def get_speeds(self):
        """Get morse speeds."""

        return (self.cwpm, self.wpm)

    def set_volumes(self, signal, noise):
        """Set morse volumes.

        signal  signal volume percentage
        noise   noise volume percentage
        """

        self.signal = signal / 100.0
        self.noise = noise / 100.0
        self.create_sounds()

    def set_frequency(self, frequency):
        """Set tone frequency."""

        self.frequency = frequency
        self.create_sounds()

    def send(self, code):
        """Send characters in 'code' to speakers as morse."""

# TODO
# Look at reorganizing this.  Each element (dot or dash) should have a trailing
# inter-element silence.  Should add inter-character and inter-word silences when
# appropriate.

        # if, by some mischance we haven't created the sounds, do it now
        if self.dot_sound is None:
            self.create_sounds()

        # send the morse
        for char in code:
            char = char.upper()
            if char == ' ':
                self.stream.write(self.inter_word_silence)
            elif char in utils.Char2Morse:
                code = utils.Char2Morse[char]
                for s in code:
                    if s == '.':
                        self.stream.write(self.dot_sound)
                    elif s == '-':
                        self.stream.write(self.dash_sound)
                    self.stream.write(self.inter_element_silence)
            else:
                print("Unrecognized character '%s' in morse to send" % char)

            self.stream.write(self.inter_word_silence)


if __name__ == '__main__':
    for wpm in [5, 10, 15, 20, 25, 30, 35, 40, 45]:
        (dot_time, stretch_dot_time) = utils.farnsworth_times(wpm, wpm)
        print('wpm=%d, dot_time=%d' % (wpm, int(dot_time*500)))
