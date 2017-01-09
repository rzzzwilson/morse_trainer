from distutils.core import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='morse_trainer',
      packages=['morse_trainer'],
      version='0.2',
      description='A program to teach sending and copying Morse code',
      long_description=readme(),
      url='http://github.com/rzzzwilson/morse_trainer',
      author='Ross Wilson',
      author_email='rzzzwilson@gmail.com',
      license='MIT',
      install_requires=['python3', 'PyQt5', 'numpy', 'pyaudio'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3',
                   'Topic :: Communications :: Ham Radio',
                   'Topic :: Education :: Computer Aided Instruction (CAI)'],
      keywords='python pyqt5 morse',
      download_url='https://github.com/rzzzwilson/morse_trainer/releases/tag/0.2',
      include_package_data=True,
      zip_safe=False)
