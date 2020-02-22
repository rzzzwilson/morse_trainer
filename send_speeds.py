"""
A PyQt5 custom widget used by Morse Trainer.

Used to select overall word speed for the Send tab only.

speed = SendSpeeds()

speed.setState(wpm)     # sets the speed display

The widget generates a signal '.changed' when some value changes.
"""

import platform

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel, QSpinBox, QGroupBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import pyqtSignal

import utils
import logger
log = logger.Log('debug.log', logger.Log.CRITICAL)


class SendSpeeds(QWidget):

    # signal raised when user changes cwpm
    changed = pyqtSignal(int)

    # maximum, minimum speeds and increment
    MinSpeed = 5
    MaxSpeed = 40
    StepSpeed = 5

    def __init__(self, speed=MinSpeed):
        QWidget.__init__(self)

        # define state variables
        self.inhibit = True
        self.speed = speed

        # define the UI
        self.initUI()
        self.setFixedHeight(80)
        self.show()
        self.inhibit = False

    def initUI(self):
        # define the widgets we are going to use
        lbl_set_speed = QLabel('Set to:')
        self.spb_speed = QSpinBox(self)
        self.spb_speed.setMinimum(SendSpeeds.MinSpeed)
        self.spb_speed.setMaximum(SendSpeeds.MaxSpeed)
        self.spb_speed.setSingleStep(SendSpeeds.StepSpeed)
        self.spb_speed.setSuffix(' wpm')
        self.spb_speed.setValue(self.speed)
        self.lbl_apparent_speed = QLabel('Apparent speed:')

        # start the layout
        layout = QVBoxLayout()

        groupbox = QGroupBox("Speed")
        groupbox.setStyleSheet(utils.StyleCSS)
        layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl_set_speed)
        hbox.addWidget(self.spb_speed)
        hbox.addItem(QSpacerItem(20, 20))
        hbox.addWidget(self.lbl_apparent_speed)
        hbox.addStretch()

        groupbox.setLayout(hbox)

        self.setLayout(layout)

        # helpful (?) tooltip
        self.setToolTip('<font size=4>'
                        'This provides a rough control over the speed Morse '
                        'Trainer will attempt to recognize.  Setting the '
                        'speed in the spinbox will configure the program to '
                        'recognize that speed.  Once the program recognizes '
                        'your code it will adapt to any speed variation.<p>'
                        'The "apparent speed" display is a rough attempt to '
                        'show the speed you are sending.'
                        '</font>'
                       )

        # connect spinbox events to handlers
        self.spb_speed.valueChanged.connect(self.handle_speed_change)

    def handle_speed_change(self, word_speed):
        """The widget speed changed.

        word_speed  the new speed

        Raise self.changed event with params.
        """

        # save changed speed
        self.speed = word_speed

        # tell the world there was a change, if allowed
        if not self.inhibit:
            self.changed.emit(self.speed)

    def setState(self, wpm):
        """Set the overall widget state.

        wpm  the speed in words per minute (integer)
        """

        # force speed to nearest 5wpm value
        canon_wpm = utils.make_multiple(wpm, 5)

        self.inhibit = True

        self.speed = canon_wpm
        self.spb_speed.setValue(canon_wpm)

        self.inhibit = False

        self.update()

    def getState(self):
        """Return the widget state.

        Returns the speed in wpm.
        """

        return self.speed

    def setApparentSpeed(self, wpm):
        """Set the apparent speed to 'wpm'."""

        new_text = 'Apparent speed: %d wpm' % wpm
        self.lbl_apparent_speed.setText(new_text)
        self.lbl_apparent_speed.update()
