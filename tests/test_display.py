#!/usr/bin/env python3

"""
Test code for 'display' widget used by Morse Trainer.
"""

import sys
sys.path.append('..')
from display import Display
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton)


class DisplayExample(QWidget):
    """Application to demonstrate the Morse Trainer 'display' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        self.display = Display()
        button = QPushButton('Next', self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.display)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

        button.clicked.connect(self.buttonClicked)

        self.setGeometry(20, 100, 1000, 200)
        self.setWindowTitle('Example of Display widget')
        self.show()

        # populate the display widget a bit
        for index in range(30):
            if index in (7, 21):
                self.display.insert_upper('U', fg=Display.AnsTextBadColour)
            else:
                self.display.insert_upper('U', fg=Display.AskTextColour)

            if index in (5, 19):
                self.display.insert_lower('L', fg=Display.AnsTextBadColour)
            else:
                if index < 29:
                    self.display.insert_lower('L', fg=Display.AnsTextGoodColour)

            if index == 0:
                self.display.update_tooltip("Expected 'A', got 'N'\nweqweqwe")
            if index == 5:
                self.display.update_tooltip('Tooltip at index 5, '
                                            'rewyerewrewtrewtrewtrewtrewrtewi'
                                            'trewrewtrewtrewtrewtrewtrew')
            if index == 19:
                self.display.update_tooltip("Expected 'A', got 'N'\n"
                                            "weqweqwe\nasdasdadasd\na\na\na\na\na")


        self.display.set_highlight()


    def buttonClicked(self):
        """Clear display, reenter new test text.."""

        self.display.clear()

        for index in range(25):
            if index in (7, 21):
                self.display.insert_upper('1', fg=Display.AnsTextBadColour)
            else:
                self.display.insert_upper('1', fg=Display.AskTextColour)
            if index == 0:
                self.display.update_tooltip('Tooltip at index 0')
            if index == 5:
                self.display.update_tooltip('Tooltip at index 5')
            if index == 19:
                self.display.update_tooltip('Tooltip at index 19')

        for index in range(24):
            if index in (5, 19):
                self.display.insert_lower('8', fg=Display.AnsTextBadColour)
            else:
                self.display.insert_lower('8', fg=Display.AnsTextGoodColour)

        self.display.set_highlight()


app = QApplication(sys.argv)
ex = DisplayExample()
sys.exit(app.exec())
