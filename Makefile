#
# To manage the Morse Trainer project a little
#

run:
	python morse_trainer.py
	#python -Qwarnall morse_trainer.py

clean:
	rm -Rf __pycache__ *.log
	(cd morse_trainer; rm -Rf __pycache__ *.log)
