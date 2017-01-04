Morse Trainer
=============

This is an attempt at a "morse trainer" program.  It will allow the user to
practice sending and copying morse.  Besides this program you will need some
method of making audio morse sounds, such as a morse key and code practice
oscillator.

This program actually listens to and decodes the morse you send.  If the program
can recognize your morse it's probably reasonably well-formed!

Current Status
--------------

The UI is mostly complete, barring any unforeseen things.  Next step is to
start putting code under the UI, probably starting with "copy".

Requirements
------------

* Teach sending and copying morse
    * SEND listens to morse sounds and displays the decoded morse
    * COPY sounds morse and listener types in the received characters
* Uses both Koch and selectable charset approaches
* User can vary char and word speeds independently (Farnsworth method)
* Program keeps learning statistics for feedback

Nice to have:

* Have a "practice communication" mode, computer is other end?
* Multiple users, each with own history/statistics (so, login)
* Get text from the 'net as copy practice (news?)

Implementation
--------------

* python3
* PyQt5
* numpy
* use sqlite for statistics/history memory?

Design
------

**SEND**

The program will show user groups to send, highlighting the current expected
group.  As the user sends morse, the decoded characters appear underneath, with
incorrect characters highlighted.

Operations allowed:

* START
* STOP
* PAUSE
* CLEAR (?)

Parameters that can be changed:

* Characters used

Statistics kept:

* % correct, in current test and globally
* relative error rates by character

**COPY**

The program will sound morse and accept user keying in the character.  The
display will show the received character and also the sent character, with
highlighting if incorrect.

Operations allowed:

* START
* STOP
* PAUSE
* CLEAR

Parameters that can be changed:

* Characters used (just A-Z, NUMERALS, etc)
* char speed
* word speed

The characters used could also follow the Koch method, starting with two
characters at the desired char speed (usually K and M).  When the error
rate falls below a preset level, add one more character.  Continue until
all selected characters are OK.

Statistics kept:

* % correct, in current test and globally
* relative error rates by character

**STATUS**

This pane will show the 'percentage correct' values for all characters.
The percentages for Send and Receive will be kept separate.

The *show_status.py* file contains the code for one status display.

Character Selection
-------------------

Selection of characters will be from groups:

* common (selection of alphabetics, numerals and some punctuation)
* alphabetic
* numerals
* punctuation
* callsigns
* prosigns

The selection of characters will allow one or more  groups, with the user being
allowed to choose a sub-set of a group.

The *grid_select.py* file contains the code for this.

Sending Selection
-----------------

The user can choose what to send and how they are sent:

* characters - group (4/5), Q codes, etc
* English text (from built-in or external text)
* prosigns
* callsigns
* actual contacts (may be send then receive then send, ...)
