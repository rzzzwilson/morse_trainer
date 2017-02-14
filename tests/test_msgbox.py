#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Test code for controlling QMessageBox format.
"""

import sys
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QMessageBox,
                             QSpinBox, QLineEdit, QPushButton,
                             QHBoxLayout, QVBoxLayout)


class TestMsgBox(QWidget):
    """Application to demonstrate the Morse Trainer 'grouping' widget."""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        lbl_font = QLabel('Font size', self)
        self.spb_fontsize = QSpinBox(self)
        self.spb_fontsize.setMinimum(1)
        self.spb_fontsize.setMaximum(20)
        lbl_msg = QLabel('Message', self)
        self.led_message = QLineEdit()
        btn_test = QPushButton('Test', self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(lbl_font)
        hbox1.addWidget(self.spb_fontsize)
        hbox1.addStretch()

        hbox2 = QHBoxLayout()
        hbox2.addWidget(lbl_msg)
        hbox2.addWidget(self.led_message)
        hbox2.addStretch()

        hbox3 = QHBoxLayout()
        hbox3.addStretch()
        hbox3.addWidget(btn_test)

        vbox = QVBoxLayout(self)
        self.setLayout(vbox)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.setGeometry(100, 100, 800, 300)
        self.setWindowTitle('Test of QMessageBox')
        self.show()

        btn_test.clicked.connect(self.test_msgbox)

    def test_msgbox(self):
        font_size = self.spb_fontsize.value()
        message = self.led_message.text()
        msg = ['<font size=%d>' % font_size,
               'font size=%d<br>' % font_size,
               message,
               '<br>',
               '</font>']
        msgbox = QMessageBox(self)
        msgbox.setText('Koch promotion')
        msgbox.setInformativeText(''.join(msg))
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.setDefaultButton(QMessageBox.Ok)
        msgbox.setMinimumWidth(800)
        msgbox.setMaximumWidth(800)
        msgbox.exec()
#        QMessageBox.information(self, 'Test', ''.join(msg), QMessageBox.Ok)

app = QApplication(sys.argv)
ex = TestMsgBox()
sys.exit(app.exec())
