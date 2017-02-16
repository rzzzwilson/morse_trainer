#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Shows the characters to be used in the send/receive tests.

charset = utils.MiniCharset(charset, num_used)

charset.setState(num_used, data, threshold, sample_size)
where 'num_used'     is the number of characters of the dataset in use, and
      'data'         a dict of {char: (fraction, sample_size, threshold), ...} values.
      'threshold'    the required proficiency before promotion
      'sample_size'  number od character samples before we count it
"""

import platform

from PyQt5.QtWidgets import QWidget, QGridLayout, QButtonGroup, QVBoxLayout
from PyQt5.QtWidgets import QGroupBox, QSpacerItem
from PyQt5.QtWidgets import QPushButton, QRadioButton, QSpinBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from mini_proficiency import MiniProficiency
import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class MiniCharset(QWidget):
    """Widget to display the characters used during send/receive ."""

    # set platform-dependent sizes
    if platform.system() == 'Linux':
        pass
    elif platform.system() == 'Darwin':
        pass
    elif platform.system() == 'Windows':
        pass
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())

    # set max/min numbers
    UsedMin = 2     # always at least 2 chars in test set in use


    def __init__(self, charset, num_used=UsedMin):
        """Initialize the widget.

        charset   the characters used
        num_used  the number of characters being used
        """

        super().__init__()

        # declare state variables here so we know what they all are
        self.num_used = num_used    # the number of characters used
        self.charset = charset      # the charset being used

        # set up the UI
        self.initUI()

        self.setFixedHeight(100)
        self.show()

    def initUI(self):
        """Set up the UI."""

        # create all the sub-widgets
        lbl_using = QLabel('   Using first')
        lbl_chars = QLabel('characters')
        self.lbl_UsedNumber = QLabel(str(self.num_used))
        self.lbl_Charset = QLabel('Test set:')
        self.mpr_proficiency = MiniProficiency(self.charset)

        layout = QVBoxLayout()
        groupbox = QGroupBox('Koch Test Set')
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        # assemble sub-widgets left-to-right
        grid = QGridLayout()
        grid.setSpacing(1)
        grid.setHorizontalSpacing(2)
        grid.setVerticalSpacing(1)

        row = 0
        grid.addWidget(self.lbl_Charset, row, 0)
        grid.addWidget(self.mpr_proficiency, row, 1)
        grid.addWidget(lbl_using, row, 2)
        grid.addWidget(self.lbl_UsedNumber, row, 3)
        grid.addWidget(lbl_chars, row, 4)

        # add empty column that stretches
        grid.addItem(QSpacerItem(1,1), row, 5)
        grid.setColumnStretch(5, 1)

        groupbox.setLayout(grid)
        self.setLayout(layout)

        self.setMinimumSize(500, 100)

        self.show()

    def setUsedNumber(self, num_used):
        """Set the 'used' number."""

        self.lbl_UsedNumber.setText(str(num_used))
        self.lbl_UsedNumber.update()

    def setState(self, num_used, data, threshold, sample_size):
        """Update internal values and redraw.

        num_used     number of characters being used
        data         a dict of {char: (fraction, sample_size), ...} values
                         where fraction    is the measure of number right (float, [0.0,1.0]),
                               sample_size is the number of samples of character, and
        threshold    required proficiency before promotion
        sample_size  need this number of samples before we can promote
        """

        self.num_used = num_used
        self.setUsedNumber(num_used)

        # set the the UI to show the above state
        self.mpr_proficiency.setState(num_used, data, threshold, sample_size)

        self.update()
