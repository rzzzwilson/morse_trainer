#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Used to select overall word speed for the Send tab only.

speed = SendSpeeds()

speed.setState(wpm)     # sets the speed display

The widget generates a signal '.changed' when some value changes.
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel, QSpinBox, QGroupBox, QCheckBox
from PyQt5.QtCore import pyqtSignal

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class SendSpeeds(QWidget):

    # signal raised when user changes cwpm
    changed = pyqtSignal(int)

    # maximum and minimum speeds
    MinSpeed = 5
    MaxSpeed = 40

    def __init__(self, speed=MinSpeed):
        QWidget.__init__(self)

        # define state variables
        self.inhibit = True
        self.speed = speed

        # define the UI
        self.initUI()
        self.setFixedHeight(80)
        self.show()
        self.inhibit = True

    def initUI(self):
        # define the widgets we are going to use
        lbl_speed = QLabel('Speed')
        self.spb_speed = QSpinBox(self)
        self.spb_speed.setMinimum(SendSpeeds.MinSpeed)
        self.spb_speed.setMaximum(SendSpeeds.MaxSpeed)
        self.spb_speed.setSuffix(' wpm')
        self.spb_speed.setValue(self.speed)

        # start the layout
        layout = QVBoxLayout()

        groupbox = QGroupBox("Speed")
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.spb_speed)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

        # connect spinbox events to handlers
        self.spb_speed.valueChanged.connect(self.handle_speed_change)

    def handle_speed_change(self, word_speed):
        """The widget speed changed.

        word_speed  the new speed

        Raise self.changed event with params.
        """

        # save changed speed
        self.speed = word_speed

        # tell the world there was a change
        if not self.inhibit:
            self.changed.emit(self.speed)

    def setState(self, wpm):
        """Set the overall widget state.

        wpm  the speed in words per minute (integer)
        """

        self.inhibit = True

        self.speed = wpm
        self.spb_speed.setValue(wpm)
        self.inhibit = False

        self.update()

    def getState(self):
        """Return the widget state.

        Returns the speed in wpm.
        """

        return self.speed
