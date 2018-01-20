#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Small utility functions.
"""


import sys
import traceback
from random import betavariate
from random import choice
from math import floor

import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


# various charsets
Alphabetics = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
Numbers = '0123456789'
Punctuation = """?,.!=/()'":;"""
AllUserChars = Alphabetics + Numbers + Punctuation

# all user chars in the 'Koch' order
Koch = """KMRSUAPTLOWI.NJE=F0Y,VG5/Q9ZH38B?427C1D6X():;!"'"""

# ensure Koch is same as AllUserChars
auc_sorted = ''.join(sorted(AllUserChars))
koch_sorted = ''.join(sorted(Koch))
if auc_sorted != koch_sorted:
    print('*'*80)
    print('* Error in utils.py, Koch and AllUserChars are different')
    print('*     len(Koch)=%d' % len(Koch))
    print('*     len(AllUserChars)=%d' % len(AllUserChars))
    print('*     auc_sorted= %s' % auc_sorted)
    print('*     koch_sorted=%s' % koch_sorted)
    print('*'*80)
    sys.exit(1)

# map chars to morse strings
Char2Morse = {
              '!': '-.-.--', '"': '.-..-.', '$': '...-..-', '&': '.-...',
              "'": '.----.', '(': '-.--.', ')': '-.--.-', ',': '--..--',
              '-': '-....-', '.': '.-.-.-', '/': '-..-.', ':': '---...',
              ';': '-.-.-.', '=': '-...-', '?': '..--..', '@': '.--.-.',
              '_': '..--.-', '+': '.-.-.',

              '0': '-----', '1': '.----', '2': '..---', '3': '...--',
              '4': '....-', '5': '.....', '6': '-....', '7': '--...',
              '8': '---..', '9': '----.',

              'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
              'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
              'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
              'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
              'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
              'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
              'Y': '-.--', 'Z': '--..',

              ' ': ' '
             }

# sequence of tuples (dot_time, wpm) used to interpolate
# put sentinel values both ends, MUST BE SORTED ON WPM!
# NOTE: this is arbitrary and will probably need adjustment
DotTime2Wpm = ((120, 0), (120, 5), (60, 10), (40, 15), (30, 20),
               (24, 25), (20, 30), (17, 35), (15, 40), (13, 45), (10, 50))

# invert above dict to create map of morse strings to chars
Morse2Char = {v:k for (k, v) in Char2Morse.items()}

# stylesheet code for PyQt5
StyleCSS = """
/*css stylesheet file that contains all the style information*/

table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
    padding: 15px;
    border-spacing: 5px;
}

QGroupBox {
    border: 1px solid black;
    border-radius: 3px;
}

QGroupBox:title{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding-left: 0px;
    padding-right: 5px;
    padding-top: -7px;
    border-top: none;
}
"""
#StyleCSS = ""


def str_trace(msg=None):
    """Get a traceback string.

    This is useful if we need at any point in code to find out how
    we got to that point.
    """

    result = []

    if msg:
        result.append(msg+'\n')

    result.extend(traceback.format_stack())

    return ''.join(result)


def log_trace(msg=None):
    """Log a traceback string."""

    log.debug(str_trace(msg))


def morse2display(morse):
    """Convert a string for a morse character to 'display' morse.

    We use this to display expected/received characters in the
    display as using ./- is not nice.  For example, '.-.' is not
    as nice as '• ━ •'
    """

    # unicode chars
    DOT = '•'    #2022
    DASH = '━'   #2501
    SIX_PER_EM_SPACE = ' '   #2005

    result = []
    for dotdash in morse:
        if dotdash == '.':
            result.append(DOT)
        elif dotdash in '-_':
            result.append(DASH)
        elif dotdash == ' ':
            result.append(' ')
        else:
            raise Exception("Unrecognized sign in '%s': %s" % (morse, dotdash))

    return SIX_PER_EM_SPACE.join(result)


def get_random_char(charset, stats, min_sample, threshold):
    """Get a random char from the charset sequence.

    charset     a string of characters we are testing
    stats       a dictionary of stats: {'A': [T, F, T, ...], ...}
    min_sample  number of samples before char is considered 'OK'
    threshold   percentage below which char is considered 'bad' (0.0, 0.999)

    Choose a character biased more towards the characters most in error.
    We do this by creating a list with ALL characters plus the characters
    with a low sample number or those below the proficiency threshold
    being duplicated.

    A low number of samples biases character(s) to be more frequent.
    """

    # make a list of characters we are going to choose from
    # chars with low proficiency are duplicated in this list,
    # as are chars with sample numbers less than the threshold
    choose_from = []

    for ch in charset:
        choose_from.append(ch)
        results = stats[ch]
        len_results = len(results)
        if len_results < min_sample:
            choose_from.append(ch)
            choose_from.append(ch)
        elif results.count(True) / len_results < threshold:
            choose_from.append(ch)
            choose_from.append(ch)

    return choice(choose_from)

def stats2errorrate(stats):
    """Convert stats data into an errorrate list.

    stats      dictionary holding statistics data

    The 'stats' data has the form {'A':[T,F,T], ...} where
    the list contains the last N results (True or False).

    The result is a list of characters sorted so the character with
    the highest error rate is first, etc.
    """

    # working list of tuples (rate, char)
    temp = []

    # get a list of (rate, char)
    for (char, result_list) in stats.items():
        sample_size = len(result_list)
        try:
            rate = result_list.count(True) / sample_size
        except ZeroDivisionError:
            # sample_size is zero, allocate low proficiency
            rate = 0.01
        if len(result_list) < 50:
            # if few results yet, test mostest, probably just added
            rate *= len(result_list)/50

        temp.append((rate, char))

    # sort by error rate, drop the rates
    temp2 = sorted(temp, key=lambda t: t[0], reverse=True)
    result = [ch for (_, ch) in temp2]

    return result


def char2morse(char):
    """Convert a character into a morse string."""

    return morse2display(Char2Morse[char.upper()])

def str2morse(string):
    """Convert a string into a morse string.

    Spaces are inserted between each character in morse.
    """

    return ' '.join([Char2Morse[ch] for ch in string.upper()])

def make_multiple(value, multiple):
    """Return integer value closest to 'value' that is multiple of 'multiple'."""

    return int(floor((value + multiple/2) / 5) * 5)

def wpm2params(wpm):
    """Convert a wpm value to morse params.

    wpm  speed in words per minute

    Returns a 'dot_time' in seconds.
    """

    # find tuples that are next highest and next lowest wpm
    # DotTime2Wpm is ((120, 0), (120, 5), (60, 10), ...), from slow to fast
    for (dot_time, dot_wpm) in DotTime2Wpm:
        if dot_wpm > wpm:
            # first tuple with faster speed, interpolate and return
            dot_range = low_dot - dot_time
            wpm_range = dot_wpm - low_wpm
            delta = dot_wpm - wpm
            ratio = delta / wpm_range
            new_dot_time = int(dot_time + ratio*dot_range)
            return new_dot_time
        else:
            # slower tuple, remember as slow speeds
            low_dot = dot_time
            low_wpm = dot_wpm

def params2wpm(dot_time):
    """Convert morse params into a wpm speed."""

    # find tuples that are next highest and next lowest dot_times
    # DotTime2Wpm is ((120, 0), (120, 5), (60, 10), ...), from slow to fast
    for (dot, wpm) in DotTime2Wpm:
        if dot < dot_time:
            # first tuple with lower dot_time
            wpm_range = wpm - low_wpm
            dot_range = low_dot - dot
            delta = low_dot - dot_time
            ratio = delta / dot_range
            new_wpm = int(low_wpm + ratio*wpm_range)
            return new_wpm
        else:
            # slower tuple, remember values
            low_dot = dot
            low_wpm = wpm
    log('SHOULD NOT GET HERE: dot_time=%d, DotTime2Wpm=%s' % (dot_time, str(DotTime2Wpm)))

def farnsworth_times(cwpm, wpm):
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



if __name__ == '__main__':
    morse = '.'
    while morse:
        morse = input('Enter morse (...-), nothing to exit: ')
        result = morse2display(morse)
        print(result)
