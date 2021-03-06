"""
Morse Trainer is an application to help a user learn to send and copy Morse.

Usage:  morse_trainer [-d <debug>]  [-h]

where  -d <debug>  sets the debug level to the number <debug> [0,50], output
                   is written to ./debug.log, smaller number means more debug
and    -h          prints this help and then stops.

You will need a morse key and Code Practice Oscillator (CPO).
"""

import os
import sys
import json
import time
import random
import getopt
import platform
import faulthandler
import traceback
from queue import Queue
from random import randrange

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout, QWidget,
                             QTabWidget, QPushButton, QMessageBox, QSpacerItem)
from PyQt5.QtGui import QIcon

from display import Display
from copy_speeds import CopySpeeds
from send_speeds import SendSpeeds
from mini_charset import MiniCharset
from instructions import Instructions
from sound_morse import SoundMorse
from read_morse import ReadMorse
from copy_volumes import CopyVolumes
import utils
import logger


# get program name and version numbers
System = platform.system()
ProgName = os.path.basename(sys.argv[0])
if ProgName.endswith('.py'):
    ProgName = ProgName[:-3]
# remove any "_<platform>" suffix
if ProgName.endswith('_' + System):
    parts = ProgName.split('_')
    ProgName = '_'.join(parts[:-1])

ProgramMajor = 1
ProgramMinor = 0
ProgramVersion = '%d.%d' % (ProgramMajor, ProgramMinor)

# extension for program state file
ProgramStateExtension = 'state'

# where we dump faulthandler module output
FaultHandlerFile = './faulthandler.log'


class MorseTrainer(QTabWidget):
    """Class for the whole application."""

    # set platform-dependent sizes
    if System == 'Windows':
        MinimumWidth = 910
        MinimumHeight = 540
        ButtonWidth = 80
    elif System == 'Linux':
        MinimumWidth = 910
        MinimumHeight = 540
        ButtonWidth = 80
    elif System == 'Darwin':
        MinimumWidth = 910
        MinimumHeight = 540
        ButtonWidth = 80
    else:
        raise Exception('Unrecognized platform: %s' % System)

    MsgBoxFontSize = 4

    # set the thresholds when we increase the Koch test charset
    KochSendThreshold = 0.90  # fraction
    KochSendCount = 50
    KochCopyThreshold = 0.90  # fraction
    KochCopyCount = 50

    # set the max number of results we keep for each character
    KochMaxHistory = 50

    # set default speeds
    DefaultWordsPerMinute = 15
    DefaultCharWordsPerMinute = 10

    # set speed step (must be same as 'StepSpeed' in *_speeds.py)
    StepSpeed = 5

    # name of the 'read morse' parameters file
    MorseParamsFile = 'read_morse.param'

    # 'enum' constants for the two tabs
    (SendTab, CopyTab) = range(2)

    # dict to convert tab index to name
    TabEnum2Name = {SendTab: 'Send',
                    CopyTab: 'Copy'}

    # the default tab showing on startup
    DefaultStartTab = SendTab

    # name for the state save file
    StateSaveFile = '%s.%s' % (ProgName, ProgramStateExtension)

    # define names of the instance variables to be saved/restored
    StateVarNames = [
                     'program_version',

                     'current_tab_index',

                     'send_Koch_number', 'send_Koch_charset',
                     'send_wpm',
                     'send_stats',

                     'copy_Koch_number', 'copy_Koch_charset',
                     'copy_wpm', 'copy_cwpm',
                     'copy_freq', 'copy_signal', 'copy_noise',
                     'copy_stats',
                    ]

    # error symbol, if needed
    ErrorSymbol = '◇'

    # default signal and noise percentages
    DefaultSignalPercent = 55
    DefaultNoisePercent = 0

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

        self.addTab(self.send_tab, 'Send')
        self.addTab(self.copy_tab, 'Copy')

        # initialize each tab
        self.initSendTab()
        self.initCopyTab()

        self.setMinimumSize(MorseTrainer.MinimumWidth,
                            MorseTrainer.MinimumHeight)
        self.setMaximumHeight(MorseTrainer.MinimumHeight)
        self.setWindowTitle('Morse Trainer %s' % ProgramVersion)
        self.setWindowIcon(QIcon('icon.png'))

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
                    'display.  Your job is to send that character using your '
                    'key and code practice oscillator.  The program will print '
                    'what it thinks you sent on the lower line of the display.  '
                    'Errors are marked in red and you can left click on an '
                    'error to see what went wrong.')
        instructions = Instructions(doc_text)
        instructions.minimumSize()
        self.send_speeds = SendSpeeds()
        self.send_charset = MiniCharset(utils.Koch)
        self.btn_send_start_stop = QPushButton('Start', self)
        self.btn_send_start_stop.setMinimumWidth(MorseTrainer.ButtonWidth)
        self.btn_send_clear = QPushButton('Clear', self)
        self.btn_send_clear.setMinimumWidth(MorseTrainer.ButtonWidth)

        # start layout
        buttons = QVBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.btn_send_start_stop)
        buttons.addItem(QSpacerItem(10, 10))
        buttons.addWidget(self.btn_send_clear)
        buttons.maximumSize()

        controls = QVBoxLayout()
        controls.addWidget(self.send_speeds)
        controls.addWidget(self.send_charset)
        controls.maximumSize()

        hbox = QHBoxLayout()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)
        hbox.maximumSize()

        layout = QVBoxLayout()
        layout.addWidget(self.send_display)
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        layout.maximumSize()
        self.send_tab.setLayout(layout)

        # connect 'Send' events to handlers
        self.send_speeds.changed.connect(self.send_speeds_change)
        self.btn_send_start_stop.clicked.connect(self.send_start)
        self.btn_send_clear.clicked.connect(self.send_clear)

    def send_speeds_change(self, speed):
        """Something changed in the speeds widget."""

        # update internal state
        self.send_wpm = speed

        # modify receive params to be the approximate desired speed
        dot_time = utils.wpm2params(speed)
        self.send_morse_obj.len_dot = dot_time
        self.send_morse_obj.len_dash = 3 * dot_time
        self.send_morse_obj.dot_dash_threshold = 2 * dot_time

    def send_start(self):
        """The Send 'start/pause' button was clicked."""

        if self.processing:
            # stop Send thread
            if self.threadSend:
                self.threadSend.terminate()
                self.threadSend.wait()
                self.threadSend = None

            # enable the Clear button and speed/grouping/charset
            self.btn_send_clear.setDisabled(False)
            self.send_speeds.setDisabled(False)
            self.btn_send_start_stop.setText('Start')

            # destroy the result queue
            self.resultq = None

            # change state variables to reflect the stop
            self.send_expected = None
            self.processing = False
        else:
            # start processing, create a thread with next random char, etc
            # disable Clear button, speed/grouping/charset, relabel Start button
            self.btn_send_clear.setDisabled(True)
            self.send_speeds.setDisabled(True)
            self.btn_send_start_stop.setText('Pause')

            # get a new result queue
            self.resultq = Queue()

            # start the 'Send' process
            self.send_expected = None
            self.processing = True

            # start new thread, send_thread_finished() called when finished
            self.send_thread_finished(None)

    @pyqtSlot(tuple)
    def send_thread_finished(self, result):
        """Catch signal when Send thread finished.

        result  a tuple (char, morse)

        Compare the char we got with expected (self.send_expected).
        If still processing, repeat thread.

        The 'self.process_count' value is a loop counter so we can do
        things like occasionally check if the Koch threshold has been
        exceeded and we can therefore increase the Koch test charset.
        """

        # indicate that the thread isn't running
        if self.threadSend:
            self.threadSend.send_done.disconnect()
            self.threadSend.wait()
        self.threadSend = None

        if result is None:
            char = None
            morse = None
        else:
            (char, morse) = result
            if char is None:
                char = MorseTrainer.ErrorSymbol

        # if we get a space, pretend it's None
        if char == ' ':
            char = None

        if char:
            # update the character stats
            self.update_stats(self.send_stats,
                              self.send_expected,
                              char==self.send_expected)

            # show result in display
            char_colour = Display.AnsTextGoodColour
            if char != self.send_expected:
                char_colour = Display.AnsTextBadColour
            self.send_display.insert_lower(char, fg=char_colour)

            # update statistics and mini_charset
            new = self.stats2percent(self.send_stats,
                                     MorseTrainer.KochSendThreshold)
            self.send_charset.setState(self.send_Koch_number, new,
                                       MorseTrainer.KochSendThreshold,
                                       MorseTrainer.KochSendCount)

            # add error tooltip if char not as expected
            if char != self.send_expected:
                msg = ("Expected '%s' (%s),\nyou sent '%s' (%s)."
                        % (self.send_expected,
                           utils.char2morse(self.send_expected),
                           char, utils.morse2display(morse)))
                self.send_display.update_tooltip(msg)

            # signal that we can wait for another character
            self.send_expected = None

            # update send count, maybe increase Koch charset
            self.process_count += 1
            if self.process_count >= self.KochSendCount:
                self.process_count = 0
                if self.all_send_chars_ok():
                    self.increase_send_Koch()

        # if we are still processing and not expecting char, prepare for next char
        if self.processing:
            if self.send_expected is None:
                send_char = utils.get_random_char(self.send_Koch_charset,
                                                  self.send_stats,
                                                  self.KochSendCount,
                                                  self.KochSendThreshold)
                self.send_display.insert_upper(send_char)
                self.send_expected = send_char
                self.send_display.set_highlight()

            self.threadSend = SendThread(self.send_morse_obj)
            self.threadSend.send_done.connect(self.send_thread_finished)
            self.threadSend.start()

        # update apparent wpm display
        len_dot = self.send_morse_obj.len_dot
        apparent_wpm = utils.params2wpm(len_dot)
        self.send_speeds.setApparentSpeed(apparent_wpm)

    def send_clear(self, event):
        """The Send 'clear' button was clicked."""

        self.send_display.clear()

    def all_send_chars_ok(self):
        """See if all Send Koch chars are over threshold.

        Return True if so.

        Note that we return False if *any* char is below the Koch count.
        """

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

        if self.send_Koch_number < len(utils.Koch):
            # we CAN increase the Send Koch charset
            self.send_Koch_number += 1
            self.send_Koch_charset = utils.Koch[:self.send_Koch_number]

            # let user know what is happening
            new_char = self.send_Koch_charset[-1]

            msg = ("<font size=%d>"
                   "Adding a new character to the test set: '%s'.<br>"
                   "The morse code for this character is '%s'."
                   "</font>"
                   % (MorseTrainer.MsgBoxFontSize, new_char,
                      utils.morse2display(utils.Char2Morse[new_char])))

            msgbox = QMessageBox(self)
            msgbox.setText('Koch promotion')
            msgbox.setInformativeText(msg)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.setDefaultButton(QMessageBox.Ok)
            msgbox.exec()

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
                    'the bottom row of the display along with the character '
                    'the program actually sent in the top row.  '
                    'Errors are marked in red and you can left click on an '
                    'error to see what went wrong.')
        instructions = Instructions(doc_text)
        instructions.minimumSize()
        self.copy_speeds = CopySpeeds()
        self.copy_volumes = CopyVolumes()
        self.copy_charset = MiniCharset(utils.Koch)
        self.btn_copy_start_stop = QPushButton('Start')
        self.btn_copy_start_stop.setMinimumWidth(MorseTrainer.ButtonWidth)
        self.btn_copy_clear = QPushButton('Clear')
        self.btn_copy_clear.setMinimumWidth(MorseTrainer.ButtonWidth)

        # start layout
        buttons = QVBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.btn_copy_start_stop)
        buttons.addItem(QSpacerItem(10, 10))
        buttons.addWidget(self.btn_copy_clear)
        buttons.maximumSize()

        controls = QVBoxLayout()
        controls.addWidget(self.copy_speeds)
        controls.addWidget(self.copy_volumes)
        controls.addWidget(self.copy_charset)
        controls.maximumSize()

        hbox = QHBoxLayout()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)
        hbox.maximumSize()

        layout = QVBoxLayout()
        layout.addWidget(self.copy_display)
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        layout.maximumSize()
        self.copy_tab.setLayout(layout)

        # connect 'Copy' events to handlers
        self.copy_speeds.changed.connect(self.copy_speeds_changed)
        self.copy_volumes.changed.connect(self.copy_volumes_changed)
        self.btn_copy_start_stop.clicked.connect(self.copy_start)
        self.btn_copy_clear.clicked.connect(self.copy_clear)

    def copy_start(self, event=None):
        """The Copy 'start/pause' button was clicked."""

        if self.processing:
            # enable the Clear button and speed/grouping/charset
            self.btn_copy_clear.setDisabled(False)
            self.copy_speeds.setDisabled(False)
            self.copy_volumes.setDisabled(False)

            # Pause button label becomes Start
            self.btn_copy_start_stop.setText('Start')
            self.btn_copy_start_stop.update()
            if self.threadCopy:
                self.threadCopy.terminate()
                self.threadCopy.wait()
                self.threadCopy = None

            # change state variables to reflect the stop
            self.processing = False
        else:
            # disable the Clear button and speed/grouping/charset, relabel Start button
            self.btn_copy_clear.setDisabled(True)
            self.copy_speeds.setDisabled(True)
            self.copy_volumes.setDisabled(True)
            self.btn_copy_start_stop.setText('Pause')

            # start the 'Send' process
            self.copy_pending = []
            self.processing = True
            self.threadCopy = None
            self.copy_thread_finished()

    @pyqtSlot()
    def copy_thread_finished(self):
        """Catch signal when Copy thread finished.

        If still processing, start new thread.
        """

        # indicate that the thread isn't running
        if self.threadCopy:
            self.threadCopy.finished.disconnect()
        self.threadCopy = None

        if self.processing:
            # update copy count, maybe increase Koch charset
            self.process_count += 1
            if self.process_count >= self.KochCopyCount:
                self.process_count = 0
                if self.all_copy_chars_ok():
                    self.copy_start()   # turn off copying, self.processing := None
                    self.increase_copy_Koch()

        # we check again if processing as we can disable in code above
        if self.processing:
            # prepare, get next char, remember last two chars
            copy_char = utils.get_random_char(self.copy_Koch_charset,
                                              self.copy_stats,
                                              self.KochCopyCount,
                                              self.KochCopyThreshold)
            self.copy_pending.append(copy_char)
            self.copy_pending = self.copy_pending[-2:]

            # start new thread to sound character
            self.threadCopy = CopyThread(copy_char, self.copy_morse_obj)
            self.threadCopy.finished.connect(self.copy_thread_finished)
            self.threadCopy.start()

    def copy_clear(self, event):
        """The Copy 'clear' button was clicked."""

        self.copy_display.clear()

    def all_copy_chars_ok(self):
        """See if all Koch chars are over threshold.

        Return True if so.
        """

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

        # if we ARE using Koch for Copy
        if self.copy_Koch_number < len(utils.Koch):
            # we CAN increase the Copy Koch charset
            self.copy_Koch_number += 1
            self.copy_Koch_charset = utils.Koch[:self.copy_Koch_number]

            # let user know what is happening
            new_char = self.copy_Koch_charset[-1]
            msg = ("<font size=%d>"
                   "Adding a new character to the test set: '%s'.<br>"
                   "The morse code for this character is '%s'."
                   "</font>"
                   % (MorseTrainer.MsgBoxFontSize, new_char,
                      utils.morse2display(utils.Char2Morse[new_char])))

            msgbox = QMessageBox(self)
            msgbox.setText('Koch promotion')
            msgbox.setInformativeText(msg)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.setDefaultButton(QMessageBox.Ok)
            msgbox.exec()

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

    def copy_volumes_changed(self, tone, signal, noise):
        """Something in the "copy volume" group changed.

        signal  new signal percent
        noise   new noise percent
        """

        self.copy_freq = tone
        self.copy_signal = signal
        self.copy_noise = noise
        self.copy_morse_obj.set_volumes(tone, signal, noise)

######
# Other code
######

    def keyPressEvent(self, e):
        """When self.processing is True we handle keypresses.

        This should only be true during Copy processing.
        """

        # ignore anything we aren't interested in
        try:
            char = chr(e.key())
        except ValueError:
            # probably some sort of control key, ignore
            return

        if char not in utils.AllUserChars:
            return      # ignore chars we aren't testing on

        if self.processing:
            if self.copy_pending:
                # if we are copying, handle char
                pending = self.copy_pending.pop(0)

                # need some logic here to handle case when user gets behind
                # if key doesn't match oldest but newest, assume newest
                if char != pending:
                    if self.copy_pending and char == self.copy_pending[0]:
                        pending = self.copy_pending.pop(0)

                self.copy_display.insert_upper(pending, self.copy_display.AskTextColour)

                colour = self.copy_display.AnsTextGoodColour
                if pending != char:
                    try:
                        morse = utils.char2morse(char)
                    except KeyError:
                        morse = '<unknown>'
                    colour = self.copy_display.AnsTextBadColour
                    msg = ("Sent '%s' (%s),\ngot '%s' (%s)."
                           % (pending, utils.char2morse(pending), char, morse))
                    self.copy_display.update_tooltip(msg)
                self.copy_display.insert_lower(char, colour)
                self.copy_display.set_highlight()       # move highlight to end

                # update the character stats and display
                self.update_stats(self.copy_stats, pending, pending==char)

                data = self.stats2percent(self.copy_stats,
                                          MorseTrainer.KochCopyThreshold)
                self.copy_charset.setState(self.copy_Koch_number, data,
                                           MorseTrainer.KochCopyThreshold,
                                           MorseTrainer.KochCopyCount)
#            else:
#                # only get here is user keying ahead, ignore it
#                log.critical("HUH!?  .processing=%s, .copy_pending=%s" % (str(self.processing), str(self.copy_pending)))
#                print("Shouldn't see this!?  See log.")

    def update_stats(self, stats, char, result):
        """Update internal character statistics.

        stats   the stats dictionary to update
        char    the character being tested
        result  True or False
        """

        # update history list for char, limit list length
        stats[char].append(result)
        stats[char] = stats[char][-self.KochMaxHistory:]

    def update_UI(self):
        """Update controls that show state values."""

        # the send speeds
        self.send_speeds.setState(self.send_wpm)
        self.send_speeds.update()

        # the send test sets
        data = self.stats2percent(self.send_stats,
                                  MorseTrainer.KochSendThreshold)
        self.send_charset.setState(self.send_Koch_number, data,
                                   MorseTrainer.KochSendThreshold,
                                   MorseTrainer.KochSendCount)
        self.send_charset.update()

        # the copy speeds
        self.copy_speeds.setState(self.copy_wpm, self.copy_cwpm)
        self.copy_speeds.update()

        # the send test sets
        data = self.stats2percent(self.copy_stats,
                                  MorseTrainer.KochCopyThreshold)
        self.copy_charset.setState(self.copy_Koch_number, data,
                                   MorseTrainer.KochCopyThreshold,
                                   MorseTrainer.KochCopyCount)
        self.copy_charset.update()

    def closeEvent(self, *args, **kwargs):
        """Program close - save the internal state."""

        super().closeEvent(*args, **kwargs)
        self.save_state(MorseTrainer.StateSaveFile)
        self.send_morse_obj.save_params(MorseTrainer.MorseParamsFile)
        if self.threadSend:
            self.threadSend.terminate()
            self.threadSend.wait(msecs=10000)
        if self.threadCopy:
            self.threadCopy.terminate()
            self.threadCopy.wait(msecs=10000)

    def clear_data(self):
        """Define and clear all internal variables."""

        # the morse objects
        self.send_morse_obj = ReadMorse()
        self.send_morse_obj.load_params(MorseTrainer.MorseParamsFile)
        self.copy_morse_obj = SoundMorse()

        # Send variables
        self.send_Koch_number = 2
        self.send_Koch_charset = utils.Koch[:self.send_Koch_number]
        self.send_wpm = 5
        # self.send_cwpm not used for Send
        self.send_expected = None
        self.threadSend = None  # the listening thread

        # Copy variables
        self.copy_Koch_number = 2
        self.copy_Koch_charset = utils.Koch[:self.copy_Koch_number]
        self.copy_wpm = 5
        self.copy_cwpm = 5
        self.copy_freq = SoundMorse.DefaultFrequency
        self.copy_pending = ''  # holds last 2 chars sounded
        self.threadCopy = None  # the sounding thread

        self.copy_signal = MorseTrainer.DefaultSignalPercent
        self.copy_noise = MorseTrainer.DefaultNoisePercent

        # the send/copy statistics
        # each 'char':value is a list of last N results, True or False
        self.send_stats = {ch:[] for ch in utils.AllUserChars}
        self.copy_stats = {ch:[] for ch in utils.AllUserChars}

        # state variable shows send or copy test in progress
        self.processing = False
        self.process_count = 0
        self.resultq = Queue()

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
        # ensure speeds are a multiple of 5
        #####

        self.send_wpm = utils.make_multiple(self.send_wpm, MorseTrainer.StepSpeed)
        self.copy_wpm = utils.make_multiple(self.copy_wpm, MorseTrainer.StepSpeed)
        self.copy_cwpm = utils.make_multiple(self.copy_cwpm, MorseTrainer.StepSpeed)

        #####
        # now update UI state from state variables
        #####

        # Send panel
        self.send_speeds.setState(self.send_wpm)
        data = self.stats2percent(self.send_stats,
                                  MorseTrainer.KochSendThreshold)
        self.send_charset.setState(self.send_Koch_number, data,
                                   MorseTrainer.KochSendThreshold,
                                   MorseTrainer.KochSendCount)

        # Copy panel
        self.copy_speeds.setState(self.copy_wpm, cwpm=self.copy_cwpm)
        data = self.stats2percent(self.copy_stats,
                                  MorseTrainer.KochCopyThreshold)
        self.copy_charset.setState(self.copy_Koch_number, data,
                                   MorseTrainer.KochCopyThreshold,
                                   MorseTrainer.KochCopyCount)
        self.copy_morse_obj.set_speeds(self.copy_cwpm, self.copy_wpm)
        self.copy_morse_obj.set_volumes(self.copy_freq,
                                        self.copy_signal, self.copy_noise)
        self.copy_volumes.setState(self.copy_freq,
                                   self.copy_signal, self.copy_noise)

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
            {'A': (fraction, sample_size), ...}

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

            results[char] = (fraction, sample_size)

        return results

    def tab_change(self, tab_index):
        """Handler when a tab is changed.

        tab_index  index of the new tab
        """

        self.current_tab_index = tab_index
        old_tab = MorseTrainer.TabEnum2Name.get(self.previous_tab_index, str(None))

        # if we left the "send" tab, turn off action, if any
        if self.previous_tab_index == MorseTrainer.SendTab:
            self.processing = True
            self.send_start()       # to set UI state to "not processing"

        # if we left the "copy" tab, turn off action, if any
        if self.previous_tab_index == MorseTrainer.CopyTab:
            self.processing = True
            self.copy_start()       # to set UI state to "not processing"

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

    It automatically sends a signal to the main thread when finished.
    The tuple of recognized char and morse is put onto the supplied queue.
    """

    send_done = pyqtSignal(tuple)

    def __init__(self, sound_object):
        """Create a thread to read one morse character.

        sound_object  the object that reads morse sounds
        resultq       queue on which to place recognized character
        """

        super().__init__()
        self.sound_object = sound_object

    def run(self):
        """Sound the character."""

        # read one character and retrurn in signal
        result = self.sound_object.read()
        self.send_done.emit(result)

######
# A thread to sound one morse character.
######

class CopyThread(QThread):
    """A thread to sound a morse character to the speakers.

    It automatically sends a signal to the main thread when finished.
    """

    def __init__(self, char, sound_object):
        """Create a thread to sound one morse character.

        char          the character to sound
        sound_object  the object that makes morse sounds
        """

        super().__init__()
        self.char = char
        self.sound_object = sound_object

    def run(self):
        """Sound the character."""

        # make the character sound in morse
        self.sound_object.send(self.char)


######
# Various functions used to run the app.
######

def trace_calls(frame, event, arg):
    """Set up c_call tracing - https://pymotw.com/3/sys/tracing.html"""

    if event != 'c_call':
        return
    co = frame.f_code
    func_name = co.co_name
    func_line_no = frame.f_lineno
    func_filename = co.co_filename
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    log('** arg=%s' % str(arg))
    log('* Call to', func_name)
    log('*  on line {} of {}'.format(func_line_no, func_filename))
    log('*  from line {} of {}'.format(caller_line_no, caller_filename))
    return

def usage(msg=None):
    """Print the module __doc__ string, plus optional message."""

    if msg:
        print(('*'*80 + '\n%s\n' + '*'*80) % msg)
    print(__doc__)

def excepthook(type, value, tb):
    """Handler for uncaught exceptions."""

    msg = '\n' + '=' * 80
    msg += '\nUncaught exception:\n'
    msg += ''.join(traceback.format_exception(type, value, tb))
    msg += '=' * 80 + '\n'
    log.critical(msg)
    print(msg)

###############################################################################
# Actual start of the app is here.
###############################################################################

# plug our handler into the python system
sys.excepthook = excepthook

# start the logging
log = logger.Log('debug.log', logger.Log.CRITICAL)

# announce the start
morse_version = utils.str2morse('morse trainer %s' % ProgramVersion)
morse_width = len(morse_version)
morse_signon = 'Morse Trainer %s - AC3DN' % ProgramVersion
log(morse_version)
log(morse_signon.center(morse_width))
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

sys.settrace(trace_calls)

# launch the app, catch thread crashes with 'faulthandler'
with open(FaultHandlerFile, 'w') as fd:
    faulthandler.enable(file=fd)   # turn on fault trap
    app = QApplication(sys.argv)
    ex = MorseTrainer()
    ex.show()
    sys.exit(app.exec())
