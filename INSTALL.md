# ---  INSTALL for PATCHANCE  ---

Before installing, please uninstall any existing Patchance installation: <br/>
`$ [sudo] make uninstall`

To install Patchance, simply run as usual: <br/>
`$ make` <br/>
`$ [sudo] make install`

Depending on the distribution (Fedora and others) you'll need to use the LRELEASE variable to build.
If you don't have 'lrelease' executable but 'lrelease-qt5' use:
`$ make LRELEASE=lrelease-qt5` <br/>
`$ [sudo] make install`

You can run Patchance without installing, by using instead: <br/>
`$ make` <br/>
`$ ./src/patchance.py`

Packagers can make use of the 'PREFIX' and 'DESTDIR' variable during install, like this: <br/>
`$ make install PREFIX=/usr DESTDIR=./test-dir`

To uninstall Patchance, run: <br/>
`$ [sudo] make uninstall`
<br/>

===== BUILD DEPENDENCIES =====
--------------------------------
The required build dependencies are: <i>(devel packages of these)</i>

 - PyQt5
 - Qt5 dev tools 
 - qtchooser

On Debian and Ubuntu, use these commands to install all build dependencies: <br/>
`$ sudo apt-get install python3-pyqt5 pyqt5-dev-tools qtchooser qttools5-dev-tools`

On Fedora: <br/>
` $ sudo dnf install python3-qt5-devel qt-devel qtchooser`

===== RUNTIME DEPENDENCIES =====
---------------------------------
If you want to provide ALSA MIDI ports, you must have the python3-pyalsa lib with version >= 1.2.4.

On Debian and Ubuntu, use these commands to install this optional dependency: <br/>
`$ sudo apt-get install python3-pyalsa`
But note that it may be not enough if the version provided by your system is too old.

On Fedora: <br/>
` $ sudo dnf install python3-alsa`
