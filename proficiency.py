"""
A PyQt5 custom widget used by Morse Trainer.

Proficiency shows the proficiency for a GridDisplay data set.

proficiency = Proficiency(data)

where 'data' is the string used to establish a GridDisplay.

proficiency.setState(data):
where 'data' a dict of {char: (fraction, sample_size, threshold), ...} values
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QFont

import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class Proficiency(QWidget):
    """Widget to display a set of bars displaying success percentages."""

    # set platform-dependent sizes
    if platform.system() == 'Linux':
        Font = 'Courier'            # the font to use
        FontSize = 12               # font size
        TopMargin = 5               # top margin to bar
        LeftMargin = 5              # left margin to bar
        RightMargin = 5             # right margin to bar
        BottomMargin = 18           # bottom margin to bar
        LabelBottomMargin = 3       # bottom margin to text
        LabelLeftMargin = 7         # left margin to text
        InterBarMargin = 3          # margin between bars
        BarWidth = 11               # width of bar in pixels
        BarHeight = 100             # height of bar in pixels
    elif platform.system() == 'Darwin':
        Font = 'Courier'
        FontSize = 12
        TopMargin = 5
        LeftMargin = 5
        RightMargin = 5
        BottomMargin = 14
        LabelBottomMargin = 3
        LabelLeftMargin = 7
        InterBarMargin = 3
        BarWidth = 11
        BarHeight = 100
    elif platform.system() == 'Windows':
        Font = 'Courier'
        FontSize = 12
        TopMargin = 5
        LeftMargin = 5
        RightMargin = 5
        BottomMargin = 14
        LabelBottomMargin = 3
        LabelLeftMargin = 7
        InterBarMargin = 3
        BarWidth = 11
        BarHeight = 100
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())

    # proficiency at which Koch system adds another character
    KochThreshold = 0.9


    def __init__(self, data, threshold):
        """Initialize the widget.

        data       a string of characters to be displayed in the widget
        threshold  the Koch count threshold for the dataset

        The widget figures out how many bars there are from 'data'.
        """

        super().__init__()

        # declare state variables here so we know what they all are
        self.data = data            # the characters to display (in order)
        self.threshold = threshold  # Koch count threshold for the dataset
        self.fraction = []          # list of tuples (char, percent, colour)
        self.font = None            # the font used
        self.font_size = None       # size of font
        self.widget_width = None    # set in initUI()
        self.widget_height = None   # set in initUI()

        # set up the UI
        self.initUI()

    def initUI(self):
        """Set up the UI."""

        # calculate the number of display bars we will have
        num_chars = len(self.data)

        # figure out the widget size
        widget_width = (Proficiency.LeftMargin + num_chars*Proficiency.BarWidth
                        + (num_chars-1)*Proficiency.InterBarMargin
                        + Proficiency.RightMargin)
        widget_height = (Proficiency.TopMargin + Proficiency.BarHeight
                         + Proficiency.BottomMargin)

        self.setFixedWidth(widget_width)
        self.setFixedHeight(widget_height)
        self.setMinimumSize(widget_width, widget_height)

        self.widget_width = widget_width
        self.widget_height = widget_height

        # set the widget internal state
        self.font = QFont(Proficiency.Font, Proficiency.FontSize)
        self.font_size = Proficiency.FontSize

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

        # draw the threshold line
        threshold_height = int(Proficiency.BarHeight * self.threshold)
        line_y = Proficiency.TopMargin + Proficiency.BarHeight - threshold_height
        qp.setPen(Qt.red)
        qp.drawLine(0, line_y, self.widget_width, line_y)

        # draw outline of each bar
        qp.setPen(Qt.gray)
        x = Proficiency.LeftMargin
        y = Proficiency.TopMargin
        for _ in self.data:
            qp.drawRect(x, y, Proficiency.BarWidth, Proficiency.BarHeight)
            x += Proficiency.BarWidth + Proficiency.InterBarMargin

        # draw the percentage bar
        x = Proficiency.LeftMargin
        y = Proficiency.TopMargin
        for (char, percent, colour) in self.fraction:
            qp.setBrush(colour)
            pct_height = int(Proficiency.BarHeight * percent)
            if pct_height == 0:     # force *some* display if 0
                pct_height = 1
            top_height = Proficiency.BarHeight - pct_height
            qp.drawRect(x, y+top_height, Proficiency.BarWidth, pct_height)
            x += Proficiency.BarWidth + Proficiency.InterBarMargin

        # draw column 'footer' header
        x = Proficiency.LabelLeftMargin
        y = self.widget_height - Proficiency.LabelBottomMargin
        qp.setPen(Qt.black)
        for (char, _, _) in self.fraction:
            qp.drawText(x, y, char)
            x += Proficiency.BarWidth + Proficiency.InterBarMargin

    def setState(self, data):
        """Update self.fraction with values matching 'data'.

        data  a dict of {char: (fraction, sample_size, threshold), ...} values

        where threshold is the char count before Koch promotion can occur.
        """

        self.fraction = []
        for char in self.data:
            # get all pertinent for each character
            (fraction, sample_size, threshold) = data[char]
            try:
                (fraction, sample_size, threshold) = data[char]
            except KeyError:
                fraction = 0
                sample_size = 0
                threshold = 100

            # figure out what colour we are using
            colour = Qt.blue
            if sample_size >= threshold:
                colour = Qt.green
            elif sample_size < threshold * 0.80:
                colour = Qt.red
            self.fraction.append((char, fraction, colour))

        self.update()   # triggers a 'paint' event
