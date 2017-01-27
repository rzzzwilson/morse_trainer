#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Test the 'mini-proficiency' widget.
"""

import sys
sys.path.append('..')
from random import random, randint
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout)
from mini_proficiency import MiniProficiency
import utils


class MiniProficiencyExample(QWidget):
    """Demonstrate the Morse Trainer 'mini-proficiency' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        self.mini_proficiency = MiniProficiency(utils.Koch)
        redisplay_button = QPushButton('Redisplay', self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.mini_proficiency)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(redisplay_button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

        redisplay_button.clicked.connect(self.redisplayButtonClicked)

        self.setGeometry(100, 100, 500, 100)
        self.setWindowTitle('Example of MiniProficiency widget')
        self.show()
        self.redisplayButtonClicked()

    def redisplayButtonClicked(self):
        """Regenerate some data (random) and display it."""

        in_use = randint(2, len(utils.Koch))

        # generate random data
        new = {}
        for char in self.mini_proficiency.data:
            new[char] = (randint(0,100)/100, randint(0,51))
        # redisplay
        self.mini_proficiency.setState(in_use, new, 0.95, 50)


app = QApplication(sys.argv)
ex = MiniProficiencyExample()
sys.exit(app.exec())
