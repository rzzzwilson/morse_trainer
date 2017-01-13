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

The UI is mostly complete, barring any unforeseen things.  The 'Send', 'Copy'
and 'Stats' tabs are all working, with some minor UI bugs, such as buttons
not beibg disabled when thay should be, etc.

Next we need to get the Koch mechanism working, that is, increasing the size
of the Koch test charset depending on error rates.  Also consider reducing the
test charset if error rates increase.

Also need to tweak the stats memory mechanism.  At the moment, we remember all
attempts to send/copy code.  The stats mechanism should only remember the last 
N instances of each character.

The code to listen to and decode morse soubds also needs to be made more robust.

Requirements
------------

* Teach sending and copying morse
    * SEND listens to morse sounds and displays the decoded morse
    * COPY sounds morse and listener types in the received characters
* Uses both Koch and selectable charset approaches
* User can vary char and word speeds independently (Farnsworth method)
* Program keeps learning statistics for feedback

Nice to have:

* Multiple users, each with own history/statistics (so, login)
* Get text from the 'net as copy practice (news?)
* Some added noise/fading for realism
* Try to have a "QSO mode" for even more realism

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

* START/PAUSE   (button changes label)
* CLEAR

Parameters that can be changed:

* Characters used
* Optional minimum speed

Statistics kept:

* relative error rates by character

**COPY**

The program will sound morse and accept user keying in the character.  The
display will show the received character and also the sent character, with
highlighting if incorrect.

Operations allowed:

* START/PAUSE   (button changes label)
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

* relative error rates by character

**STATUS**

This pane will show the 'percentage correct' values for all characters.
The percentages for Send and Receive will be kept separate.

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

Sending Selection
-----------------

The user can choose what to send and how they are sent:

* characters - group (4/5), Q codes, etc
* English text (from built-in or external text)
* prosigns
* callsigns
* actual contacts (may be send then receive then send, ...)
