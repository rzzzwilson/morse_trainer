#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Morse Trainer is an application to help a user learn to send and copy Morse.

Usage:  morse_trainer [-d <debug>]  [-h]

where  -d <debug>  sets the debug level to the number <debug> [0,50], output
                   is written to ./debug.log, smaller number means less debug
and    -h          prints this help and then stops.

You will need a morse key and Code Practice Oscillator (CPO).
"""

import sys
import json
import time
import getopt
import platform
import traceback
from random import randrange

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout, QWidget,
                             QTabWidget, QFormLayout, QLineEdit, QRadioButton,
                             QLabel, QCheckBox, QPushButton, QMessageBox,
                             QSpacerItem)

from display import Display
from copy_speeds import CopySpeeds
from send_speeds import SendSpeeds
from groups import Groups
from charset import Charset
from charset_proficiency import CharsetProficiency
from instructions import Instructions
from sound_morse import SoundMorse
from read_morse import ReadMorse
import utils
import logger


# get program name and version numbers
System = platform.system()
ProgName = sys.argv[0]
if ProgName.endswith('.py'):
    ProgName = ProgName[:-3]
    # remove any "_<platform>" suffix
    if ProgName.endswith('_' + System):
        parts = ProgName.split('_')
        ProgName = '_'.join(parts[:-1])

ProgramMajor = 0
ProgramMinor = 5
ProgramVersion = '%d.%d' % (ProgramMajor, ProgramMinor)

ProgramStateExtension = 'state'


class MorseTrainer(QTabWidget):
    """Class for the whole application."""

    # set platform-dependent sizes
    if System == 'Windows':
        MinimumWidth = 815
        MinimumHeight = 675
    elif System == 'Linux':
        MinimumWidth = 850
        MinimumHeight = 685
    elif System == 'Darwin':
        MinimumWidth = 815
        MinimumHeight = 675
    else:
        raise Exception('Unrecognized platform: %s' % System)

    # set the thresholds when we increase the Koch test charset
    KochSendThreshold = 0.95  # fraction
    KochSendCount = 20
    KochCopyThreshold = 0.95  # fraction
    KochCopyCount = 20

    # set the max number of results we keep for each character
    KochMaxHistory = 50

    # set default speeds
    DefaultWordsPerMinute = 15
    DefaultCharWordsPerMinute = 10

    # name of the 'read morse' parameters file
    MorseParamsFile = 'read_morse.param'

    # 'enum' constants for the three tabs
    (SendTab, CopyTab, StatsTab) = range(3)

    # dict to convert tab index to name
    TabEnum2Name = {SendTab: 'Send',
                    CopyTab: 'Copy',
                    StatsTab: 'Statistics'}

    # the default tab showing on startup
    DefaultStartTab = SendTab

    # name for the state save file
    StateSaveFile = '%s.%s' % (ProgName, ProgramStateExtension)

    # define names of the instance variables to be saved/restored
    StateVarNames = [
                     'program_version',

                     'current_tab_index',

                     'send_using_Koch', 'send_Koch_number', 'send_Koch_charset',
                     'send_User_chars_dict', 'send_wpm', 'send_group_index',
                     'send_stats',

                     'copy_using_Koch', 'copy_Koch_number', 'copy_Koch_charset',
                     'copy_User_chars_dict', 'copy_wpm', 'copy_cwpm',
                     'copy_group_index', 'copy_stats',
                    ]

    def __init__(self, parent = None):
        """Create a MorseTrainer object."""

        super().__init__(parent)

        # get the program version internal to the instance
        self.program_version = ProgramVersion

        # define internal state variables
        self.clear_data()

        # define the UI
        self.initUI()

        # get state from the save file, if any
        self.load_state(MorseTrainer.StateSaveFile)

        # update visible controls with possibly changed state values
        self.update_UI()

    def initUI(self):
        """Start constructing the UI."""

        self.send_tab = QWidget()
        self.copy_tab = QWidget()
        self.stats_tab = QWidget()

        self.addTab(self.send_tab, 'Send')
        self.addTab(self.copy_tab, 'Copy')
        self.addTab(self.stats_tab, 'Status')

        # initialize each tab
        self.initSendTab()
        self.initCopyTab()
        self.InitStatsTab()

        self.setMinimumSize(MorseTrainer.MinimumWidth,
                            MorseTrainer.MinimumHeight)
        self.setMaximumHeight(MorseTrainer.MinimumHeight)
        self.setWindowTitle('Morse Trainer %s' % ProgramVersion)

        # connect 'change tab' event to handler
        self.currentChanged.connect(self.tab_change)    # QTabWidget tab changed

######
# All code pertaining to the Send tab
######

    def initSendTab(self):
        """Layout the Send tab."""

        # define widgets on this tab
        self.send_display = Display()
        doc_text = ('Here we test your sending accuracy.  The program will '
                    'print the character you should send in the top row of the '
                    'display above.  Your job is to send that '
                    'character using your key and code practice oscillator.  '
                    'The program will print what it thinks you sent on the '
                    'lower line of the display.')
        instructions = Instructions(doc_text)
        self.send_speeds = SendSpeeds()
        self.send_groups = Groups()
        self.send_charset = Charset(utils.AllUserChars)
        self.btn_send_start_stop = QPushButton('Start')
        self.btn_send_clear = QPushButton('Clear')

        # start layout
        buttons = QVBoxLayout()
        buttons.maximumSize()
        buttons.addStretch()
        buttons.addWidget(self.btn_send_start_stop)
        buttons.addItem(QSpacerItem(20, 20))
        buttons.addWidget(self.btn_send_clear)

        controls = QVBoxLayout()
        controls.maximumSize()
        controls.addWidget(self.send_speeds)
        controls.addWidget(self.send_groups)
        controls.addWidget(self.send_charset)

        hbox = QHBoxLayout()
        hbox.maximumSize()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
        layout.maximumSize()
        layout.addWidget(self.send_display)
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        self.send_tab.setLayout(layout)

        # connect 'Send' events to handlers
        self.send_speeds.changed.connect(self.send_speeds_change)
        self.send_groups.changed.connect(self.send_group_change)
        self.send_charset.changed.connect(self.send_charset_change)
        self.btn_send_start_stop.clicked.connect(self.send_start)
        self.btn_send_clear.clicked.connect(self.send_clear)

    def send_speeds_change(self, use_speed, speed):
        """Something changed in the speeds widget."""

        self.send_use_speed = use_speed
        self.send_wpm = speed
        self.send_groups.setDisabled(not use_speed)

    def send_group_change(self, group_index):
        """Something changed in the Send grouping."""

        self.copy_group_index = index

    def send_charset_change(self, state):
        """Handle a change in the Send charset group widget."""

        (self.send_using_Koch,
         self.send_Koch_number,
         self.send_User_chars_dict) = state

        # update the Koch test set
        self.send_Koch_charset = utils.Koch[:self.send_Koch_number]

        # update the user test set
        on = [ch for ch in self.send_User_chars_dict
                  if self.send_User_chars_dict[ch]]
        self.send_User_sequence = ''.join(on)

        # if using the user charset
        if self.send_using_Koch:
            self.btn_send_start_stop.setDisabled(False)
        else:
            # if no user chars, disable "start" button
            self.btn_send_start_stop.setDisabled(not on)

        self.update_UI()

    def send_start(self):
        """The Send 'start/pause' button was clicked."""

        if self.processing:
            # enable the Clear button and speed/grouping/charset
            self.btn_send_clear.setDisabled(False)
            self.send_speeds.setDisabled(False)
            self.send_groups.setDisabled(False)
            self.send_charset.setDisabled(False)

            # Pause button label becomes Start
            self.btn_send_start_stop.setText('Start')

            # change state variables to reflect the stop
            self.processing = False
        else:
            # disable Clear button, speed/grouping/charset, relabel Start button
            self.btn_send_clear.setDisabled(True)
            self.send_speeds.setDisabled(True)
            self.send_groups.setDisabled(True)
            self.send_charset.setDisabled(True)
            self.btn_send_start_stop.setText('Pause')

            # start the 'Send' process
            self.send_expected = None
            self.processing = True
            if self.send_using_Koch:
                self.send_test_charset = self.send_Koch_charset
            else:
                self.send_test_charset = ''.join([ch for ch
                                                    in self.send_User_chars_dict
                                                    if self.send_User_chars_dict[ch]])

            self.send_thread_finished()

    def send_thread_finished(self, char=None, count=0):
        """Catch signal when Send thread finished.

        Compare the char we got (char) with expected (self.send_expected).
        If still processing, repeat thread.

        The 'count' param is a loop counter so we can do things like
        occassionally check is the Koch threshold has been exceeded
        and we can therefore increase the Koch test charset.
        """

        # echo received char, if any
        if char:
            if char in utils.AllUserChars:
                # update the character stats
                self.update_stats(self.send_stats,
                                  self.send_expected, char==self.send_expected)

                # show result in display
                if char == self.send_expected:
                    self.send_display.insert_lower(char)
                else:
                    self.send_display.insert_lower(char,
                                                   fg=Display.AnsTextBadColour)

                # put in a tooltip if char was wrong
                if char != self.send_expected:
                    colour = self.send_display.AnsTextBadColour
                    msg = ("Expected '%s' (%s),\nyou sent '%s' (%s)."
                            % (self.send_expected,
                               utils.char2morse(self.send_expected),
                               char, utils.char2morse(char)))
                    self.send_display.update_tooltip(msg)

                self.send_expected = None

        # update the user test set
        on = [ch for ch in self.send_User_chars_dict if self.send_User_chars_dict[ch]]
        self.send_User_sequence = ''.join(on)

        if self.processing:
            if self.send_expected is None:
                send_char = utils.get_random_char(self.send_test_charset)
                self.send_display.insert_upper(send_char)
                self.send_expected = send_char

            # update send count, maybe increase Koch charset
            count += 1
            if count >= self.KochSendCount:
                count = 0
                if self.all_send_chars_ok():
                    self.increase_send_Koch()

            self.threadSend = SendThread(self.send_morse_obj, count=count)
            self.threadSend.finished.connect(self.send_thread_finished)
            self.threadSend.start()

    def send_clear(self, event):
        """The Send 'clear' button was clicked."""

        self.send_display.clear()

    def all_send_chars_ok(self):
        """See if all Send Koch chars are over threshold.

        Return True if so.

        Note that we return False if *any* char is below the Koch count.
        """

        if self.send_using_Koch:
            # if we ARE using Koch for Send check all results for charset
            # note that we may have REDUCED the Koch charset, so active charset
            # may not contain chars for which we have results
            for char in self.send_Koch_charset:
                result_list = self.send_stats[char]
                num_samples = len(result_list)

                # all samples must be over Koch count threshold
                if num_samples < self.KochSendCount:
                    return False

                try:
                    fraction = result_list.count(True) / len(result_list)
                except ZeroDivisionError:
                    fraction = 0.0
                if fraction < self.KochSendThreshold:
                    return False

        return True

    def increase_send_Koch(self):
        """Increase the Koch send charset, if possible."""

        if self.send_using_Koch:
            # if we ARE using Koch for Send
            if self.send_Koch_number < len(utils.Koch):
                # we CAN increase the Send Koch charset
                self.send_Koch_number += 1
                self.send_Koch_charset = utils.Koch[:self.send_Koch_number]

                # let user know what is happening
                new_char = self.send_Koch_charset[-1]
                msg = ("<font size = 16>"
                       "Adding a new send character to the test set: '%s'\n\n"
                       "The morse code for this character is '%s'"
                       "</font>"
                       % (new_char,
                          utils.morse2display(utils.Char2Morse[new_char])))
                QMessageBox.information(self, 'Send promotion',
                                        msg, QMessageBox.Yes)

                # force a "pause"
                self.send_start()

                # update the Send UI
                self.update_UI()

######
# All code pertaining to the Copy tab
#####

    def initCopyTab(self):
        """Layout the Copy tab."""

        # define widgets on this tab
        self.copy_display = Display()
        doc_text = ('Here we test your copying accuracy.  The program '
                    'will sound a random morse character which you should type '
                    'on the keyboard.  The character you typed will appear in '
                    'the bottom row of the display above '
                    'along with the character the program actually sent in '
                    'the top row.')
        instructions = Instructions(doc_text)
        self.copy_speeds = CopySpeeds()
        self.copy_groups = Groups()
        self.copy_charset = Charset(utils.AllUserChars)
        self.btn_copy_start_stop = QPushButton('Start')
        self.btn_copy_clear = QPushButton('Clear')

        # start layout
        buttons = QVBoxLayout()
        buttons.maximumSize()
        buttons.addStretch()
        buttons.addWidget(self.btn_copy_start_stop)
        buttons.addItem(QSpacerItem(20, 20))
        buttons.addWidget(self.btn_copy_clear)

        controls = QVBoxLayout()
        controls.maximumSize()
        controls.addWidget(self.copy_speeds)
        controls.addWidget(self.copy_groups)
        controls.addWidget(self.copy_charset)

        hbox = QHBoxLayout()
        hbox.maximumSize()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
        layout.maximumSize()
        layout.addWidget(self.copy_display)
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        self.copy_tab.setLayout(layout)

        # connect 'Copy' events to handlers
        self.copy_speeds.changed.connect(self.copy_speeds_changed)
        self.copy_groups.changed.connect(self.copy_group_change)
        self.copy_charset.changed.connect(self.copy_charset_change)
        self.btn_copy_start_stop.clicked.connect(self.copy_start)
        self.btn_copy_clear.clicked.connect(self.copy_clear)

    def copy_start(self, event=None):
        """The Copy 'start/pause' button was clicked."""

        if self.processing:
            # enable the Clear button and speed/grouping/charset
            self.btn_copy_clear.setDisabled(False)
            self.copy_speeds.setDisabled(False)
            self.copy_groups.setDisabled(False)
            self.copy_charset.setDisabled(False)

            # Pause button label becomes Start
            self.btn_copy_start_stop.setText('Start')

            # change state variables to reflect the stop
            self.processing = False
        else:
            # disable the Clear button and speed/grouping/charset, relabel Start button
            self.btn_copy_clear.setDisabled(True)
            self.copy_speeds.setDisabled(True)
            self.copy_groups.setDisabled(True)
            self.copy_charset.setDisabled(True)
            self.btn_copy_start_stop.setText('Pause')

            # start the 'Send' process
            self.copy_pending = []
            self.processing = True

            self.copy_thread_finished()

    def copy_thread_finished(self, count=0):
        """Catch signal when Send thread finished.

        If still processing, start new thread.
        """

        if self.processing:
            # update copy count, maybe increase Koch charset
            count += 1
            if count >= self.KochCopyCount:
                count = 0
                if self.all_copy_chars_ok():
                    self.increase_copy_Koch()

            send_char = utils.get_random_char(self.copy_Koch_charset)
            self.copy_pending = (self.copy_pending + [send_char])[-2:]
            self.threadCopy = CopyThread(send_char, self.copy_morse_obj, count)
            self.threadCopy.finished.connect(self.copy_thread_finished)
            self.threadCopy.start()

    def copy_clear(self, event):
        """The Copy 'clear' button was clicked."""

        self.copy_display.clear()

    def all_copy_chars_ok(self):
        """See if all Koch chars are over threshold.

        Return True if so.
        """

        if self.copy_using_Koch:
            # if we ARE using Koch for Copy check all results for charset
            # note that we may have REDUCED the Koch charset, so active charset
            # may not contain chars for which we have results
            for char in self.copy_Koch_charset:
                result_list = self.copy_stats[char]
                num_samples = len(result_list)

                # all samples must be over count threshold
                if num_samples < self.KochCopyCount:
                    return False

                try:
                    fraction = result_list.count(True) / num_samples
                except ZeroDivisionError:
                    fraction = 0.0
                if fraction < self.KochCopyThreshold:
                    return False

        return True

    def increase_copy_Koch(self):
        """Increase the Koch copy charset, if possible."""

        if self.copy_using_Koch:
            # if we ARE using Koch for Copy
            if self.copy_Koch_number < len(utils.Koch):
                # we CAN increase the Copy Koch charset
                self.copy_Koch_number += 1
                self.copy_Koch_charset = utils.Koch[:self.copy_Koch_number]

                # let user know what is happening
                new_char = self.copy_Koch_charset[-1]
                msg = ("<font size = 16>"
                       "Adding a new copy character to the test set: '%s'.\n\n"
                       "The morse code for this character is '%s'."
                       "</font>"
                       % (new_char,
                          utils.morse2display(utils.Char2Morse[new_char])))
                QMessageBox.information(self, 'Copy promotion',
                                        msg, QMessageBox.Yes)

                # force a pause
                self.copy_start()

                # update the Send UI
                self.update_UI()

    def copy_speeds_changed(self, cwpm, wpm):
        """Something in the "copy speed" group changed.

        cwpm  new char speed
        wpm   new word speed
        """

        self.copy_cwpm = cwpm
        self.copy_wpm = wpm
        self.copy_morse_obj.set_speeds(cwpm, wpm)

    def copy_group_change(self, index):
        """Copy grouping changed."""

        self.copy_group_index = index

    def copy_charset_change(self, state):
        """Handle a change in the Copy charset group widget."""

        (self.copy_using_Koch,
         self.copy_Koch_number,
         self.copy_User_chars_dict) = state

        # update the Koch test set
        self.copy_Koch_charset = utils.Koch[:self.copy_Koch_number]

        # update the user test set
        on = [ch for ch in self.copy_User_chars_dict
                  if self.copy_User_chars_dict[ch]]
        self.copy_User_sequence = ''.join(on)

        # if using the user charset
        if self.copy_using_Koch:
            self.btn_copy_start_stop.setDisabled(False)
        else:
            # if no user chars, disable "start" button
            self.btn_copy_start_stop.setDisabled(not on)

        self.update_UI()

######
# All code pertaining to the Stats tab
######

    def InitStatsTab(self):
        """Layout the Stats tab."""

        # create all tab widgets
        doc_text = ('This shows your sending and receiving proficiency. '
                    'Each bar shows your proficiency for a character.  The '
                    'taller the bar the better.  You need to practice the '
                    'characters with shorter bars.\n\n'
                    'The red line shows the Koch threshold.  In Koch mode '
                    'if all characters in the test set are over the threshold '
                    'the algorithm will add another character to the set you '
                    'are tested with.\n\n'
                    'The colour of the bar indicates how many times that '
                    'character has been tested relative to a threshold '
                    'count.  The bar is green if the sample is valid, blue if '
                    'it close to valid and red if it is far from valid.\n\n'
                    'Pressing the "Clear" button will clear the statistics. '
                    'This is useful when changing test speeds.')
        instructions = Instructions(doc_text)
        self.send_status = CharsetProficiency('Send Proficiency',
                                              utils.Alphabetics,
                                              utils.Numbers,
                                              utils.Punctuation,
                                              self.KochSendThreshold)
        percents = self.stats2percent(self.send_stats, self.KochSendCount)
        self.send_status.setState(percents)
        self.copy_status = CharsetProficiency('Copy Proficiency',
                                              utils.Alphabetics,
                                              utils.Numbers,
                                              utils.Punctuation,
                                              self.KochCopyThreshold)
        percents = self.stats2percent(self.copy_stats, self.KochCopyCount)
        self.copy_status.setState(percents)
        self.stats_btn_clear = QPushButton('Clear')

        # lay out the tab
        buttons = QVBoxLayout()
        buttons.maximumSize()
        buttons.addStretch()
        buttons.addWidget(self.stats_btn_clear)

        controls = QVBoxLayout()
        controls.maximumSize()
        controls.addWidget(self.send_status)
        controls.addWidget(self.copy_status)

        hbox = QHBoxLayout()
        hbox.maximumSize()
        hbox.addLayout(controls)
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
        layout.maximumSize()
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        self.stats_tab.setLayout(layout)

        # connect 'Stats' events to handlers
        self.stats_btn_clear.clicked.connect(self.clear_stats)

    def clear_stats(self):
        """Clear the statistics display."""

        # "Are you sure?" dialog here
        msg = "Are you sure you want to clear all statistics?"
        reply = QMessageBox.question(self, 'Clear Statistics?', msg,
                                     QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # clear the internal data structure
        for ch in utils.AllUserChars:
            self.send_stats[ch] = []
            self.copy_stats[ch] = []

        new = self.stats2percent(self.send_stats, self.KochSendCount)
        self.send_status.setState(new)

        new = self.stats2percent(self.copy_stats, self.KochCopyCount)
        self.copy_status.setState(new)

        self.stats_btn_clear.setDisabled(True)

######
# Other code
######

    def keyPressEvent(self, e):
        """When self.processing is True we handle keypresses.

        This should only be true during Copy processing.
        """

        # ignore anything we aren't interested in
        key_int = e.key()
        if not 32 < key_int < 128:
            return
        char = chr(key_int)
        if char not in utils.AllUserChars:
            return

        if self.processing:
            if self.copy_pending:
                # if we are copying, handle char
                pending = self.copy_pending.pop(0)

                # need some logic here to handle case when user gets behind
                # if key doesn't match oldest but newest, assume newest
                if char != pending:
                    if self.copy_pending and char == self.copy_pending[0]:
                        pending = self.copy_pending.pop(0)

                self.copy_display.insert_upper(pending, self.send_display.AskTextColour)

                colour = self.send_display.AnsTextGoodColour
                if pending != char:
                    colour = self.send_display.AnsTextBadColour
                    msg = ("Sounded '%s' (%s),\nyou entered '%s' (%s)."
                            % (pending, utils.char2morse(pending),
                               char, utils.char2morse(char)))
                    self.copy_display.update_tooltip(msg)
                self.copy_display.insert_lower(char, colour)

                # update the character stats
                self.update_stats(self.copy_stats, pending, pending==char)
#            elif self.send_pending:
#                # if we are sending, handle here
#                pass

    def update_stats(self, stats, char, result):
        """Update a stats dictionary.

        stats   the stats dictionary to update
        char    the character being tested
        result  True or False
        """

        stats[char].append(result)
        stats[char] = stats[char][:self.KochMaxHistory]

    def update_UI(self):
        """Update controls that show state values."""

        # the send speeds
        self.send_speeds.setState(self.send_using_Koch, self.send_wpm)

        # the send test sets (Koch and user-selected)
        self.send_charset.setState(self.send_using_Koch,
                                   self.send_Koch_number,
                                   self.send_User_chars_dict)

        # the copy speeds
        self.copy_speeds.setState(self.copy_wpm)

        # the copy test sets (Koch and user-selected)
        self.copy_charset.setState(self.copy_using_Koch,
                                   self.copy_Koch_number,
                                   self.copy_User_chars_dict)

    def closeEvent(self, *args, **kwargs):
        """Program close - save the internal state."""

        super().closeEvent(*args, **kwargs)
        self.save_state(MorseTrainer.StateSaveFile)

    def clear_data(self):
        """Define and clear all internal variables."""

        # the morse objects
        self.send_morse_obj = ReadMorse()
        self.send_morse_obj.load_params(MorseTrainer.MorseParamsFile)
        self.copy_morse_obj = SoundMorse()

        # Send variables
        self.send_using_Koch = True
        self.send_Koch_number = 2
        self.send_Koch_charset = utils.Koch[:self.send_Koch_number]
        self.send_User_chars_dict = {ch:False for ch in utils.AllUserChars}
        self.send_use_speed = False
        self.send_wpm = 5
        # self.send_cwpm not used for Send
        self.send_group_index = 0
        self.send_expected = None
        self.send_test_charset = None

        # Copy variables
        self.copy_using_Koch = True
        self.copy_Koch_number = 2
        self.copy_Koch_charset = utils.Koch[:self.copy_Koch_number]
        self.copy_User_chars_dict = {ch:False for ch in utils.AllUserChars}
        self.copy_wpm = 5
        self.copy_cwpm = 5
        self.copy_group_index = 0
        self.copy_pending = ''              # holds last 2 chars sounded

        # the send/copy statistics
        # each 'char':value is a list of last N results, True or False
        self.send_stats = {ch:[] for ch in utils.AllUserChars}
        self.copy_stats = {ch:[] for ch in utils.AllUserChars}

        # state variable shows send or copy test in progress
        self.processing = False

        # set the current and previous tab indices
        self.current_tab_index = MorseTrainer.DefaultStartTab
        self.previous_tab_index = None

    def load_state(self, filename):
        """Load saved state from the given file."""

        # read JSON from file, if we can
        if filename is None:
            log.info('load_state: no state file configured to recover from')
            return

        try:
            with open(filename, 'r') as fd:
                data = json.load(fd)
        except FileNotFoundError:
            log.info("load_state: state file '%s' not found" % filename)
            return

        # check version of loaded data, modify load data if necessary
        loaded_version = data['program_version']
        log.info("load_state: loaded version='%s', this program is '%s'"
                 % (loaded_version, ProgramVersion))

        # get data from the restore dictionary, if possible
        for var_name in MorseTrainer.StateVarNames:
            try:
                value = data[var_name]
            except KeyError:
                pass
            else:
                log.debug('load_state: setting var %s to %s'
                          % (var_name, str(value)))
                setattr(self, var_name, value)

        #####
        # now update UI state from state variables
        #####

        # Send panel
        self.send_speeds.setState(self.send_using_Koch, self.send_wpm)
        self.send_groups.setState(self.send_group_index)
        self.send_charset.setState(self.send_using_Koch,
                                   self.send_Koch_number,
                                   self.send_User_chars_dict)
        self.send_charset_change((self.send_using_Koch,
                                  self.send_Koch_number,
                                  self.send_User_chars_dict))
#        self.send_morse_obj.set_speeds(self.send_wpm)

        # Copy panel
        self.copy_speeds.setState(self.copy_wpm, cwpm=self.copy_cwpm)
        self.copy_groups.setState(self.copy_group_index)
        self.copy_charset.setState(self.copy_using_Koch,
                                   self.copy_Koch_number,
                                   self.copy_User_chars_dict)
        self.copy_charset_change((self.copy_using_Koch,
                                  self.copy_Koch_number,
                                  self.copy_User_chars_dict))
        self.copy_morse_obj.set_speeds(self.copy_wpm, self.copy_cwpm)

        # adjust tabbed view to last view
        self.set_app_tab(self.current_tab_index)

        self.update()

    def save_state(self, filename):
        """Save saved state to the given file."""

        # write data to the save file, if any
        if filename is None:
            return

        # create a dictionary filled with save data
        save_data = {}
        for var_name in MorseTrainer.StateVarNames:
            save_data[var_name] = getattr(self, var_name)

        json_str = json.dumps(save_data, sort_keys=True, indent=4)

        with open(filename, 'w') as fd:
            fd.write(json_str + '\n')

    def stats2percent(self, stats, threshold):
        """Convert stats data into a fraction dictionary.

        stats      dictionary holding statistics data
        threshold  the number of samples before Koch promotion

        The 'stats' data has the form {'A':[T,F,T], ...} where
        the list contains the last N results (True or False).

        The resultant fraction dictionary has the form:
            {'A': (fraction, sample_size, threshold), ...}

        We pass 'threshold' through despite the redundancy since the
        widget module knows nothing of the Koch count threshold.
        """

        results = {}

        for (char, result_list) in stats.items():
            if not result_list:
                fraction = 0.0
                sample_size = 0
            else:
                sample_size = len(result_list)
                try:
                    fraction = result_list.count(True) / sample_size
                except ZeroDivisionError:
                    fraction = 0.0
            results[char] = (fraction, sample_size, threshold)

        return results

    def tab_change(self, tab_index):
        """Handler when a tab is changed.

        tab_index  index of the new tab
        """

        self.current_tab_index = tab_index
        old_tab = MorseTrainer.TabEnum2Name.get(self.previous_tab_index, str(None))

        # if we left the "send" tab, turn off action, if any
        if self.previous_tab_index == MorseTrainer.SendTab:
            pass

        # if we left the "copy" tab, turn off action, if any
        if self.previous_tab_index == MorseTrainer.CopyTab:
            self.processing = True
            self.copy_start()       # to set UI state to "not processing"

        # if we changed to the "statistics" tab, refresh the stats widget
        if tab_index == MorseTrainer.StatsTab:
            percents = self.stats2percent(self.send_stats, self.KochSendCount)
            self.send_status.setState(percents)

            percents = self.stats2percent(self.copy_stats, self.KochCopyCount)
            self.copy_status.setState(percents)

            # if nothing to clear, disable 'Clear' button
            # see if statistics are already empty
            send_sum = sum([len(v) for v in self.send_stats.values()])
            copy_sum = sum([len(v) for v in self.copy_stats.values()])
            stats_sum = send_sum + copy_sum
            self.stats_btn_clear.setDisabled(stats_sum == 0)

        # remember the previous tab for NEXT TIME WE CHANGE
        self.previous_tab_index = tab_index

    def set_app_tab(self, tab_index):
        """Make app show the required tab index sheet."""

        self.setCurrentIndex(tab_index)

######
# A thread to read one morse character from the microphone.
######

class SendThread(QThread):
    """A thread to read a morse character from the microphone.

    It sends a signal to the main thread when finished.  The signal
    contains the character read (or None if nothing read).
    """

    # the signal when finished
    finished = pyqtSignal(str, int)

    def __init__(self, sound_object, count):
        """Create a thread to read one morse character.

        sound_object  the object that reads morse sounds
        count         times we've run the thread, returned in 'finished' event
        """

        QThread.__init__(self)
        self.sound_object = sound_object
        self.count = count

#    def __del__(self):
#        """Delete the thread."""
#
#        self.wait()

    def run(self):
        """Sound the character."""

        # make the character sound in morse
        char = self.sound_object.read()

        # send signal to main thread: finished
        self.finished.emit(char, self.count)

######
# A thread to sound one morse character.
######

class CopyThread(QThread):
    """A thread to sound a morse character to the speakers.

    It sends a signal to the main thread when finished.
    """

    # the signal when finished
    finished = pyqtSignal(int)

    def __init__(self, char, sound_object, count):
        """Create a thread to sound one morse character.

        char          the character to sound
        sound_object  the object that makes morse sounds
        count         number of times the thread has run
        """

        QThread.__init__(self)
        self.char = char
        self.sound_object = sound_object
        self.count = count

#    def __del__(self):
#        """Delete the thread."""
#
#        self.wait()

    def run(self):
        """Sound the character."""

        # make the character sound in morse
        self.sound_object.send(self.char)

        # send signal to main thread: finished
        self.finished.emit(self.count)


if __name__ == '__main__':
    import sys

    # small 'usage' function
    def usage(msg=None):
        if msg:
            print(('*'*80 + '\n%s\n' + '*'*80) % msg)
        print(__doc__)

    # our own handler for uncaught exceptions
    def excepthook(type, value, tb):
        msg = '\n' + '=' * 80
        msg += '\nUncaught exception:\n'
        msg += ''.join(traceback.format_exception(type, value, tb))
        msg += '=' * 80 + '\n'
        log.critical(msg)
        print(msg)

    # plug our handler into the python system
    sys.excepthook = excepthook

    # start the logging
    log = logger.Log('debug.log', logger.Log.CRITICAL)

    # announce the start
    morse_version = utils.str2morse('morse trainer %s' % ProgramVersion)
    morse_width = len(morse_version)
    morse_signon = 'Morse Trainer %s' % ProgramVersion
    log(morse_version)
    log(morse_signon.center(morse_width))
    log('VK4FAWR/M'.center(morse_width))
    log(morse_version)

    # parse command line options
    argv = sys.argv[1:]

    try:
        (opts, args) = getopt.getopt(argv, 'd:h', ['debug=', 'help'])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)

    for (opt, param) in opts:
        if opt in ['-d', '--debug']:
            try:
                debug = int(param)
                log.set_level(debug)
            except ValueError:
                usage("-d must be followed by an integer, got '%s'" % param)
                sys.exit(1)
        elif opt in ['-h', '--help']:
            usage()
            sys.exit(0)

    # launch the app
    app = QApplication(sys.argv)
    ex = MorseTrainer()
    ex.show()
    sys.exit(app.exec())
