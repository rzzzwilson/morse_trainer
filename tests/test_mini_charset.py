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
        self.toggle = True
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
        if self.toggle:
            # generate random data
            in_use = randint(2, len(utils.Koch))
            new = {}
            for char in utils.Koch:
                new[char] = (randint(0,100)/100, randint(0,51))
        else:
            # set a fixed state
            in_use = 15
            new = {}
            for (n, char) in enumerate(utils.Koch):
                if n == 0:
                    new[char] = (0.98, 50)
                elif n == 1:
                    new[char] = (0.98, 40)
                elif n == 2:
                    new[char] = (0.88, 40)
                elif n == 3:
                    new[char] = (0.88, 50)
                else:
                    new[char] = (randint(0,100)/100, randint(0,51))

        # redisplay
        self.display.setState(in_use, new, 0.95, 50)

        self.toggle = not self.toggle



app = QApplication(sys.argv)
ex = TestMiniCharset()
sys.exit(app.exec())
