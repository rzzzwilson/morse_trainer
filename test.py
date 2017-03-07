#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the 'send_morse' module.
"""

import sys
import os
import getopt
import threading
sys.path.append('..')
from sound_morse import SoundMorse


# get program name from sys.argv
prog_name = sys.argv[0]
if prog_name.endswith('.py'):
    prog_name = prog_name[:-3]


def usage(msg=None):
    if msg:
        print(('*'*80 + '\n%s\n' + '*'*80) % msg)
    print("\n"
          "CLI program to continually send a morse string.\n\n"
          "Usage: %s [-h] [-s c,w] <string>\n\n"
          "where -h      means print this help and stop\n"
          "      -s c,w  means set char and word speeds\n\n"
          "and   <string>  is the morse string to repeatedly send\n"
          "The morse sound is created in a separate thread." % prog_name)

def send_morse(string, sound_object):
    # sound each character in the string
    # we do this in this strange way so setting a global from main code will stop the thread
    for ch in string:
        if StopThread:
            return
        sound_object.send(ch)


# parse the CLI params
argv = sys.argv[1:]

try:
    (opts, args) = getopt.getopt(argv, 'hs:', ['help', '--speed='])
except getopt.GetoptError as err:
    usage(err)
    sys.exit(1)

morse_string = ''.join(args)

cwpm = 25
wpm = 15
for (opt, param) in opts:
    if opt in ['-h', '--help']:
        usage()
        sys.exit(0)
    elif opt in ['-s', '--speed']:
        speeds = param.split(',')
        if len(speeds) not in (1, 2):
            usage("-s option must be followed by one or two speeds, eg: '-s 20' or '- 10,5'")
        cwpm = speeds[0]
        wpm = cwpm
        if len(speeds) == 2:
            (cwpm, wpm) = speeds
        cwpm = int(cwpm)
        wpm = int(wpm)

morse = SoundMorse()
morse.set_speeds(cwpm=cwpm, wpm=wpm)

StopThread = False

while True:
    for ch in morse_string:
        try:
            thread = threading.Thread(target=send_morse, args=(ch, morse))
            thread.start()
            thread.join()
            thread = None
        except KeyboardInterrupt:
            print('')
            StopThread = True
            if thread:
                thread.join()
            break
    print('*', end='')
    sys.stdout.flush()

