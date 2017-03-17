#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Test the 'Copy Volumes' widget.
"""

import sys
import random

sys.path.append('..')
from copy_volumes import CopyVolumes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSpacerItem

class SpeedsExample(QWidget):
    """Application to demonstrate the Morse Trainer 'Copy Volumes' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()
        self.button.clicked.connect(self.button_clicked)

    def initUI(self):
        self.volume_group = CopyVolumes(self)
        self.button = QPushButton('Set random percentages', self)

        vbox = QVBoxLayout()
        vbox.addWidget(self.volume_group)
        vbox.addItem(QSpacerItem(100, 100))
        vbox.addWidget(self.button)
        self.setLayout(vbox)

        self.setWindowTitle('Example of Copy Volumes widget')
        self.setFixedSize(400, 125)
        self.show()

        # connect the widget to '.changed' event handler
        self.volume_group.changed.connect(self.volumes_changed)

    def volumes_changed(self, signal, noise):
        print('New signal=%d, noise=%d' % (signal, noise))

    def button_clicked(self):
        signal = random.randint(0, 100)
        noise = random.randint(0, 100)

        self.volume_group.setState(signal, noise)


app = QApplication(sys.argv)
ex = SpeedsExample()
sys.exit(app.exec())
