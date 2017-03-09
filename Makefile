#
# To manage the Morse Trainer project a little
#

run:
#	rm -f *.log
	python3 morse_trainer.py

exe:
	bash build_executable

backup:
	cp read_morse.param read_morse.param.OLD
	cp morse_trainer.state morse_trainer.state.OLD

clean:
	rm -Rf __pycache__
	rm -f *.log

