#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to read morse sounds from the internal microphone and return
the English characters.  The code can read dynamic parameters from
a JSON file.  The dynamic parameters (possibly changed) can be save
back to a file.

morse = ReadMorse()

morse.load_params(params_file)

morse.save_params(params_file)

value = morse.average_stream()

char = morse.read()

morse.close()
"""


import sys
import json

import pyaudio
import numpy as np

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class ReadMorse:
    """A class to read and decode morse from the microphone."""

    CHUNK = 16
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 8000

    # lengths of various things (set for my slow speed!)
    LenDot = 30
    LenDash = LenDot * 3
    DotDashThreshold = (LenDot + LenDash)//2       # threshold between dot & dash

    MaxSignal = 5000
    MinSignal = 500
    SignalThreshold = 3000

    # lower sampling rate counters
    CharSpace = 3      # number of silences indicates a space
    WordSpace = 9      # number of silences to end word

    # the UNICODE character for "unrecognized"
    NOTHING = u'\u00bf'     # inverted 'question'


    def __init__(self):
        """Prepare the ReceiveMorse object."""

        # set receive params to defaults
        self.len_dot = ReadMorse.LenDot
        self.len_dash = ReadMorse.LenDash
        self.dot_dash_threshold = ReadMorse.DotDashThreshold
        self.char_space = ReadMorse.CharSpace
        self.word_space = ReadMorse.WordSpace
        self.max_signal = ReadMorse.MaxSignal
        self.min_signal = ReadMorse.MinSignal
        self.signal_threshold = ReadMorse.SignalThreshold

        self.sent_space = True
        self.sent_word_space = True

        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(format=ReadMorse.FORMAT,
                                        channels=ReadMorse.CHANNELS,
                                        rate=ReadMorse.RATE,
                                        input=True,
                                        frames_per_buffer=ReadMorse.CHUNK)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()

# seems to cause problems
#    def __del__(self):
#        self.close()

    def save_params(self, filename):
        """Save recognition params to file."""

        log.debug('Saving params to %s' % filename)

        if filename is None:
            return

        data_dict = {
                     'self.len_dot': self.len_dot,
                     'self.len_dash': self.len_dash,
                     'self.dot_dash_threshold': self.dot_dash_threshold,
                     'self.char_space': self.char_space,
                     'self.word_space': self.word_space,
                     'self.max_signal': self.max_signal,
                     'self.min_signal': self.min_signal,
                     'self.signal_threshold': self.signal_threshold
                     }

        json_str = json.dumps(data_dict, sort_keys=True, indent=4)

        with open(filename, 'w') as fd:
            fd.write(json_str + '\n')

    def load_params(self, filename):
        """Load recognition params from file, if it exists."""

        log.debug('Reading params from %s' % filename)

        if filename is None:
            return

        try:
            with open(filename, 'r') as fd:
                data = json.load(fd)
        except FileNotFoundError:
            return

        try:
            self.len_dot = data['self.len_dot']
            self.len_dash = data['self.len_dash']
            self.dot_dash_threshold = data['self.dot_dash_threshold']
            self.char_space = data['self.char_space']
            self.word_space = data['self.word_space']
            self.max_signal = data['self.max_signal']
            self.min_signal = data['self.min_signal']
            self.signal_threshold = data['self.signal_threshold']
        except KeyError:
            raise Exception('Invalid data in JSON file %s' % filename)

    def _decode_morse(self, morse):
        """Decode morse code character."""

        try:
            char = utils.Morse2Char[morse]
        except KeyError:
            #char = ReadMorse.NOTHING
            char = None
        return char

    def average_stream(self):
        """Get one average sample from the audio stream.

        Returns a single integer that is the average signal of one 'sample'.
        The average is taken from ReadMorse.CHUNK audio samples.
        """

        data = self.stream.read(ReadMorse.CHUNK, exception_on_overflow=False)
        #data = self.stream.read(ReadMorse.CHUNK)
        data = np.fromstring(data, 'int16')
        data = [abs(x) for x in data]
        return int(sum(data) // len(data))      # average value

    def _get_sample(self):
        """Return a sample tuple that indicates sound or silence.

        Returned values are a tuple: (N, average) where
             -N       silence for N samples
             N        N samples of sound (terminated by silence)
        and  average  is the average sound value in the sample.
        """

        # state values
        S_SOUND = 1
        S_SILENCE = 2

        # count of silence or sound time
        count = 0

        # no SOUND for this time is SILENCE
        SILENCE = 20

        # hang time before silence is noticed
        HOLD = 2

        state = S_SILENCE
        hold = HOLD

        values = []

        while True:
            value = self.average_stream()
            values.append(value)

            if state == S_SILENCE:
                # in SILENCE state
                if value < self.signal_threshold:
                    count += 1
                    if count >= SILENCE:
                        return (-count, sum(values) // len(values))
                else:
                    # we have a signal, change to SOUND state
                    state = S_SOUND
                    count = 1
                    values = [value]     # start value samples fresh
            else:
                # in SOUND state
                if value < self.signal_threshold:
                    hold -= 1
                    if hold <= 0:
                        # silence at the end of a SOUND period
                        # return SOUND result
                        return (count, sum(values) // len(values))
                else:
                    hold = HOLD
                    count += 1

    def read(self):
        """Returns one recognized character.

        Returns a tuple (char, morse)
        where char   is the recognized character (None if not recognized)
        and   morse  is the recognized morse dots'n'dashes string (None if no equivalent)
        """

        space_count = 0
        word_count = 0
        morse = ''

        while True:
            (count, level) = self._get_sample()

            if count > 0:
                # got a sound
                self.max_signal = level
                if count < 3:
                    continue    # not long enough, ignore

                self.sent_word_space = False
                self.sent_space = False
                space_count = 0
                word_count = 0

                # dot or dash?
                if count > self.dot_dash_threshold:
                    morse += '-'
                    self.len_dash = (self.len_dash*2 + count) // 3
                else:
                    morse += '.'
                    self.len_dot = (self.len_dot*2 + count) // 3

                self.dot_dash_threshold = (self.len_dot + self.len_dash) // 2
            else:
                # got a silence, bump silence counters & capture minimum
                space_count += 1
                word_count += 1
                self.min_signal = level

                # if silence long enough, emit a space
                if space_count >= self.char_space:
                    if morse:
                        return (self._decode_morse(morse), morse)
                    elif not self.sent_space:
                        self.sent_space = True
                        return (' ', None)
                    space_count = 0

                if word_count >= self.word_space:
                    if not self.sent_word_space:
                        self.sent_word_space = True
                        return (' ', None)
                    word_count = 0

            # set new signal threshold
            self.signal_threshold = (self.min_signal + 2*self.max_signal)//3
            log.debug('new .signal_threshold=%d' % self.signal_threshold)


if __name__ == '__main__':
    import sys
    import os
    import getopt

    # get program name from sys.argv
    prog_name = sys.argv[0]
    if prog_name.endswith('.py'):
        prog_name = prog_name[:-3]

    # path to file holding morse recognition parameters
    params_file = '%s.param' % prog_name

    def emit(char):
        print(char, end='')
        sys.stdout.flush()

    def usage(msg=None):
        if msg:
            print(('*'*80 + '\n%s\n' + '*'*80) % msg)
        print("\n"
              "CLI program to read morse from the microphone and\n"
              "print the received characters.\n\n"
              "Usage: morse [-f filename] [-h] [-l] [-s]\n\n"
              "where -f filename  means read params from filename\n"
              "      -h           means print this help and stop\n"
              "      -l           means don't load any params from file\n"
              "      -s           means don't save any params to file")


    # parse the CLI params
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'f:hls',
                                     ['file=', 'help', 'load', 'save'])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)

    read_param = True
    save_param = True
    for (opt, param) in opts:
        if opt in ['-f', '--file']:
            params_file = param
        elif opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ['-l', '--load']:
            read_param = False
        elif opt in ['-s', '--save']:
            save_param = False

    morse = ReadMorse()
    if read_param:
        morse.load_params(params_file)

    emit('*')       # show we are ready

    while True:
        try:
            char = morse.read()
            emit(char)
        except KeyboardInterrupt:
            emit('\nFinished\n')
            break

    if save_param:
        morse.save_params(params_file)
