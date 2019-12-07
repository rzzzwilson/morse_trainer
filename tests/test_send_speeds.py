#!/usr/bin/env python3

"""
Test the 'Send speeds' widget.
"""

import sys
import random

sys.path.append('..')
from send_speeds import SendSpeeds
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout

class SpeedsExample(QWidget):
    """Application to demonstrate the Morse Trainer 'Send speeds' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.speed_group = SendSpeeds()

        hbox = QHBoxLayout()
        hbox.addWidget(self.speed_group)
        self.setLayout(hbox)

        self.setWindowTitle('Example of Send Speeds widget')
        self.setFixedSize(400, 125)
        self.show()

        # connect the widget to '.changed' event handler
        self.speed_group.changed.connect(self.speed_changed)

    def speed_changed(self, speed):
        rand_speed = random.randint(5, 40)
        self.speed_group.setApparentSpeed(rand_speed)


app = QApplication(sys.argv)
ex = SpeedsExample()
sys.exit(app.exec())
