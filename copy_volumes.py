#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A PyQt5 custom widget used by Morse Trainer.

Used to select code and noise sound levels.

volume = CopyVolumes()

volume.setState(signal, noise)
(signal, noise) = volume.getState()

The widget generates a signal '.changed' when some value changes.
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel, QSpinBox, QGroupBox, QCheckBox, QSpacerItem
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class CopyVolumes(QWidget):

    # signal raised when user changes state: signal, noise integer percentages
    changed = pyqtSignal(int, int)

    # display signal level and percentage
    levels = [('S0', 00), ('S1', 11), ('S2', 22), ('S3', 33), ('S4', 44),
              ('S5', 55), ('S6', 66), ('S7', 77), ('S8', 88), ('S9', 99)]

    # display QRN level and percentage
    qrn_levels = [('1 - none', 00), ('2 - slight', 25), ('3 - moderate', 50),
                  ('4 - severe', 75), ('5 - extreme', 99)]

    def __init__(self, signal=55, noise=0):
        QWidget.__init__(self)

        # define state variables
        self.inhibit = True
        self.signal = signal    # the default signal volume percentage
        self.noise = noise      # the default noise volume percentage

        # define the UI
        self.initUI()

        # connect combobox events to handlers
        self.cbo_signal.currentIndexChanged.connect(self.handle_signal_changed)
        self.cbo_noise.currentIndexChanged.connect(self.handle_noise_changed)

        # finish off display params
        self.setFixedHeight(80)
        self.show()
        self.inhibit = False

    def initUI(self):
        # define the widgets we are going to use
        lbl_signal = QLabel('Signal:')
        self.cbo_signal = QComboBox(self)
        for (l, p) in CopyVolumes.levels:
            self.cbo_signal.addItem(l, userData=p)

        lbl_noise = QLabel('QRN:')
        self.cbo_noise = QComboBox(self)
        for (l, p) in CopyVolumes.qrn_levels:
            self.cbo_noise.addItem(l, userData=p)

        # start the layout
        layout = QVBoxLayout()

        groupbox = QGroupBox("Audio Levels")
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl_signal)
        hbox.addWidget(self.cbo_signal)
        hbox.addItem(QSpacerItem(20, 20))
        hbox.addWidget(lbl_noise)
        hbox.addWidget(self.cbo_noise)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

        # define hover tooltop
        self.setToolTip('<font size=4>'
                        'This shows the signal and noise (QRN) levels:<br>'
                        '<center>'
                        '<table fontsize="4" border="1" style="width:100%">'
                        '<tr><td rowspan="2">Signal</td><td>S0</td><td>no signal</td></tr>'
                        '<tr><td>S9</td><td>maximum signal</td></tr>'
                        '<tr><td rowspan="2">QRN</td><td>1</td><td>no noise</td></tr>'
                        '<tr><td>5</td><td>maximum noise</td></tr>'
                        '</table>'
                        '</center>'
                        '</font>'
                       )

    def handle_signal_changed(self, index):
        """The widget signal level changed.

        index  index of the new signal level

        Raise self.changed event with new signal/noise percentages.
        """

        log('handle_signal_change: index=%s' % str(index))

        # save changed speed
        self.signal = self.cbo_signal.currentData()

        # tell the world there was a change, if allowed
        if not self.inhibit:
            self.changed.emit(self.signal, self.noise)

    def handle_noise_changed(self, index):
        """The widget noise level changed.

        index  index of the new noise level

        Raise self.changed event with new noise/noise percentages.
        """

        log('handle_noise_change: index=%s' % str(index))

        # save changed speed
        self.noise = self.cbo_noise.currentData()

        # tell the world there was a change, if allowed
        if not self.inhibit:
            self.changed.emit(self.signal, self.noise)

    def setState(self, signal, noise):
        """Set the overall widget state.

        signal  the signal volume percentage
        noise   the noise volume percentage
        """

        def percent2index(percent, levels_list):
            """Convert a percent value to canonical percent & combobox item index."""

            for (i, (l, p)) in enumerate(levels_list):
                if percent == p:
                    return (percent, i)
            raise RuntimeException('Got bad percent value: %s' % str(percent))

        self.inhibit = True

        (good_percent, index) = percent2index(signal, CopyVolumes.levels)
        self.signal = good_percent
        self.cbo_signal.setCurrentIndex(index)

        (good_percent, index) = percent2index(noise, CopyVolumes.qrn_levels)
        self.noise = good_percent
        self.cbo_noise.setCurrentIndex(index)

        self.inhibit = False

        self.update()

    def getState(self):
        """Return the widget state.

        Returns a tuple of percentages: (signal, noise) 
        """

        return (self.signal, self.noise)
