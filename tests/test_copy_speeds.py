#!/usr/bin/env python3

"""
Test the 'speeds' widget.
"""

import sys
sys.path.append('..')
from copy_speeds import CopySpeeds
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout

class SpeedsExample(QWidget):
    """Application to demonstrate the Morse Trainer 'display' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        self.speed_group = CopySpeeds()

        hbox = QHBoxLayout()
        hbox.addWidget(self.speed_group)
        self.setLayout(hbox)

        self.setWindowTitle('Example of Copy Speeds widget')
        self.setFixedSize(400, 125)
        self.show()

        # connect the widget to '.changed' event handler
        self.speed_group.changed.connect(self.speed_changed)

    def speed_changed(self, char_speed, word_speed):
        print('Changed speeds, cwpm=%d' % char_speed)
        print('Change overall speed to %d' % word_speed)


app = QApplication(sys.argv)
ex = SpeedsExample()
sys.exit(app.exec())
