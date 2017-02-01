#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Used to select overall word speed for the Send tab only.

speed = SendSpeeds()

speed.setState(active, wpm)     # sets the use checkbox and speed display

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
    changed = pyqtSignal(bool, int)

    # default use state
    DefaultUseState = True

    # maximum and minimum speeds
    MinSpeed = 5
    MaxSpeed = 40

    def __init__(self, use_state=DefaultUseState, speed=MinSpeed):
        QWidget.__init__(self)

        # define state variables
        self.inhibit = True
        self.use_state = use_state
        self.speed = speed

        # define the UI
        self.initUI()
        self.setFixedHeight(80)
        self.show()
        self.inhibit = True

    def initUI(self):
        # define the widgets we are going to use
        self.cb_use = QCheckBox('Send speed', self)
        self.cb_use.setChecked(self.use_state)

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
        hbox.addWidget(self.cb_use)
        hbox.addWidget(self.spb_speed)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

        # connect spinbox events to handlers
        self.cb_use.stateChanged.connect(self.handle_use_change)
        self.spb_speed.valueChanged.connect(self.handle_speed_change)

    def handle_use_change(self, use_state):
        """The Use State checkbox changed.

        state  boolean with new checkbox state

        Raise self.changed event with params.
        """

        # save changed speed
        self.use_state = use_state

        # disable the speed spinbox if not obeying speed
        self.spb_speed.setEnabled(use_state)

        # tell the world there was a change
        if not self.inhibit:
            self.changed.emit(self.use_state, self.speed)

    def handle_speed_change(self, word_speed):
        """The widget speed changed.

        word_speed  the new speed

        Raise self.changed event with params.
        """

        # save changed speed
        self.speed = word_speed

        # tell the world there was a change
        if not self.inhibit:
            self.changed.emit(self.use_state, self.speed)

    def setState(self, use_state, wpm):
        """Set the overall widget state.

        use_state  the checkbox state (boolean)
        wpm        the speed in words per minute (integer)
        """

        self.inhibit = True
        self.use_state = use_state
        self.cb_use.setChecked(use_state)

        self.speed = wpm
        self.spb_speed.setValue(wpm)
        self.spb_speed.setEnabled(use_state)
        self.inhibit = False

        self.update()

    def getState(self):
        """Return the widget state.

        Returns a tuple: (use_state, speed)
        """

        return (self.use_state, self.speed)
