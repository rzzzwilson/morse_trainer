REM Use pyinstaller to create a Windows morse_trainer executable.
REM -------------------------------------------------------------

rmdir /S/Q dist build
pyinstaller -F --noconsole morse_trainer.py
cd dist
move morse_trainer.exe ../morse_trainer.win.exe
cd ..
rmdir /S/Q dist build __pycache__
del *.spec