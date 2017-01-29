#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Test the 'mini charset' custom widget used by Morse Trainer.
"""

import sys
from random import randint
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton)
sys.path.append('..')
from mini_charset import MiniCharset
import utils


class TestMiniCharset(QWidget):
    """Application to demonstrate the Morse Trainer 'charset' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        self.display = MiniCharset(utils.Koch, 2)
        redisplay_button = QPushButton('Redisplay', self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.display)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(redisplay_button)
        self.setLayout(vbox)

        redisplay_button.clicked.connect(self.redisplayButtonClicked)

        self.setGeometry(100, 100, 500, 100)
        self.setWindowTitle('Example of MiniCharset widget')
        self.show()

    def redisplayButtonClicked(self, event):

        in_use = randint(2, len(utils.Koch))

        # generate random data
        new = {}
        for char in utils.Koch:
            new[char] = (randint(0,100)/100, randint(0,51))
        # redisplay
        self.display.setState(in_use, new, 0.95, 50)



app = QApplication(sys.argv)
ex = TestMiniCharset()
sys.exit(app.exec())
