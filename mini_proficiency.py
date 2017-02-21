#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Mini-MiniProficiency shows the proficiency for the Koch test charset
in a space-efficient way.

proficiency = MiniProficiency(data)

where 'data' is the string of characters in the test set.

proficiency.setState(in_use, data):

where 'in_use'  is the number of characters of the dataset in use, and
      'data'    a dict of {char: (fraction, sample_size), ...} values.
"""

import platform

from PyQt5.QtWidgets import QWidget, QGridLayout, QToolTip
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QFont

import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class MiniProficiency(QWidget):
    """Display the Koch charset proficiency in a space-efficient way."""

    # set platform-dependent sizes
    if platform.system() == 'Linux':
        Font = 'Courier'            # the font to use
        FontSize = 12               # font size
        TopMargin = 10              # top margin
        LeftMargin = 5              # left margin
        RightMargin = 5             # right margin
        BottomMargin = 3            # bottom margin
        CharWidth = 7               # character spacing
        CharHeight = 10             # character 'height'
        TooltipFontSize = 4         # tooltip font size
    elif platform.system() == 'Darwin':
        Font = 'Courier'
        FontSize = 13
        TopMargin = 10
        LeftMargin = 5
        RightMargin = 3
        BottomMargin = 0
        CharWidth = 8
        CharHeight = 8
        TooltipFontSize = 4
    elif platform.system() == 'Windows':
        Font = 'Courier'
        FontSize = 12
        TopMargin = 10
        LeftMargin = 5
        RightMargin = 5
        BottomMargin = 3
        CharWidth = 8
        CharHeight = 10
        TooltipFontSize = 4
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())

    # define the colours used in characters
    ColourNoSamples = Qt.black      # not enough samples
    ColourOKErrors = Qt.blue        # sample good, OK error rate
    ColourBadErrors = Qt.red        # sample good, too many errors
    ColourNotInUse = Qt.lightGray   # not in use

    def __init__(self, data):
        """Initialize the widget.

        data       a string of characters to be displayed in the widget
        """

        super().__init__()

        # declare state variables here so we know what they all are
        self.data = data            # the characters to display (in order)
        self.in_use = 0             # the number of chars in self.data in use
        self.display_list = []      # list of tuples (char, colour)
        self.font = None            # the font used
        self.font_size = None       # size of font
        self.widget_width = None    # set in initUI()
        self.widget_height = None   # set in initUI()

        # set up the UI
        self.initUI()

    def initUI(self):
        """Set up the UI."""

        # calculate the number of characters we will have
        num_chars = len(self.data)

        # figure out the widget size
        widget_width = (MiniProficiency.LeftMargin
                        + num_chars*MiniProficiency.CharWidth
                        + MiniProficiency.RightMargin)
        widget_height = (MiniProficiency.TopMargin
                         + MiniProficiency.CharHeight
                         + MiniProficiency.BottomMargin)

        self.setFixedWidth(widget_width)
        self.setFixedHeight(widget_height)
        self.setMinimumSize(widget_width, widget_height)

        self.widget_width = widget_width
        self.widget_height = widget_height

        # set the widget internal state
        self.font = QFont(MiniProficiency.Font, MiniProficiency.FontSize)
        self.font_size = MiniProficiency.FontSize

        # set a tooltip on this custom widget
        self.setToolTip('<font size=4>'
                        'This shows the Koch test with colours showing usage:<br>'
                        '<center>'
                        '<table fontsize="4" border="1">'
                        '<tr><td>gray</td><td>not in use</td></tr>'
                        '<tr><td>black</td><td>character not tested enough</td></tr>'
                        '<tr><td>red</td><td>too many errors</td></tr>'
                        '<tr><td>blue</td><td>OK, low error rate</td></tr>'
                        '</table>'
                        '</center>'
                        '</font>'
                        )

    def paintEvent(self, e):
        """Prepare to draw the widget."""

        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        """Draw the widget from internal state."""

        # set to the font we use in the widget
        qp.setFont(self.font)

        # clear the display area
        qp.setPen(Qt.white)
        qp.setBrush(Qt.white)
        qp.drawRoundedRect(0, 0, self.widget_width, self.widget_height, 3, 3)

        # draw characters with colour coding
        x = MiniProficiency.LeftMargin
        y = MiniProficiency.TopMargin + 3
        qp.setBrush(Qt.green)
        for (char, colour) in self.display_list:
            qp.setPen(colour)
            qp.drawText(x, y, char)
            x += MiniProficiency.CharWidth

    def setState(self, in_use, stats, threshold, min_sample):
        """Update self.display_list with values matching 'data'.

        in_use      the number of characters in the test set in use
        stats       a dict of {char: (fraction, sample_size), ...} values
                    where fraction    is the measure of number right (float, [0.0,1.0]),
                          sample_size is the number of samples of character, and
        threshold   required proficiency before Koch promotion can occur
        min_sample  the required minimum sample size before promotion
        """

        self.in_use = in_use
        self.stats = stats

        self.display_list = []
        for (i, char) in enumerate(self.data):
            if i < in_use:
                # get all data pertinent for each character
                try:
                    (fraction, sample_size) = stats[char]
                except KeyError:
                    fraction = 0.0
                    sample_size = 0

                # figure out what colour we are using
                if sample_size < min_sample:
                    # not enough samples
                    colour = MiniProficiency.ColourNoSamples
                else:
                    if fraction >= threshold:
                        # sample good, OK error rate
                        colour = MiniProficiency.ColourOKErrors
                    else:
                        # sample good, too many errors
                        colour = MiniProficiency.ColourBadErrors
            else:
                # not in use
                colour = MiniProficiency.ColourNotInUse

            self.display_list.append((char, colour))

        self.update()   # redraw the widget

    def mousePressEvent(self, e):
        """Left click handler - show 'tooltip'."""

        # coding for e.button() and e.type() values
        # button = {1:'left', 2:'right', 4:'middle'}
        # type = {2:'single', 4:'double'}

        # single click, left button, show tooltip
        if e.type() == 2 and e.button() == 1:
            # figure out what character we clicked on, if any
            char_index = (e.x() - MiniProficiency.LeftMargin) // MiniProficiency.CharWidth
            char = self.data[char_index]
            if char_index < self.in_use:
                (correct, num_samples) = self.stats[char]
                text = ('Character: %s\n'
                        '%d samples\n'
                        '%d%% correct' % (char, num_samples, int(correct*100)))
            else:
                text = ('Character: %s\n'
                        'Not used' % char)

            num_newlines = text.count('\n')
            posn = e.globalPos()
            new_text = text.replace('\n', '<br>')
            QToolTip.showText(posn, '<font size=%d>%s</font>'
                              % (MiniProficiency.TooltipFontSize, new_text))
