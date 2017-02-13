#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test code to explore setting parse params.
"""


import sys
import read_morse as rm
import logger
log = logger.Log('test.log', logger.Log.CRITICAL)

SampleSize = 1000

def main():
    log('main() called')
    in_stream = rm.ReadMorse()
    input('Ready for SILENCE ')

    quiet = []
    for _ in range(SampleSize):
        avg = in_stream.average_stream()
        quiet.append(avg)
    quiet_avg = sum(quiet) // len(quiet)
    quiet_max = max(quiet)
    quiet_min = min(quiet)
    log('quiet average=%d, min=%d, max=%d' % (quiet_avg, quiet_min, quiet_max))

    input('Ready for SOUND ')

    sound = []
    for _ in range(SampleSize):
        avg = in_stream.average_stream()
        sound.append(avg)
    sound_avg = sum(sound) // len(sound)
    sound_max = max(sound)
    sound_min = min(sound)
    log('sound average=%d, min=%d, max=%d' % (sound_avg, sound_min, sound_max))

    threshold = (sound_avg + quiet_avg) // 2
    log('threshold=%d' % threshold)

    input("Send morse until characters are recognized ")
    try:
        while True:
            char = in_stream.read()
            if char != ' ':
                print(char, end='')
            sys.stdout.flush()
    except KeyboardInterrupt:
        print('')

    in_stream.save_params('xyzzy.param')

main()
