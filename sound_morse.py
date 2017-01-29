#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to make morse sounds from English characters.  We use a state
machine to send well-formed morse code.

morse = SoundMorse()

morse.set_speeds(chars_per_minute, words_per_minute)
(cwpm, wpm) = morse.get_speeds()

morse.set_volume(volume)
morse.set_frequency(frequency)

morse.close()
-------------

"""

import sys
import math
import audioop
import pyaudio

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class SoundMorse:
    """Send well-formed morse code to the speakers."""

    # the default settings
    DefaultCWPM = 10            # character speed (characters per minute)
    DefaultWPM = 5              # word speed (words per minute)
    DefaultVolume = 0.7         # in range [0.0, 1.0]
    DefaultFrequency = 700      # hertz

    # internal settings
    SampleRate = 14400          # samples per second
    Format = pyaudio.paInt8     # 8 bit audio

    # Words/minute below which we use the Farnsworth timing method
    FarnsworthThreshold = 18


    def __init__(self, volume=DefaultVolume, frequency=DefaultFrequency,
                       cwpm=DefaultCWPM, wpm=DefaultWPM):
        """Prepare the SoundMorse object."""

        # set send params to defaults
        self.cwpm = cwpm            # the character word speed
        self.wpm = wpm              # the word speed
        self.volume = volume        # volume
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

    def make_tone(self, duration, volume):
        """Create a bytes sequence full of sinewave data.

        duration  time duration of string
        volume    volume when string played

        Result is a string of byte data.
        """

        MaxValue = 2**7 // 2
        LeadInOutCycles = 3

        # get number of samples in one tone cycle, create one cycle of sound
        num_cycle_samples = SoundMorse.SampleRate // self.frequency
        cycle = []
        for n in range(num_cycle_samples):
            value = int((math.sin(2*math.pi*n/num_cycle_samples)*MaxValue + MaxValue) * volume)
            cycle.append(value)

        # make complete tone
        data = []
        for _ in range(int(self.frequency * duration)):
            data.extend(cycle)

        # add lead-in and lead-out
        lead_samples = num_cycle_samples*LeadInOutCycles
        for i in range(lead_samples):
            data[i] = int(data[i] * i/lead_samples)
            data[-i] = int(data[-i] * i/lead_samples)

        return bytes(data)

    def Xmake_tone(self, duration, volume):
        """Create a string full of sinewave data.

        duration  time duration of string
        volume    volume when string played

        Result is a string of byte data.
        """

        # calculate length of one cycle at rquired frequency
        cycle_len = SoundMorse.SampleRate // self.frequency
        num_cycles = int((duration * SoundMorse.SampleRate) // cycle_len)

        # create one cycle at required frequency+volume
        cycle_data = []
        for t in range(cycle_len):
            cycle_data.append(chr(int((math.sin(t*2*math.pi/cycle_len)*127+128)*volume)))

        # add cycles until required duration is reached
        result = []
        for _ in range(num_cycles):
            result.extend(cycle_data)

        result = ''.join(result)
        return result

    def farnsworth_times(self, cwpm, wpm):
        """Calculate Farnsworth spacing.

        cwpm  character speed, words/minute
        wpm   overall speed, words/minute

        Returns (dot_time, stretched_dot_time) times (in seconds).
        The 'stretched_dot_time' is used to calculate the inter-char and
        inter_word spacings in Farnsworth mode.
        """

        dot_time = (1.2 / cwpm)
        word_time_cwpm = 60 / cwpm
        word_time_wpm = 60 / wpm

        delta_per_word = word_time_wpm - word_time_cwpm
        stretched_dot_time = dot_time + delta_per_word/19

        return (dot_time, stretched_dot_time)

    def create_sounds(self):
        """Create morse sounds from state variables.

        We use the ARRL documentation to set various timings.  Look in
        "Morse_Farnsworth.pdf" for the details.  NOTE: didn't actually
        use the data in that document as I couldn't make it work.  The
        spacing is calculated from first principles below.

        The input variables are:
            self.cwpm
            self.wpm
            self.frequency
            SoundMorse.SampleRate
        """

        # calculate dot and dash times, normal and Farnsworth
        (dot_time, dot_time_f) = self.farnsworth_times(self.cwpm, self.wpm)

        dash_time = 3 * dot_time
        inter_elem_time = dot_time
        inter_char_time = 3 * dot_time
        inter_word_time = 7 * dot_time

        if self.wpm < SoundMorse.FarnsworthThreshold:
            # if using Farnsworth, stretch inter char/word times
            inter_char_time = 3 * dot_time_f
            inter_word_time = 7 * dot_time_f

        self.dot_sound = self.make_tone(dot_time, volume=self.volume)
        self.dash_sound = self.make_tone(dash_time, volume=self.volume)
        self.inter_element_silence = self.make_tone(inter_elem_time, volume=0.0)
        self.inter_char_silence = self.make_tone(inter_char_time, volume=0.0)
        self.inter_word_silence = self.make_tone(inter_word_time, volume=0.0)

    def set_speeds(self, cwpm=None, wpm=None):
        """Set morse speeds."""

        if cwpm or wpm:
            self.cwpm = cwpm
            self.wpm = wpm
            self.create_sounds()

    def get_speeds(self):
        """Get morse speeds."""

        return (self.cwpm, self.wpm)

    def set_volume(self, volume):
        """Set morse volume."""

        self.volume = volume
        self.create_sounds()

    def set_frequency(self, frequency):
        """Set tone frequency."""

        self.frequency = frequency
        self.create_sounds()

    def send(self, code):
        """Send characters in 'code' to speakers as morse."""

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
