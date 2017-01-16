#
# To manage the Morse Trainer project a little
#

run:
	rm -f *.log
	python3 morse_trainer.py

exe:
	bash build_executable

clean:
	rm -Rf __pycache__
	rm -f *.log

