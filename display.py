#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom 'display' widget used by Morse Trainer.

Display two lines of English text.  Allow colour change to background
for individual characters.  Allow outline highlighting for any group
of two vertical characters.  Allow tooltip text for any group of two
vertical characters.

display = Display(...)              # constructor

display.clear()                     # whole display cleared

display_id = display.insert_upper(ch, fg=None)  # insert char in upper row
display_id = display.insert_lower(ch, fg=None)  # insert char in lower row

display.set_tooltip(text)           # set tooltip at display end
display.update_tooltip(text)        # change tooltip at display end

display.set_highlight()             # set tooltip on latest column
"""

import platform

import utils

from PyQt5.QtWidgets import QWidget, QTableWidget, QPushButton, QMessageBox
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QFont, QColor, QPen
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class Display(QWidget):
    """Widget to display two rows of text for the Morse Trainer."""

    # define colours
    AskTextColour = Qt.black
    AnsTextGoodColour = Qt.blue
    AnsTextBadColour = Qt.red
    HighlightColour = QColor(255, 255, 153)
    HighlightEdgeColour = QColor(234, 234, 234)
    HoverColour = Qt.black
    HoverBGNoneColour = QColor(255, 255, 255, alpha=0)
    HoverBGTooltipColour = QColor(255, 0, 0, alpha=100)

    # set platform-dependent sizes
    if platform.system() == 'Windows':
        DefaultWidgetHeight = 55
        DefaultWidgetWidth = 600
        BaselineOffsetUpper = 24
        BaselineOffsetLower = 48
        FontSize = 30
        TextLeftOffset = 3
        RoundedRadius = 3.0
        TooltipOffset = 33
        TooltipLineOffset = 13
    elif platform.system() == 'Linux':
        DefaultWidgetHeight = 85
        DefaultWidgetWidth = 600
        BaselineOffsetUpper = 40
        BaselineOffsetLower = 80
        FontSize = 40
        TextLeftOffset = 3
        RoundedRadius = 3.0
        TooltipOffset = 33
        TooltipLineOffset = 13
    elif platform.system() == 'Darwin':
        DefaultWidgetHeight = 55
        DefaultWidgetWidth = 600
        BaselineOffsetUpper = 24
        BaselineOffsetLower = 48
        FontSize = 30
        TextLeftOffset = 3
        RoundedRadius = 3.0
        TooltipOffset = 33
        TooltipLineOffset = 13
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())

    # length of the test string used to determine character pixel width
    TestStringLength = 100

    def __init__(self):
        super().__init__()
        self.initUI()

        # clear the internal state
        self.clear()
        self.num_columns = 999999999

        # turn on mouse tracking
        self.setMouseTracking(True)

        # force a draw
        self.update()

        # get current width/height
        # height of widget never changes, width might
        self.display_width = self.width()
        self.display_height = self.height()

    def initUI(self):
        """Set up the UI."""

        # set the widget internal state
        self.setFixedHeight(Display.DefaultWidgetHeight)
        #self.fixed_font = QFont('Helvetica', Display.FontSize, QFont.DemiBold)
        self.fixed_font = QFont('Courier', Display.FontSize, QFont.DemiBold)
        self.font_size = Display.FontSize
        self.font = self.fixed_font

        # define start positions for upper and lower text
        self.upper_start = QPoint(Display.TextLeftOffset,
                                  Display.BaselineOffsetUpper)
        self.lower_start = QPoint(Display.TextLeftOffset,
                                  Display.BaselineOffsetLower)

        # cache for pixel size of one character in display (set in drawWidget())
        self.char_width = None

    def clear(self):
        """Clear the widget display."""

        # clear actual data in display
        self.text_upper = []        # tuples of (char, colour)
        self.text_lower = []

        self.tooltips = []          # list of tooltip text or None

        self.next_display_id = 0    # ID of next tooltip display ID

        self.highlight_index = None # index of current highlight

        self.hover_index = None     # mouse hovering over this column
        self.hover_rect_bg = False  # show hover rectangle background if True

        self.update()               # force a redraw

    def mouseMoveEvent(self, e):
        # remove any artifacts
        self.hover_rect_bg = False  # clear hover background flag

        index = self.x2index(e.x())
        self.hover_index = index
        if index is not None:
            # if we have tooltip text at this column, flag for display
            if self.tooltips[index]:
                self.hover_rect_bg = True
            self.update()

    def leaveEvent(self, e):
        self.hover_index = None
        self.update()

    def mousePressEvent(self, e):
        """Left click handler - maybe show 'tooltip'."""

        # coding for e.button() and e.type() values
        # button = {1:'left', 2:'right', 4:'middle'}
        # type = {2:'single', 4:'double'}

        # single click, left button, show tooltip, if any at position
        if e.type() == 2 and e.button() == 1:
            # figure out what index test we clicked on
            index = self.x2index(e.x())
            if index is not None and index >= 0:
                try:
                    text = self.tooltips[index]
                except IndexError:
                    text = None

                if text:
                    num_newlines = text.count('\n')
                    offset = (Display.TooltipOffset +
                              Display.TooltipLineOffset*num_newlines)
                    posn = e.globalPos() + QPoint(0, -offset)
                    QToolTip.showText(posn, '<font size=12>%s</font>' % text)

    def x2index(self, x):
        """Convert widget x coordinate to column index.

        Returns None if 'x' isn't in a column that is displayed.
        """

        index = (x - Display.TextLeftOffset + 1) // self.char_width
        max_length = max(self.upper_len(), self.lower_len())

        if not 0 <= index < max_length:
            index = None

        return index

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

        # calculate width of characters
        # should do this only on resize, but need a drawing context (qp)
        test_str = 'H' * Display.TestStringLength
        str_width = qp.fontMetrics().boundingRect(test_str).width()
        self.char_width = str_width // Display.TestStringLength + 4     # add extra spacing

        # figure out display size
        window_size = self.size()
        width = window_size.width()
        height = window_size.height()
        self.display_width = width

        # calc the max number of chars we can fit on display
        self.num_columns = (width - Display.TextLeftOffset) // self.char_width

        # figures out if we need to truncate the display to make it fit
        max_len = max(self.upper_len(), self.lower_len())
        if max_len > self.num_columns:
            self.left_scroll(max_len - self.num_columns)

        # clear the display area
        qp.setPen(Qt.white)
        qp.setBrush(Qt.white)
        qp.drawRoundedRect(0, 0, width, height,
                           Display.RoundedRadius, Display.RoundedRadius)

        # draw an outline
        qp.setPen(Qt.black)
        qp.drawRoundedRect(0, 0, self.display_width, self.display_height,
                           Display.RoundedRadius,
                           Display.RoundedRadius)

        # draw any highlights
        if self.highlight_index is not None:
            # calculate pixel offset of X start of highlight
            hl_x = Display.TextLeftOffset + self.char_width * self.highlight_index - 2
            # draw highlight rectangle
            qp.setPen(Display.HighlightEdgeColour)
            qp.setBrush(Display.HighlightColour)
            qp.drawRoundedRect(hl_x, 1, self.char_width,
                               Display.DefaultWidgetHeight,
                               Display.RoundedRadius,
                               Display.RoundedRadius)

        # draw upper text
        x = Display.TextLeftOffset
        last_colour = None
        for (char, colour) in self.text_upper:
            if last_colour != colour:
                qp.setPen(colour)
                last_colour = colour
            qp.drawText(x, Display.BaselineOffsetUpper, char)
            x += self.char_width

        # draw lower text
        x = Display.TextLeftOffset
        last_colour = None
        for (char, colour) in self.text_lower:
            if last_colour != colour:
                qp.setPen(colour)
                last_colour = colour
            qp.drawText(x, Display.BaselineOffsetLower, char)
            x += self.char_width

        # draw hover selection, if any
        if self.hover_index is not None:
            # calculate pixel offset of X start of hover selection
            hl_x = Display.TextLeftOffset + self.char_width * self.hover_index - 2
            # draw hover selection rectangle
            qp.setPen(Display.HoverColour)
            qp.setBrush(Display.HoverBGNoneColour)
            if self.hover_rect_bg:
                qp.setBrush(Display.HoverBGTooltipColour)
            qp.drawRoundedRect(hl_x, 0, self.char_width,
                               Display.DefaultWidgetHeight,
                               Display.RoundedRadius,
                               Display.RoundedRadius)

    def resizeEvent(self, e):
        """Handle widget resize.

        The main focus here is that we must scroll the display text if the
        width becomes small and limits the view.
        """

        # refresh display width and height
        self.display_width = self.width()
        self.display_height = self.height()

        # do we need to scroll?
        max_length = max(self.upper_len(), self.lower_len())
        if self.num_columns < max_length:
            self.left_scroll(max_length - self.num_columns)

    def upper_len(self):
        """Return length of the upper text."""

        return len(self.text_upper)

    def lower_len(self):
        """Return length of the lower text."""

        return len(self.text_lower)

    def insert_upper(self, ch, fg=None):
        """Insert char at end of upper row.

        ch  the character to insert
        fg  foreground colour of char
        """

        if fg is None:
            fg = Display.AskTextColour

        # add char to upper row
        self.text_upper.append((ch, fg))

        # if we extended display, add new empty tooltip
        if len(self.text_upper) > len(self.tooltips):
            self.set_tooltip(None)

        # decide if we have to scroll
        max_length = max(self.upper_len(), self.lower_len())
        if max_length > self.num_columns:
            self.left_scroll(max_length - self.num_columns)

        self.update()

    def insert_lower(self, ch, fg=None):
        """Insert char at end of lower row.

        ch     the character to insert
        fg     foreground colour of char
        """

        if fg is None:
            fg = Display.AnsTextGoodColour

        # add char to lower row
        self.text_lower.append((ch, fg))

        # if we extended display, add new empty tooltip
        if len(self.text_lower) > len(self.tooltips):
            self.set_tooltip(None)

        # decide if we have to scroll
        max_length = max(self.upper_len(), self.lower_len())
        if max_length > self.num_columns:
            self.left_scroll(max_length - self.num_columns)

        self.update()

    def set_tooltip(self, text):
        """"Add new tooltip at end of display.

        text  the tooltip text
        """

        self.tooltips.append(text)

    def update_tooltip(self, text):
        """"Change text in tooltip at end of display.

        text  the tooltip text
        """

        self.tooltips[-1] = text

    def left_scroll(self, num=None):
        """Left scroll display.

        num  number of columns to scroll left by

        If 'num' not supplied, scroll left a default amount.
        """

        # default the value for number of columns to scroll left
        if num is None:
            num = 1

        # do the scrolling
        self.text_upper = self.text_upper[num:]
        self.text_lower = self.text_lower[num:]
        self.tooltips = self.tooltips[num:]
        self.set_highlight()
        self.update()

    def set_highlight(self):
        """Show a highlight at end of display.

        If lower and upper rows same length, highlight one past end.
        """

        index = max(self.upper_len(), self.lower_len()) - 1

        if self.upper_len() == self.lower_len():
            index += 1

        self.highlight_index = index
        self.update()
