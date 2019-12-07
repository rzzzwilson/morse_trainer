#!/usr/bin/env python3

"""
A simple test to play a tone for a certain period.

Creates the sine wave in a numpoy array
Doesn't do any on/off shaping of the data.
"""

import math
import numpy
import pyaudio

Frequency = 700     # tone frequency in Hz
Period = 5          # tone length in seconds


def sine(frequency, length, rate):
    length = int(length * rate)
    factor = float(frequency) * (math.pi * 2) / rate
    return numpy.sin(numpy.arange(length) * factor)


def play_tone(stream, frequency=440, length=1, rate=44100):
    chunks = []
    chunks.append(sine(frequency, length, rate))

    chunk = numpy.concatenate(chunks) * 0.25

    stream.write(chunk.astype(numpy.float32).tostring())


if __name__ == '__main__':
    print(f'Playing {Frequency}Hz tone for {Period} seconds.')
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1, rate=44100, output=1)

    play_tone(stream, frequency=Frequency, length=Period)

    stream.close()
    p.terminate()
