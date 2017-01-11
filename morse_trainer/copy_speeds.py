#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Used to select character speed and show overall word speed.

speed = CopySpeeds()

speed.setState(wpm)     # sets the overall speed display
cwpm = speed.getState() # get the char wpm value set by the user

The widget generates a signal '.changed' when some value changes.
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel, QSpinBox, QGroupBox
from PyQt5.QtCore import pyqtSignal

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class CopySpeeds(QWidget):

    # signal raised when user changes cwpm
    changed = pyqtSignal(int, int)

    # maximum and minimum speeds
    MinSpeed = 5
    MaxSpeed = 40

    def __init__(self, char_speed=MinSpeed, word_speed=MaxSpeed):
        QWidget.__init__(self)
        self.initUI(char_speed, word_speed)
        self.setWindowTitle('Test Copy Speeds widget')
        self.setFixedHeight(80)
        self.show()

        # define state variables
        self.char_speed = char_speed
        self.word_speed = word_speed

    def initUI(self, char_speed, word_speed):
        # define the widgets we are going to use
        lbl_words = QLabel('  Overall')
        self.spb_words = QSpinBox(self)
        self.spb_words.setMinimum(CopySpeeds.MinSpeed)
        self.spb_words.setMaximum(CopySpeeds.MaxSpeed)
        self.spb_words.setValue(word_speed)
        self.spb_words.setSuffix(' wpm')

        lbl_chars = QLabel('Characters')
        self.spb_chars = QSpinBox(self)
        self.spb_chars.setMinimum(CopySpeeds.MinSpeed)
        self.spb_chars.setMaximum(CopySpeeds.MaxSpeed)
        self.spb_chars.setValue(char_speed)
        self.spb_chars.setSuffix(' wpm')

        # start the layout
        layout = QVBoxLayout()

        groupbox = QGroupBox("Speeds")
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl_chars)
        hbox.addWidget(self.spb_chars)
        hbox.addWidget(lbl_words)
        hbox.addWidget(self.spb_words)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

        # connect spinbox events to handlers
        self.spb_chars.valueChanged.connect(self.handle_charspeed_change)
        self.spb_words.valueChanged.connect(self.handle_wordspeed_change)

    def handle_wordspeed_change(self, word_speed):
        """Word speed changed.

        Ensure word speed <= char speed.  Bump char speed if necessary.
        """

        # save changed speed
        self.word_speed = word_speed

        # ensure char >= word speed
        if self.char_speed < word_speed:
            self.char_speed = word_speed
            self.spb_chars.setValue(word_speed)
            self.update()

        # tell the world there was a change
        self.changed.emit(self.char_speed, self.word_speed)

    def handle_charspeed_change(self, char_speed):
        """Character speed changed.

        Ensure char speed >= word speed.  Bump word speed if necessary.
        """

        # save changed speed
        self.char_speed = char_speed

        # ensure char >= word speed
        if char_speed < self.word_speed:
            self.word_speed = char_speed
            self.spb_words.setValue(char_speed)
            self.update()

        # tell the world there was a change
        self.changed.emit(self.char_speed, self.word_speed)

    def setState(self, wpm, cwpm=None):
        """Set the overall wpm speed.

        wpm   the overall words per minute (integer)
        cwpm  the character speed in words per minute (integer)
        """

        self.word_speed = wpm
        self.spb_words.setValue(wpm)

        if cwpm is not None:
            self.char_speed = cwpm
            self.spb_chars.setValue(cwpm)

        self.update()

    def getState(self):
        """Return the chosen speeds.


        Returns a tuple: (char_speed, word_speed)
        """

        return (self.char_speed, self.word_speed)
