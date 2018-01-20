REM Use pyinstaller to create a Windows morse_trainer executable.
REM -------------------------------------------------------------

REM rmdir /S/Q dist build
pyinstaller -F -p "C:\Users\r-w\AppData\Local\Programs\Python\Python35\Lib\site-packages\PyQt5" morse_trainer.py
cd dist
move /Y morse_trainer.exe ../morse_trainer.win.exe
cd ..
REM rmdir /S/Q dist build __pycache__
del *.spec