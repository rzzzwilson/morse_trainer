#!/usr/bin/env python3

"""
A PyQt5 custom widget used by Morse Trainer.

Show the proficiency of all chars in the charset:
    alphas, numbers and punctuation.

cf = CharsetProficiency(alpha_data, number_data, punctuation_data)

where '*_data' is the string used to establish a GridDisplay.

cf.setState(dict)
(alpha, num, punct) = cf.getState()

where 'dict' is a dictionary: {'A':10, 'B':26, ...} that maps each
character to a 'success' percentage.  Note that the dictioanry contains
entries for all characters in the alpha, numbwr and punctuation sets.
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QFont

from proficiency import Proficiency
import utils


class CharsetProficiency(QWidget):
    """Widget to display a set of bars displaying success percentages."""

    # set platform-dependent sizes
    if platform.system() == 'Linux':
        pass
    elif platform.system() == 'Darwin':
        pass
    elif platform.system() == 'Windows':
        pass
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())


    def __init__(self, gbox_name, alpha, number, punct, threshold):
        """Initialize the widget.

        gbox_name  string to label groupbox with
        alpha      string of alphabetic characters
        number     string of number characters
        punct      string of punctuation characters
        threshold  the Koch count threshold for the dataset
        """

        super().__init__()

        # declare state variables here so we know what they all are
        self.alpha = alpha          # the alphabetic characters
        self.number = number        # the numeric characters 
        self.punct = punct          # the punctuation characters
        self.gbox_name = gbox_name  # label of the surrounding groupbox
        self.threshold = threshold  # the Koch count threshold

        # set up the UI
        self.initUI()

    def initUI(self):
        """Set up the UI."""

        # create all sub-widgets
        self.st_alpha = Proficiency(self.alpha, self.threshold)
        self.st_number = Proficiency(self.number, self.threshold)
        self.st_punct = Proficiency(self.punct, self.threshold)

        # layout the widget
        layout = QVBoxLayout()

        groupbox = QGroupBox(self.gbox_name)
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.st_alpha)
        hbox.addWidget(self.st_number)
        hbox.addWidget(self.st_punct)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

    def setState(self, data):
        """Update the three sub-widgets with values matching 'data'."""

        self.st_alpha.setState(data)
        self.st_number.setState(data)
        self.st_punct.setState(data)

        self.update()

    def getState(self):
        """Return a list with all three sub-widget's data strings."""

        return self.st_alpha.data + self.st_number.data + self.st_punct.data
