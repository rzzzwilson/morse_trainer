#!/usr/bin/env python3

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

    # maximum, minimum speeds and increment
    MinSpeed = 5
    MaxSpeed = 40
    StepSpeed = 5

    def __init__(self, char_speed=MinSpeed, word_speed=MaxSpeed):
        QWidget.__init__(self)
        self.inhibit = True
        self.initUI(char_speed, word_speed)
        self.setWindowTitle('Test Copy Speeds widget')
        self.setFixedHeight(80)
        self.show()
        self.inhibit = False

        # define state variables
        self.char_speed = char_speed
        self.word_speed = word_speed

    def initUI(self, char_speed, word_speed):
        # define the widgets we are going to use
        lbl_words = QLabel('  Word')
        self.spb_words = QSpinBox(self)
        self.spb_words.setMinimum(CopySpeeds.MinSpeed)
        self.spb_words.setMaximum(CopySpeeds.MaxSpeed)
        self.spb_words.setSingleStep(CopySpeeds.StepSpeed)
        self.spb_words.setValue(word_speed)
        self.spb_words.setSuffix(' wpm')

        lbl_chars = QLabel('Character')
        self.spb_chars = QSpinBox(self)
        self.spb_chars.setMinimum(CopySpeeds.MinSpeed)
        self.spb_chars.setMaximum(CopySpeeds.MaxSpeed)
        self.spb_chars.setSingleStep(CopySpeeds.StepSpeed)
        self.spb_chars.setValue(char_speed)
        self.spb_chars.setSuffix(' wpm')

        # start the layout
        layout = QVBoxLayout()

        groupbox = QGroupBox("Farnsworth Speeds")
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

        # helpful (?) tooltip
        self.setToolTip('<font size=4>'
            'This controls the sending speed. The Farnsworth method is used.<p>'
            'The "character" speed sets the speed each character is sent. '
            'The "word" speed sets the speed at which standard 5 character '
            'words are sent.  You should set the character speed to a reasonable '
            'speed such as 20wpm.  Use a slower word speed such as 10wpm or '
            '15wpm.  Increase the word speed as you become more proficient.'
            '</font>'
            )

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
        if not self.inhibit:
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
        if not self.inhibit:
            self.changed.emit(self.char_speed, self.word_speed)

    def setState(self, wpm, cwpm=None):
        """Set the overall wpm speed.

        wpm   the overall words per minute (integer)
        cwpm  the character speed in words per minute (integer)
        """

        if not cwpm:
            cwpm = wpm

        # force speeds to nearest 5wpm value
        canon_wpm = utils.make_multiple(wpm, 5)
        canon_cwpm = utils.make_multiple(cwpm, 5)

        self.inhibit = True
        self.word_speed = canon_wpm
        self.spb_words.setValue(canon_wpm)

        self.char_speed = canon_cwpm
        self.spb_chars.setValue(canon_cwpm)
        self.inhibit = False

        self.update()

    def getState(self):
        """Return the chosen speeds.


        Returns a tuple: (char_speed, word_speed)
        """

        return (self.char_speed, self.word_speed)
