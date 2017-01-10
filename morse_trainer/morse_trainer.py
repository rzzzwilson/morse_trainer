#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Morse Trainer is an application to help a user learn to send and copy Morse.

Usage:  morse_trainer [-d <debug>]  [-h]

where  -d <debug>  sets the debug level to the number <debug> [0,50]
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

import copy_morse
from display import Display
from copy_speeds import Speeds
from groups import Groups
from charset import Charset
from charset_proficiency import CharsetProficiency
from instructions import Instructions
from sound_morse import SoundMorse
import utils
import logger


# get program name and version
ProgName = sys.argv[0]
if ProgName.endswith('.py'):
        ProgName = ProgName[:-3]

ProgramMajor = 0
ProgramMinor = 2
ProgramVersion = '%d.%d' % (ProgramMajor, ProgramMinor)


class MorseTrainer(QTabWidget):

    # set platform-dependent sizes
    if platform.system() == 'Windows':
        MinimumWidth = 815
        MinimumHeight = 675
    elif platform.system() == 'Linux':
        MinimumWidth = 850
        MinimumHeight = 685
    elif platform.system() == 'Darwin':
        MinimumWidth = 815
        MinimumHeight = 675
    else:
        raise Exception('Unrecognized platform: %s' % platform.system())

    # set default speeds
    DefaultWordsPerMinute = 15
    DefaultCharWordsPerMinute = 10

    # 'enum' constants for the three tabs
    (SendTab, CopyTab, StatsTab) = range(3)

    # dict to convert tab index to name
    TabEnum2Name = {SendTab: 'Send',
                    CopyTab: 'Copy',
                    StatsTab: 'Statistics'}

    # name for the state save file
    StateSaveFile = '%s.state' % ProgName

    # define names of the instance variables to be saved/restored
    StateVarNames = ['send_stats', 'copy_stats', 'copy_using_Koch',
                     'copy_Koch_number', 'copy_Koch_list',
                     'copy_User_chars_dict', 'copy_wpm', 'copy_cwpm',
                     'copy_group_index', 'send_wpm', 'send_Koch_list',
                     'current_tab_index']


    def __init__(self, parent = None):
        """Create a MorseTrainer object."""

        super().__init__(parent)

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

        self.initSendTab()
        self.initCopyTab()
        self.InitStatsTab()

        self.setMinimumSize(MorseTrainer.MinimumWidth, MorseTrainer.MinimumHeight)
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
        controls.addItem(QSpacerItem(20, 20))   # empty, for now

        hbox = QHBoxLayout()
        hbox.addLayout(controls)
        hbox.addStretch()
        #hbox.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
        layout.addWidget(self.send_display)
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        self.send_tab.setLayout(layout)

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
        self.copy_speeds = Speeds()
        self.copy_groups = Groups()
        self.copy_charset = Charset(utils.AllUserChars)
        self.btn_copy_start_stop = QPushButton('Start')
        self.btn_copy_clear = QPushButton('Clear')

        # start layout
        buttons = QVBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.btn_copy_start_stop)
        buttons.addItem(QSpacerItem(20, 20))
        buttons.addWidget(self.btn_copy_clear)

        controls = QVBoxLayout()
        controls.addWidget(self.copy_speeds)
        controls.addWidget(self.copy_groups)
        controls.addWidget(self.copy_charset)

        hbox = QHBoxLayout()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
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

    def copy_thread_finished(self):
        """Catch signal when Send thread finished.

        If still processing, start new thread.
        """

        if self.processing:
            send_char = utils.get_random_char(self.copy_Koch_list)
            self.copy_pending = (self.copy_pending + [send_char])[-2:]
            self.threadCopy = CopyThread(send_char, self.copy_morse_obj)
            self.threadCopy.finished.connect(self.copy_thread_finished)
            self.threadCopy.start()

    def copy_clear(self, event):
        """The Copy 'clear' button was clicked."""

        self.copy_display.clear()

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
        self.copy_Koch_list = utils.Koch[:self.copy_Koch_number]

        # update the user test set
        on = [ch for ch in self.copy_User_chars_dict if self.copy_User_chars_dict[ch]]
        self.copy_User_sequence = ''.join(on)

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
                    'Pressing the "Clear" button will clear the statistics. '
                    'This is useful when changing test speeds.')
        instructions = Instructions(doc_text)
        self.send_status = CharsetProficiency('Send Proficiency',
                                              utils.Alphabetics,
                                              utils.Numbers,
                                              utils.Punctuation)
        percents = self.stats2percent(self.send_stats)
        self.send_status.setState(percents)
        self.copy_status = CharsetProficiency('Copy Proficiency',
                                              utils.Alphabetics,
                                              utils.Numbers,
                                              utils.Punctuation)
        percents = self.stats2percent(self.copy_stats)
        self.copy_status.setState(percents)
        btn_clear = QPushButton('Clear')

        # lay out the tab
        buttons = QVBoxLayout()
        buttons.addStretch()
        buttons.addWidget(btn_clear)

        controls = QVBoxLayout()
        controls.addWidget(self.send_status)
        controls.addWidget(self.copy_status)

        hbox = QHBoxLayout()
        hbox.addLayout(controls)
        buttons.addItem(QSpacerItem(10, 1))
        hbox.addLayout(buttons)

        layout = QVBoxLayout()
        layout.addWidget(instructions)
        layout.addStretch()
        layout.addLayout(hbox)
        self.stats_tab.setLayout(layout)

        # connect 'Stats' events to handlers
        btn_clear.clicked.connect(self.clear_stats)

    def clear_stats(self):
        """Clear the statistics display."""

        # should have a "Are you sure?" dialog here

        # clear the internal data structure
        for ch in utils.AllUserChars:
            self.copy_stats[ch] = (0, 0)

        new = self.stats2percent(self.copy_stats)
        self.copy_status.setState(new)

######
# Other code
######

    def keyPressEvent(self, e):
        """When self.processing is True we handle keypresses."""

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
                (num_chars, num_ok) = self.copy_stats[pending]
                num_chars += 1
                if pending == char:
                    num_ok += 1
                self.copy_stats[pending] = (num_chars, num_ok)
#            elif self.send_pending:
#                # if we are sending, handle here
#                pass

    def update_UI(self):
        """Update controls that show state values."""

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

        # the morse sound object and Send state variables
        self.copy_morse_obj = SoundMorse()  # the Copy morse thread object
        self.keypress_count = 0             # keypress counter
        self.copy_pending = ''              # holds last 2 chars sounded

        # state variable shows send or copy processing
        self.processing = False

        # clear the send/copy statistics
        # each dictionary contains tuples of (<num_chars>, <num_ok>)
        self.send_stats = {}
        self.copy_stats = {}
        for char in utils.AllUserChars:
            self.send_stats[char] = (0, 0)
            self.copy_stats[char] = (0, 0)

        # the character sets we test on and associated variables
        self.copy_using_Koch = True
        self.copy_Koch_number = 2
        self.copy_Koch_list = utils.Koch[:self.copy_Koch_number]
        self.copy_User_chars_dict = {ch:False for ch in utils.AllUserChars}

        self.send_Koch_number = 2
        self.send_Koch_list = [ch for ch in utils.Koch[:self.send_Koch_number]]

        # send and copy speeds
        self.send_wpm = None        # not used yet
        self.copy_wpm = 5
        self.copy_cwpm = 5

        # the copy grouping
        self.copy_group_index = 0

        # set the current and previous tab indices
        self.current_tab_index = MorseTrainer.SendTab
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

        # the speed
        self.copy_speeds.setState(self.copy_wpm, cwpm=self.copy_cwpm)
        # the grouping
        self.copy_groups.setState(self.copy_group_index)
        # the charset used
        self.copy_charset.setState(self.copy_using_Koch,
                                   self.copy_Koch_number,
                                   self.copy_User_chars_dict)
        # update the Send morse sounder object
        self.copy_morse_obj.set_speeds(self.copy_cwpm, self.copy_wpm)

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

    def stats2percent(self, stats):
        """Convert stats data into a fraction dictionary.

        The 'stats' data has the form {'A':(100,50), ...} where
        the tuple contains (<num tested>, <num OK>).

        The resultant fraction dictionary has the form:
            {'A': 0.50, ...}
        """

        results = {}
        for (char, (num_tested, num_ok)) in stats.items():
            if num_tested == 0:
                fraction = 0.0
            else:
                fraction = num_ok / num_tested
            results[char] = fraction

        return results

    def update_stats(self, stats_dict, char, ok):
        """Update the stats for a single character.

        stats_dict  a reference to the stats dictionary to update
        char        the character that was tested
        ok          True if test was good, else False
        """

        (num_tests, num_ok) = stats_dict[char]
        num_tests += 1
        if ok:
            num_ok += 1
        stats_dict[char] = (num_tests, num_ok)

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
            percents = self.stats2percent(self.send_stats)
            self.send_status.setState(percents)

            percents = self.stats2percent(self.copy_stats)
            self.copy_status.setState(percents)

        # remember the previous tab for NEXT TIME WE CHANGE
        self.previous_tab_index = tab_index

    def set_app_tab(self, tab_index):
        """Make app show the required tab index sheet."""

        self.setCurrentIndex(tab_index)


######
# A class to sound one more character.
# We need a thread for this as we are doing things while the Copy cound is made.
######

class CopyThread(QThread):
    """A thread to sound a morse character to the speakers.

    It sends a signal to the main thread when finished.
    """

    # the signal when finished
    finished = pyqtSignal()

    def __init__(self, char, sound_object):
        """Create a thread to sound one morse character.

        char         the character to sound
        sound_object  the object that makes morse sounds
        """

        QThread.__init__(self)
        self.char = char
        self.sound_object = sound_object

    def __del__(self):
        """Delete the thread."""

        self.wait()

    def run(self):
        """Sound the character."""

        # make the character sound in morse
        self.sound_object.send(self.char)

        # send signal to main thread: finished
        self.finished.emit()


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
    log('* -- --- .-. ... .  - .-. .- .. -. . .-. *')
    log('*                                        *')
    log('*      Morse Trainer %3s by VK4FAWR      *' % ProgramVersion)
    log('*                                        *')
    log('* -- --- .-. ... .  - .-. .- .. -. . .-. *')

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
