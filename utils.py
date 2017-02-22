#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Small utility functions.
"""


import sys
import traceback
from random import betavariate
from random import choices
from math import floor

import logger


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

# invert above dict to create map of morse strings to chars
Morse2Char = {v:k for (k, v) in Char2Morse.items()}

# stylesheet code for PyQt5
#StyleCSS = ""
StyleCSS = """
/*css stylesheet file that contains all the style information*/

table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
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

log = logger.Log('debug.log', logger.Log.CRITICAL)


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


def get_random_char(charset, stats):
    """Get a random char from the charset sequence.

    charset  a string of characters we are testing
    stats    a dictionary of stats: {'A': [T, F, T, ...], ...}

    Choose a character biased more towards the characters most in error.
    We do this by sorting the charset by error rate, then choosing from the
    front of the sorted list.

    A low number of samples biases character(s) to be more frequent.
    """

    # figure out the error rate of chars in the charset
    test_stats = {}
    for ch in charset:
        test_stats[ch] = stats[ch]
    ordered_charset = stats2errorrate(test_stats)

    bias = 0.5
    charset_len = len(charset)
    weights = [x+bias for x in range(charset_len)]
    sum_weights = sum(weights)
    normal_weights = [x/sum_weights for x in weights]

    return choices(ordered_charset, weights=normal_weights)[0]

def old_get_random_char(charset, stats):
    """Get a random char from the charset sequence.

    charset  a string of characters we are testing
    stats    a dictionary of stats: {'A': [T, F, T, ...], ...}

    Choose a character biased more towards the characters most in error.
    We do this by sorting the charset by error rate, then choosing from the
    front of the sorted list.
    """

    # figure out the error rate of chars in the charset
    test_stats = {}
    for ch in charset:
        test_stats[ch] = stats[ch]
    weighted_charset = stats2errorrate(test_stats)

    # choose randomly, but more likely the erroring char(s)
    beta = betavariate(1, 3)
    beta_len = beta * len(charset)
    rand_sample = floor(beta_len)
    result = weighted_charset[rand_sample]

    return result

def stats2errorrate(stats):
    """Convert stats data into an errorrate list.

    stats      dictionary holding statistics data

    The 'stats' data has the form {'A':[T,F,T], ...} where
    the list contains the last N results (True or False).

    The result is a list of characters sorted so the character with
    the highest error rate is forst, etc.
    """

    # working list of tuples (rate, char)
    temp = []

    # get a list of (rate, char)
    for (char, result_list) in stats.items():
        sample_size = len(result_list)
        rate = result_list.count(True) / sample_size
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


if __name__ == '__main__':
    morse = '.'
    while morse:
        morse = input('Enter morse (...-), nothing to exit: ')
        result = morse2display(morse)
        print(result)
