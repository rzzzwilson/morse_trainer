#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Small utility functions.
"""


import traceback

import logger


# various charsets
Alphabetics = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
Numbers = '0123456789'
Punctuation = """?,.!=/()'":;"""
AllUserChars = Alphabetics + Numbers + Punctuation

# amalgamated charset in the 'Koch' order
Koch = """KMRSUAPTLOWI.NJE=F0Y,VG5/Q9ZH38B?427C1D6X?():;!"'"""

StyleCSS = """
/*css stylesheet file that contains all the style information*/

QGroupBox {
    border: 1px solid black;
    border-radius: 3px;
}

QGroupBox:title{
    subcontrol-origin: margin;
/*    subcontrol-origin: content; */
/*    subcontrol-origin: padding; */
    subcontrol-position: top left;
    padding: -8px 5px 0 5;
}
"""

log = logger.Log('debug.log', logger.Log.DEBUG)


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

    log(str_trace(msg))


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


if __name__ == '__main__':
    morse = '.'
    while morse:
        morse = input('Enter morse (...-), nothing to exit: ')
        result = morse2display(morse)
        print(result)
